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
# from apps.aipersona.models import AIPersona
# from apps.chat.models import ChatMessage, ChatSession

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.ai = AIChatCore()
    #     self.conversation = None
    #     self.user = None
    #     self.room_group_name = None
    #     self.persona = None

    # def debug_json_serialization(self, data, context=""):
    #     """Debug helper to find what's causing JSON serialization issues"""
    #     try:
    #         json.dumps(data)
    #         print(f"{context}: JSON serialization OK")
    #         return data
    #     except TypeError as e:
    #         print(f"{context}: JSON Error - {str(e)}")
    #         print(f"Data type: {type(data)}")
    #         if isinstance(data, dict):
    #             for key, value in data.items():
    #                 try:
    #                     json.dumps(value)
    #                 except TypeError:
    #                     print(f"  Problem key: '{key}' = {value} (type: {type(value)})")
    #         return data

    # def convert_decimals(self, obj):
    #     """Convert Decimal objects to float for JSON serialization"""
    #     if isinstance(obj, decimal.Decimal):
    #         return float(obj)
    #     elif isinstance(obj, dict):
    #         return {k: self.convert_decimals(v) for k, v in obj.items()}
    #     elif isinstance(obj, list):
    #         return [self.convert_decimals(v) for v in obj]
    #     return obj

    # async def connect(self):
    #     self.user = self.scope.get("user")

    #     if isinstance(self.user, AnonymousUser):
    #         await self.close(code=4001)
    #         return

    #     # Read session_id from WebSocket URL (e.g. ws/chat/<session_id>/)
    #     self.session_id = self.scope["url_route"]["kwargs"].get("session_id")

    #     # Optional: Validate the session exists for this user
    #     if self.session_id:
    #         try:
    #             self.conversation = await database_sync_to_async(ConversationManager)(
    #                 user=self.user, session_id=self.session_id
    #             )
    #         except Exception as e:
    #             await self.close(code=4004)
    #             return

    #     # Join user-specific group
    #     self.room_group_name = f"chat_{self.user.id}"

    #     await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    #     await self.accept()

    #     await self.send(
    #         json.dumps(
    #             {
    #                 "type": "connection",
    #                 "message": "Connected successfully!",
    #                 "user_id": self.user.id,
    #                 "session_id": self.session_id,
    #             }
    #         )
    #     )

    # async def disconnect(self, close_code):
    #     """Clean disconnect"""
    #     if self.conversation:
    #         await database_sync_to_async(self.conversation.end_session)()

    #     # Leave room group
    #     if self.room_group_name:
    #         await self.channel_layer.group_discard(
    #             self.room_group_name, self.channel_name
    #         )

    # async def receive(self, text_data):
    #     """Enhanced message processing with error handling and typing indicators"""
    #     try:
    #         data = json.loads(text_data)
    #         message_type = data.get("type", "message")

    #         if message_type == "message":
    #             await self.handle_chat_message(data)
    #         elif message_type == "new_session":
    #             await self.handle_new_session()
    #         elif message_type == "get_sessions":
    #             await self.handle_get_sessions()
    #         else:
    #             await self.send_error("Unknown message type")

    #     except json.JSONDecodeError:
    #         await self.send_error("Invalid JSON format")
    #     except Exception as e:
    #         await self.send_error(f"Unexpected error: {str(e)}")

    # async def handle_chat_message(self, data):
    #     """Process chat message with AI response"""
    #     try:
    #         message = data.get("message", "").strip()
    #         session_id = data.get("session_id")

    #         if not message:
    #             await self.send_error("Message cannot be empty")
    #             return

    #         # Initialize or get conversation
    #         if not self.conversation or (
    #             session_id and str(self.conversation.session.id) != session_id
    #         ):
    #             self.conversation = await database_sync_to_async(ConversationManager)(
    #                 user=self.user, session_id=session_id
    #             )

    #         # Send typing indicator
    #         await self.send(json.dumps({"type": "typing", "is_typing": True}))

    #         # Add user message to conversation
    #         user_message = await database_sync_to_async(self.conversation.add_message)(
    #             content=message, is_user=True
    #         )

    #         # Get conversation history for AI
    #         conversation_history = await database_sync_to_async(
    #             self.conversation.format_for_ai
    #         )()

    #         # # Generate AI response (run in thread pool to avoid blocking)
    #         # ai_response_data = await asyncio.get_event_loop().run_in_executor(
    #         #     None, self.ai.generate_response, conversation_history, self.user
    #         # )

    #         session_persona = await database_sync_to_async(
    #             lambda: self.conversation.session.persona
    #         )()

    #         # Generate AI response WITH persona
    #         ai_response_data = await asyncio.get_event_loop().run_in_executor(
    #             None, self._generate_ai_response, conversation_history, session_persona
    #         )

    #         self.debug_json_serialization(ai_response_data, "AI Response Data")

    #         ai_response_data = self.convert_decimals(ai_response_data)
    #         # Stop typing indicator
    #         await self.send(json.dumps({"type": "typing", "is_typing": False}))

    #         if ai_response_data["success"]:
    #             # Add AI response to conversation
    #             ai_message = await database_sync_to_async(
    #                 self.conversation.add_message
    #             )(
    #                 content=ai_response_data["content"],
    #                 is_user=False,
    #                 ai_metadata=ai_response_data,
    #             )

    #             # Update session context if available
    #             if ai_response_data.get("user_context"):
    #                 await database_sync_to_async(
    #                     self.conversation.update_session_context
    #                 )(ai_response_data["user_context"])

    #             # Create response data
    #             response_data = {
    #                 "type": "message",
    #                 "content": ai_response_data["content"],
    #                 "session_id": str(self.conversation.session.id),
    #                 "message_id": ai_message.id,
    #                 "tokens_used": ai_response_data.get("tokens_used", 0),
    #                 "response_time": ai_response_data.get("response_time", 0),
    #                 "model_used": ai_response_data.get("model_used", ""),
    #                 "timestamp": ai_message.created_at.isoformat(),
    #             }

    #             # Send successful response
    #             await self.send(json.dumps(response_data))
    #         else:
    #             # Send error response
    #             await self.send_error(
    #                 f"AI Error: {ai_response_data.get('error', 'Unknown error')}"
    #             )

    #     except Exception as e:
    #         await self.send_error(f"Message processing error: {str(e)}")

    # async def handle_new_session(self):
    #     """Create new chat session"""
    #     try:
    #         self.conversation = await database_sync_to_async(ConversationManager)(
    #             user=self.user
    #         )

    #         session_summary = await database_sync_to_async(
    #             self.conversation.get_session_summary
    #         )()

    #         session_summary = self.convert_decimals(session_summary)

    #         await self.send(
    #             json.dumps({"type": "new_session", "session": session_summary})
    #         )

    #     except Exception as e:
    #         await self.send_error(f"Failed to create new session: {str(e)}")

    # async def handle_get_sessions(self):
    #     """Get user's chat sessions"""
    #     try:
    #         sessions = await database_sync_to_async(self.get_user_sessions)()

    #         sessions = self.convert_decimals(sessions)

    #         await self.send(json.dumps({"type": "sessions_list", "sessions": sessions}))
    #     except Exception as e:
    #         await self.send_error(f"Failed to get sessions: {str(e)}")

    # def get_user_sessions(self):
    #     """Get user's recent chat sessions"""

    #     sessions = ChatSession.objects.filter(user=self.user, is_active=True).order_by(
    #         "-updated_at"
    #     )[:10]

    #     return [
    #         {
    #             "id": str(session.id),
    #             "title": session.title,
    #             "message_count": session.message_count,
    #             "tokens_used": session.tokens_used,
    #             "created_at": session.created_at.isoformat(),
    #             "updated_at": session.updated_at.isoformat(),
    #         }
    #         for session in sessions
    #     ]

    # async def send_error(self, message: str):
    #     """Send error message to client"""
    #     await self.send(
    #         json.dumps(
    #             {
    #                 "type": "error",
    #                 "message": message,
    #                 "timestamp": timezone.now().isoformat(),
    #             }
    #         )
    #     )

    # def _generate_ai_response(self, conversation_history, persona):
    #     """Helper to call AI service with persona"""
    #     return self.ai.generate_response(
    #         conversation_history=conversation_history,
    #         user=self.user,
    #         persona=persona
    #     )


    # # Handle group messages (for future features like notifications)
    # async def chat_message(self, event):
    #     """Handle messages sent to the group"""
    #     await self.send(
    #         json.dumps({"type": "notification", "message": event["message"]})
    #     )
    pass
