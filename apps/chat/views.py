from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction, models
from apps.chat.models import ChatSession, ChatMessage
from apps.chat.services.ai_chat_core import AIChatCore
from apps.chat.services.context_builder import ConversationManager
from rest_framework import serializers
import asyncio
import json
from apps.core.utils.mixins import BaseResponseMixin
from apps.chat.serializers import ChatMessageSerializer, ChatSessionSerializer, ChatSessionDetailSerializer


# API Views
class CreateChatSessionView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("DEBUG - CreateChatSessionView.post: Creating/saving session")
        try:
            session_id = request.data.get('session_id')
            print(f"DEBUG - session_id received: {session_id}")

            session = None
            if session_id:
                session = ChatSession.objects.get(id=session_id, user=request.user)
                print(f"DEBUG - Found session, is_saved before: {session.is_saved}, messages: {session.message_count}")
                session.is_saved = True
                session.is_active = True
                if not session.title:
                    session.title = f"Bible Conversation - {timezone.now().strftime('%B %d')}"
                session.save()
                print(f"DEBUG - Session saved! is_saved now: {session.is_saved}")

            # DEBUG - print what we're about to delete
            leftover = ChatSession.objects.filter(
                user=request.user,
                is_saved=False,
            )
            if session_id:
                leftover = leftover.exclude(id=session_id)

            print(f"DEBUG - About to delete these sessions:")
            for s in leftover:
                print(f"  → id: {s.id}, is_saved: {s.is_saved}, messages: {s.message_count}")

            count = leftover.count()
            leftover.delete()
            print(f"DEBUG - Cleaned up {count} leftover temp sessions")

            # Now create ONE fresh temp session
            new_conversation = ConversationManager(user=request.user)
            new_session = new_conversation.session
            print(f"DEBUG - New temp session created: {new_session.id}")

            return self.created_response(
                data={
                    'saved_session': ChatSessionSerializer(session).data if session else None,
                    'new_session': ChatSessionSerializer(new_session).data
                },
                message="Session saved and new session started"
            )

        except ChatSession.DoesNotExist:
            print(f"DEBUG - Session NOT found: {session_id}")
            return self.not_found_response(message="Session not found")
        except Exception as e:
            print(f"DEBUG - Exception: {str(e)}")
            return self.handle_exception(e)
    
    def _generate_session_title(self, user_context):
        """Generate meaningful session title"""
        journey_reason = user_context.get('journey_reason', '')
        faith_goal = user_context.get('faith_goal', '')
        
        if journey_reason:
            return f"Bible Chat - {journey_reason}"
        elif faith_goal:
            return f"Bible Study - {faith_goal}"
        else:
            return f"Bible Conversation - {timezone.now().strftime('%B %d')}"

class StartChatSessionView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("DEBUG - StartChatSessionView.post: Starting new session")
        try:
            # Check if unsaved temp session already exists
            existing_session = ChatSession.objects.filter(
                user=request.user,
                is_saved=False,
                is_active=True
            ).order_by('-created_at').first()

            if existing_session:
                # Return same temp session
                serializer = ChatSessionSerializer(existing_session)
                print(f"DEBUG - StartChatSessionView.post: Resumed existing session {existing_session.id}")
                return self.success_response(
                    data=serializer.data,
                    message="Resumed existing session"
                )

            # No temp session exists — create fresh one
            conversation_manager = ConversationManager(user=request.user)
            new_session = conversation_manager.session
            print(f"DEBUG - StartChatSessionView.post: Created new session {new_session.id}")

            serializer = ChatSessionSerializer(new_session)
            return self.created_response(
                data=serializer.data,
                message="New session started"
            )

        except Exception as e:
            print(f"DEBUG - StartChatSessionView.post: Exception {str(e)}")
            return self.handle_exception(e)

class ChatSessionListView(BaseResponseMixin, generics.ListAPIView):
    """List all chat sessions for the authenticated user"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ChatSession.objects.filter(
            user=self.request.user,
            is_active=True,
            is_saved=True 
        ).order_by('-updated_at')

        is_favorite = self.request.query_params.get('favorite', None)
        if is_favorite == 'true':
            queryset = queryset.filter(is_favorite=True)

        return queryset

    def list(self, request, *args, **kwargs):
        print("DEBUG - ChatSessionListView.list: Listing chat sessions")
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            print(f"DEBUG - ChatSessionListView.list: Found {len(serializer.data)} sessions")
            return self.success_response(
                data=serializer.data,
                message="Chat sessions retrieved successfully"
            )
        except Exception as e:
            print(f"DEBUG - ChatSessionListView.list: Exception {str(e)}")
            return self.handle_exception(e)


class ChatSessionDetailView(BaseResponseMixin, APIView):
    """Get detailed chat session with all messages"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        print(f"DEBUG - ChatSessionDetailView.get: Getting session {session_id}")
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user,
            )
            
            serializer = ChatSessionDetailSerializer(session)
            print(f"DEBUG - ChatSessionDetailView.get: Session {session_id} has {len(serializer.data.get('messages', []))} messages")
            return self.success_response(
                data=serializer.data,
                message="Chat session retrieved successfully"
            )
            
        except ChatSession.DoesNotExist:
            print(f"DEBUG - ChatSessionDetailView.get: Session {session_id} not found")
            return self.not_found_response(message="Session not found")
        except Exception as e:
            print(f"DEBUG - ChatSessionDetailView.get: Exception {str(e)}")
            return self.handle_exception(e)
        

class ChatSessionUpdateView(BaseResponseMixin, generics.UpdateAPIView):
    """Update chat session (title, favorite status, etc.)"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'  # Add this
    lookup_url_kwarg = 'session_id' 
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                self.perform_update(serializer)
                return self.updated_response(
                    data=serializer.data,
                    message="Chat session updated successfully"
                )
            else:
                return self.bad_request_response(
                    message="Invalid data provided",
                    errors=serializer.errors
                )
        except Exception as e:
            return self.handle_exception(e)


class ChatSessionDeleteView(BaseResponseMixin, APIView):
    """Delete a chat session"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, session_id):
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user
            )
            
            # Hard delete - completely remove the session and all related messages
            session.delete()
            
            return self.success_response(
                message="Chat session deleted successfully",
                status_code=status.HTTP_200_OK
            )
            
        except ChatSession.DoesNotExist:
            return self.not_found_response(message="Session not found")
        except Exception as e:
            return self.handle_exception(e)

class BookmarkMessageView(BaseResponseMixin, APIView):
    """Bookmark/unbookmark a specific message"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, message_id):
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                session__user=request.user
            )
            
            bookmark_status = request.data.get('bookmark', True)
            message.bookmark = bookmark_status
            message.save()
            
            return self.success_response(
                data={
                    'message_id': message_id,
                    'bookmarked': bookmark_status
                },
                message=f"Message {'bookmarked' if bookmark_status else 'unbookmarked'} successfully"
            )
            
        except ChatMessage.DoesNotExist:
            return self.not_found_response(message="Message not found")
        except Exception as e:
            return self.handle_exception(e)


class BookmarkedMessagesView(BaseResponseMixin, generics.ListAPIView):
    """List all bookmarked messages for the user"""
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatMessage.objects.filter(
            session__user=self.request.user,
            bookmark=True
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message="Bookmarked messages retrieved successfully"
            )
        except Exception as e:
            return self.handle_exception(e)


class RegenerateResponseView(BaseResponseMixin, APIView):
    """Regenerate AI response for a specific message"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, message_id):
        try:
            # Get the AI message to regenerate
            ai_message = ChatMessage.objects.get(
                id=message_id,
                session__user=request.user,
                is_user=False
            )
            
            # Get the conversation manager
            conversation_manager = ConversationManager(
                user=request.user,
                session_id=str(ai_message.session.id)
            )
            
            # Get conversation history up to this point
            conversation_history = conversation_manager.format_for_ai()
            user_context = conversation_manager.get_user_spiritual_context()
            
            # Generate new AI response
            ai_core = AIChatCore()
            ai_response_data = ai_core.generate_bible_response(
                conversation_history=conversation_history,
                user=request.user,
                user_context=user_context
            )
            
            if ai_response_data["success"]:
                # Update the existing message
                ai_message.content = ai_response_data["content"]
                ai_message.model_used = ai_response_data.get("model_used", "")
                ai_message.tokens_consumed = ai_response_data.get("tokens_used", 0)
                ai_message.response_time = ai_response_data.get("response_time", 0.0)
                ai_message.ai_metadata = ai_response_data
                ai_message.updated_at = timezone.now()
                ai_message.save()
                
                # Update session tokens
                ai_message.session.tokens_used += ai_response_data.get("tokens_used", 0)
                ai_message.session.save()
                
                return self.success_response(
                    data={
                        'message': ChatMessageSerializer(ai_message).data,
                        'regenerated': True
                    },
                    message="Response regenerated successfully"
                )
            else:
                return self.error_response(
                    message=ai_response_data.get('error', 'Failed to regenerate response'),
                    error_code="REGENERATION_FAILED",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except ChatMessage.DoesNotExist:
            return self.not_found_response(message="Message not found")
        except Exception as e:
            return self.handle_exception(e)


class SearchChatHistoryView(BaseResponseMixin, generics.ListAPIView):
    """Search through all chat history for specific text"""
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        
        if not query:
            return ChatMessage.objects.none()
        
        # Search in message content
        queryset = ChatMessage.objects.filter(
            session__user=self.request.user,
            session__is_active=True,
            content__icontains=query
        ).order_by('-created_at')
        
        # Filter by session if provided
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by message type if provided
        message_type = self.request.query_params.get('type')
        if message_type == 'user':
            queryset = queryset.filter(is_user=True)
        elif message_type == 'ai':
            queryset = queryset.filter(is_user=False)
        
        return queryset

    def list(self, request, *args, **kwargs):
        try:
            query = request.query_params.get('q', '')
            if not query:
                return self.bad_request_response(message="Search query parameter 'q' is required")
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message=f"Search results for '{query}' retrieved successfully"
            )
        except Exception as e:
            return self.handle_exception(e)


class FavoriteChatSessionView(BaseResponseMixin, APIView):
    """Mark/unmark chat session as favorite"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user
            )
            
            favorite_status = request.data.get('favorite', True)
            session.is_favorite = favorite_status
            session.save()
            
            return self.success_response(
                data={
                    'session_id': session_id,
                    'is_favorite': favorite_status
                },
                message=f"Session {'marked as favorite' if favorite_status else 'removed from favorites'} successfully"
            )
            
        except ChatSession.DoesNotExist:
            return self.not_found_response(message="Session not found")
        except Exception as e:
            return self.handle_exception(e)


class NeedMoreClarityView(BaseResponseMixin, APIView):
    """
    Handle 'Need more clarity?' — YES or NO.
    YES → Deeper clarification (no restating, max 120 words)
    NO  → AI suggests follow-up conversation question
           Frontend MUST append '— or —\nStart a new chat' as static UI text
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request, message_id):
        try:
            ai_message = ChatMessage.objects.get(
                id=message_id,
                session__user=request.user,
                is_user=False
            )
 
            needs_clarity = request.data.get('needs_clarity', True)
 
            # Record feedback
            metadata = ai_message.ai_metadata or {}
            metadata['clarity_feedback'] = {
                'needs_clarity': needs_clarity,
                'timestamp': timezone.now().isoformat(),
            }
            ai_message.ai_metadata = metadata
            ai_message.save()
 
            # Get user's tone preference
            conversation_manager = ConversationManager(
                user=request.user,
                session_id=str(ai_message.session.id)
            )
            user_context = conversation_manager.get_user_spiritual_context()
            tone = (
                user_context.get("tone_preference", {}).get("name", "Clear and Hopeful")
                if user_context else "Clear and Hopeful"
            )
 
            ai_core = AIChatCore()
 
            if needs_clarity:
                # YES → deeper expansion
                result = ai_core.generate_clarification_yes(
                    original_response=ai_message.content,
                    tone=tone,
                )
 
                if result["success"]:
                    new_message = conversation_manager.add_message(
                        content=result["content"],
                        is_user=False,
                        ai_metadata=result,
                    )
                    return self.success_response(
                        data={
                            'needs_clarity': True,
                            'clarification_provided': True,
                            'show_clarification': False, 
                            'clarification_message': ChatMessageSerializer(new_message).data
                        },
                        message="Clarification provided"
                    )
            else:
                # NO → follow-up question suggestion
                result = ai_core.generate_clarification_no(
                    original_response=ai_message.content,
                    tone=tone,
                )
 
                if result["success"]:
                    new_message = conversation_manager.add_message(
                        content=result["content"],
                        is_user=False,
                        ai_metadata=result,
                    )
                    return self.success_response(
                        data={
                            'needs_clarity': False,
                            'clarification_provided': True,
                            'show_clarification': False,
                            # Frontend renders '— or —\nStart a new chat' below this
                            'show_new_chat_option': True,
                            'continuation_message': ChatMessageSerializer(new_message).data
                        },
                        message="Follow-up question generated"
                    )
 
            return self.error_response(
                message="Failed to generate response",
                status_code=500
            )
 
        except ChatMessage.DoesNotExist:
            return self.not_found_response(message="Message not found")
        except Exception as e:
            return self.handle_exception(e)

class ChatStatisticsView(BaseResponseMixin, APIView):
    """Get user's chat statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user_sessions = ChatSession.objects.filter(
                user=request.user,
                is_active=True
            )
            
            user_messages = ChatMessage.objects.filter(
                session__user=request.user,
                session__is_active=True
            )
            
            stats = {
                'total_sessions': user_sessions.count(),
                'favorite_sessions': user_sessions.filter(is_favorite=True).count(),
                'total_messages': user_messages.count(),
                'user_messages': user_messages.filter(is_user=True).count(),
                'ai_messages': user_messages.filter(is_user=False).count(),
                'bookmarked_messages': user_messages.filter(bookmark=True).count(),
                'total_tokens_used': user_sessions.aggregate(total=models.Sum('tokens_used'))['total'] or 0,
                'average_session_length': user_sessions.aggregate(avg=Avg('message_count'))['avg'] or 0,
                'recent_activity': user_sessions.order_by('-updated_at')[:5].values(
                    'id', 'title', 'updated_at', 'message_count'
                )
            }
            
            return self.success_response(
                data=stats,
                message="Chat statistics retrieved successfully"
            )
        except Exception as e:
            return self.handle_exception(e)


class ExportChatHistoryView(BaseResponseMixin, APIView):
    """Export chat history as JSON"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print("DEBUG - ExportChatHistoryView.get: Exporting chat history")
        try:
            sessions = ChatSession.objects.filter(
                user=request.user,
                is_saved=True
            ).prefetch_related('messages')

            print(f"DEBUG export - all is_saved sessions:")
            for s in sessions:
                print(f"  → id: {s.id}, is_active: {s.is_active}, is_saved: {s.is_saved}, messages: {s.message_count}")
                
            export_data = {
                'user_id': request.user.id,
                'export_date': timezone.now().isoformat(),
                'sessions': []
            }
            
            for session in sessions:
                            # Get first user message as preview
                first_user_msg = session.messages.filter(is_user=True).order_by('created_at').first()
                preview = ""
                if first_user_msg and first_user_msg.content:
                    preview = first_user_msg.content[:100] + "..." if len(first_user_msg.content) > 100 else first_user_msg.content

                session_data = {
                    'id': str(session.id),
                    'title': session.title,
                    'preview': preview,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat(),
                    'is_saved': session.is_saved,
                    'is_favorite': session.is_favorite,
                    'message_count': session.message_count,
                    'messages': []
                }
                
                for message in session.messages.all():
                    message_data = {
                        'id': message.id,
                        'content': message.content,
                        'is_user': message.is_user,
                        'bookmark': message.bookmark,
                        'has_voice': message.has_voice,
                        'voice_transcript': message.voice_transcript,
                        'voice_file_url': None,
                        'created_at': message.created_at.isoformat(),
                    }
                    
                    # Add voice file URL if exists
                    if message.voice_file:
                        message_data['voice_file_url'] = message.voice_file.url
                    
                    session_data['messages'].append(message_data)
                
                export_data['sessions'].append(session_data)
            
            print(f"DEBUG - ExportChatHistoryView.get: Exported {len(export_data['sessions'])} sessions")
            return self.success_response(
                data=export_data,
                message="Chat history exported successfully"
            )
        except Exception as e:
            print(f"DEBUG - ExportChatHistoryView.get: Exception {str(e)}")
            return self.handle_exception(e)

class ClearAllChatHistoryView(BaseResponseMixin, APIView):
    """Delete all saved chat sessions for the user"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        print("DEBUG - ClearAllChatHistoryView.delete: Clearing all chat history")
        try:
            deleted_count, _ = ChatSession.objects.filter(
                user=request.user,
                is_saved=True
            ).delete()
            
            print(f"DEBUG - ClearAllChatHistoryView.delete: Deleted {deleted_count} sessions")
            return self.success_response(
                data={'deleted_sessions': deleted_count},
                message=f"All chat history cleared successfully"
            )
        except Exception as e:
            print(f"DEBUG - ClearAllChatHistoryView.delete: Exception {str(e)}")
            return self.handle_exception(e)

import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment

class VoiceToTextAPIView(BaseResponseMixin, APIView):
    def post(self, request):
        temp_file_path = None
        wav_file_path = None
        
        try:
            voice_file = request.FILES.get('voice_file')
            session_id = request.data.get('session_id')
            
            if not voice_file:
                return self.error_response(
                    message='No voice file provided',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not session_id:
                return self.error_response(
                    message='session_id is required',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if session exists
            try:
                chat_session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                return self.error_response(
                    message='Invalid session ID',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            # Check file size
            if voice_file.size > 10 * 1024 * 1024:  # 10MB limit
                return self.error_response(
                    message='File size too large. Maximum 10MB allowed',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Save original file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in voice_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Convert any audio format to WAV using pydub
            try:
                audio = AudioSegment.from_file(temp_file_path)
                wav_file_path = temp_file_path + '.wav'
                audio.export(wav_file_path, format='wav')
            except Exception as e:
                return self.error_response(
                    message=f'Invalid audio file format: {str(e)}',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert voice to text
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            
            # Clean up temp files
            self._cleanup_files(temp_file_path, wav_file_path)
            
            if not text:
                return self.error_response(
                    message='No speech detected in the audio file',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Create ChatMessage with both voice file and transcript
            message = ChatMessage.objects.create(
                session=chat_session,
                content=text,  # The transcript
                voice_transcript=text,  # Store transcript separately for clarity
                is_user=True,
                voice_file=voice_file,  # Save the original audio file
                has_voice=True
            )
            
            # Update session message count
            chat_session.message_count += 1
            chat_session.save()
                
            return self.success_response(
                data={
                    'success': True,
                    'message_id': str(message.id),
                    'transcript': text,
                    'voice_url': message.voice_file.url if message.voice_file else None,
                    'session_id': str(chat_session.id),
                    'message': 'Voice successfully converted to text and saved'
                },
                status_code=status.HTTP_200_OK
            )
            
        except sr.UnknownValueError:
            self._cleanup_files(temp_file_path, wav_file_path)
            return self.error_response(
                message='Could not understand the audio. Please speak clearly',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except sr.RequestError as e:
            self._cleanup_files(temp_file_path, wav_file_path)
            return self.error_response(
                message=f'Speech recognition service error: {str(e)}',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            self._cleanup_files(temp_file_path, wav_file_path)
            return self.error_response(
                message=f'An unexpected error occurred: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _cleanup_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass