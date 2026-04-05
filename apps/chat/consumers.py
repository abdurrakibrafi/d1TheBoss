from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
import traceback
import decimal
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from apps.chat.services.ai_chat_core import AIChatCore
from apps.chat.services.context_builder import ConversationManager
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.chat.models import ChatMessage, ChatSession

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = AIChatCore()
        self.conversation = None
        self.user = None
        self.room_group_name = None

    def convert_decimals(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self.convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_decimals(v) for v in obj]
        return obj

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get("user")

        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return

        # Get session_id from URL
        self.session_id = self.scope["url_route"]["kwargs"].get("session_id")

        # Validate session exists for this user
        if self.session_id:
            try:
                self.conversation = await database_sync_to_async(ConversationManager)(
                    user=self.user, session_id=self.session_id
                )
                # Refresh the session's context snapshot from latest onboarding
                # data so updates (e.g. tone changes) are reflected immediately.
                await database_sync_to_async(
                    lambda: self.conversation.update_session_context(
                        self.conversation._get_user_spiritual_context()
                    )
                )()
            except Exception as e:
                await self.close(code=4004)
                return

        # Join user-specific group
        self.room_group_name = f"bible_chat_{self.user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send connection confirmation
        await self.send(json.dumps({
            "type": "connection",
            "message": "Connected to Bible Chat!",
            "user_id": self.user.id,
            "session_id": self.session_id,
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.conversation:
            await database_sync_to_async(self.conversation.end_session)()

        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "message")

            if message_type == "message":
                await self.handle_bible_chat_message(data)
            elif message_type == "new_session":
                await self.handle_new_session()
            elif message_type == "get_sessions":
                await self.handle_get_sessions()
            elif message_type == "bookmark_message":
                await self.handle_bookmark_message(data)
            else:
                await self.send_error("Unknown message type")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Unexpected error: {str(e)}")


    async def handle_bible_chat_message(self, data):
        """Process Bible chat with Preachly structure"""
        try:
            message = data.get("message", "").strip()
            message_type = data.get("message_type", "objection")
            tone = data.get("tone", "Clear and Hopeful")
            depth = data.get("depth", "In-Depth Explanation")
 
            if not message:
                await self.send_error("Message cannot be empty")
                return
 
            # Initialize conversation if needed
            if not self.conversation:
                self.conversation = await database_sync_to_async(ConversationManager)(
                    user=self.user
                )
 
            # Add user message to DB
            await database_sync_to_async(self.conversation.add_message)(
                content=message, is_user=True
            )
 
            user_context = await database_sync_to_async(
                self.conversation.get_user_spiritual_context
            )()
 
            saved_tone = (
                user_context.get("tone_preference", {}).get("name")
                if user_context
                else None
            )
            if saved_tone:
                tone = saved_tone

            # ADD THIS — pull depth from bible_familiarity
            saved_familiarity = (
                user_context.get("bible_familiarity", {}).get("title")
                if user_context else None
            )
            familiarity_to_depth = {
                "Conversation Ready": "Conversation Ready",
                "In-Depth": "In-Depth Explanation",
                "Full Framework": "Full Framework",
            }
            if saved_familiarity and saved_familiarity in familiarity_to_depth:
                depth = familiarity_to_depth[saved_familiarity]
            
            # Handle yes_no BEFORE sending typing indicator
            # Clarification handlers control their own typing indicator
            if message_type == "yes_no":
                if message.lower() in ["yes", "yes, explain more"]:
                    await self.handle_clarification_request(data)
                    return
                elif message.lower() in ["no", "no, thanks"]:
                    await self.handle_no_clarification(data)
                    return
 
            # Only send typing for normal messages (not yes/no)
            await self.send(json.dumps({"type": "typing", "is_typing": True}))
 
            # Generate Preachly response
            ai_response_data = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_preachly_response, message, tone, depth, user_context
            )
 
            await self.send(json.dumps({"type": "typing", "is_typing": False}))
 
            if ai_response_data["success"]:
                ai_message = await database_sync_to_async(
                    self.conversation.add_message
                )(
                    content=ai_response_data["content"],
                    is_user=False,
                    ai_metadata=ai_response_data,
                )
 
                response_data = {
                    "type": "preachly_response",
                    "content": ai_response_data["content"],
                    "session_id": str(self.conversation.session.id),
                    "message_id": ai_message.id,
                    "tone": ai_response_data["tone"],
                    "depth": ai_response_data["depth"],
                    "tokens_used": ai_response_data.get("tokens_used", 0),
                    "show_clarification": True,
                    "timestamp": ai_message.created_at.isoformat(),
                }
 
                await self.send(json.dumps(response_data))
            else:
                await self.send_error(ai_response_data.get("error", "Unknown error"))
 
        except Exception as e:
            await self.send_error(f"Error: {str(e)}")

    async def handle_clarification_request(self, data):
        """Handle 'Yes' — provide deeper clarification (NO restating)"""
        try:
            last_message = await database_sync_to_async(
                lambda: self.conversation.session.messages.filter(is_user=False).last()
            )()
 
            if not last_message:
                await self.send_error("No previous response to clarify")
                return
 
            user_context = await database_sync_to_async(
                self.conversation.get_user_spiritual_context
            )()
            tone = (
                user_context.get("tone_preference", {}).get("name", "Clear and Hopeful")
                if user_context else "Clear and Hopeful"
            )
 
            await self.send(json.dumps({"type": "typing", "is_typing": True}))
 
            clarification_data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ai.generate_clarification_yes(last_message.content, tone)
            )
 
            await self.send(json.dumps({"type": "typing", "is_typing": False}))
 
            if clarification_data["success"]:
                clarification_message = await database_sync_to_async(
                    self.conversation.add_message
                )(
                    content=clarification_data["content"],
                    is_user=False,
                    ai_metadata=clarification_data,
                )
 
                await self.send(json.dumps({
                    "type": "clarification_response",
                    "content": clarification_data["content"],
                    "session_id": str(self.conversation.session.id),
                    "message_id": clarification_message.id,
                    "show_clarification": True,
                    "timestamp": clarification_message.created_at.isoformat(),
                }))
 
        except Exception as e:
            await self.send_error(f"Clarification error: {str(e)}")


    async def handle_no_clarification(self, data):
        """
        Handle 'No' — AI suggests follow-up conversation question.
        Frontend MUST append '— or —\\nStart a new chat' as static UI text.
        """
        try:
            last_message = await database_sync_to_async(
                lambda: self.conversation.session.messages.filter(is_user=False).last()
            )()
 
            if not last_message:
                await self.send_error("No previous response found")
                return
 
            user_context = await database_sync_to_async(
                self.conversation.get_user_spiritual_context
            )()
            tone = (
                user_context.get("tone_preference", {}).get("name", "Clear and Hopeful")
                if user_context else "Clear and Hopeful"
            )
 
            await self.send(json.dumps({"type": "typing", "is_typing": True}))
 
            continuation_data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ai.generate_clarification_no(last_message.content, tone)
            )
 
            await self.send(json.dumps({"type": "typing", "is_typing": False}))
 
            if continuation_data["success"]:
                continuation_message = await database_sync_to_async(
                    self.conversation.add_message
                )(
                    content=continuation_data["content"],
                    is_user=False,
                    ai_metadata=continuation_data,
                )
 
                await self.send(json.dumps({
                    "type": "conversation_continuation",
                    "content": continuation_data["content"],
                    "session_id": str(self.conversation.session.id),
                    "message_id": continuation_message.id,
                    # Frontend renders below this:
                    # "— or —\nStart a new chat"
                    "show_new_chat_option": True,
                    "timestamp": continuation_message.created_at.isoformat(),
                }))
 
        except Exception as e:
            await self.send_error(f"Continuation error: {str(e)}")
    
    def _generate_preachly_response(self, objection, tone, depth, user_context):
        """Helper for Preachly response generation"""
        return self.ai.generate_preachly_response(objection, tone, depth, user_context)

    def _generate_clarification(self, original_response, tone):
        """Generate focused clarification"""
        try:
            clarification_prompt = f"""Provide a focused clarification of this response using {tone} tone:

    {original_response}

    Guidelines:
    - Briefly reaffirm the key point
    - Add 1-2 new insights or examples
    - Include 1-2 additional scripture references if relevant
    - Maintain {tone} tone throughout
    - Limit to 2-3 concise paragraphs
    - End with inspiring conclusion"""

            response = self.ai.client.chat.completions.create(
                model=self.ai.model,
                messages=[{"role": "user", "content": clarification_prompt}],
                temperature=self.ai._get_tone_temperature(tone),
                max_completion_tokens=3000,
            )

            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "success": True,
            }
        except Exception as e:
            return {
                "content": "I apologize, but I'm having trouble providing clarification right now.",
                "success": False,
                "error": str(e)
            }

    async def handle_new_session(self):
        """Create new Bible chat session"""
        try:
            self.conversation = await database_sync_to_async(ConversationManager)(
                user=self.user
            )

            session_summary = await database_sync_to_async(
                self.conversation.get_session_summary
            )()

            session_summary = self.convert_decimals(session_summary)

            await self.send(json.dumps({
                "type": "new_session", 
                "session": session_summary
            }))

        except Exception as e:
            await self.send_error(f"Failed to create new session: {str(e)}")

    async def handle_get_sessions(self):
        """Get user's Bible chat sessions"""
        try:
            sessions = await database_sync_to_async(self.get_user_sessions)()
            sessions = self.convert_decimals(sessions)

            await self.send(json.dumps({
                "type": "sessions_list", 
                "sessions": sessions
            }))
        except Exception as e:
            await self.send_error(f"Failed to get sessions: {str(e)}")

    async def handle_bookmark_message(self, data):
        """Handle message bookmarking"""
        try:
            message_id = data.get("message_id")
            bookmark_status = data.get("bookmark", True)

            if not message_id:
                await self.send_error("Message ID required")
                return

            success = await database_sync_to_async(self.toggle_bookmark)(
                message_id, bookmark_status
            )

            if success:
                await self.send(json.dumps({
                    "type": "bookmark_updated",
                    "message_id": message_id,
                    "bookmarked": bookmark_status
                }))
            else:
                await self.send_error("Failed to update bookmark")

        except Exception as e:
            await self.send_error(f"Bookmark error: {str(e)}")

    def get_user_sessions(self):
        """Get user's recent Bible chat sessions"""
        sessions = ChatSession.objects.filter(
            user=self.user, 
            is_active=True
        ).order_by("-updated_at")[:10]

        return [{
            "id": str(session.id),
            "title": session.title,
            "message_count": session.message_count,
            "tokens_used": session.tokens_used,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        } for session in sessions]

    def toggle_bookmark(self, message_id, bookmark_status):
        """Toggle message bookmark status"""
        try:
            message = ChatMessage.objects.get(
                id=message_id, 
                session__user=self.user
            )
            message.bookmark = bookmark_status
            message.save()
            return True
        except ChatMessage.DoesNotExist:
            return False

    async def send_error(self, message: str):
        """Send error message to client"""
        await self.send(json.dumps({
            "type": "error",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }))

    def _generate_bible_response(self, conversation_history, user_context):
        """Helper to call AI service with Bible context"""
        return self.ai.generate_bible_response(
            conversation_history=conversation_history,
            user=self.user,
            user_context=user_context
        )

    # Handle group messages (for future features like notifications)
    async def chat_message(self, event):
        """Handle messages sent to the group"""
        await self.send(json.dumps({
            "type": "notification", 
            "message": event["message"]
        }))