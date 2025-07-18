from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from apps.chat.models import ChatSession, ChatMessage
from apps.chat.services.ai_chat_core import AIChatCore
from apps.chat.services.context_builder import ConversationManager
from rest_framework import serializers
import asyncio
import json


# Serializers
class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'content', 'is_user', 'bookmark', 'model_used', 
            'tokens_consumed', 'response_time', 'ai_metadata', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.ReadOnlyField()
    last_message_at = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'message_count', 'tokens_used',
            'created_at', 'updated_at', 'last_message_at', 'is_favorite'
        ]
        read_only_fields = ['id', 'message_count', 'tokens_used', 'created_at', 'updated_at']
    
    def get_last_message_at(self, obj):
        last_message = obj.messages.last()
        return last_message.created_at if last_message else obj.created_at


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    spiritual_context = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'message_count', 'tokens_used',
            'created_at', 'updated_at', 'messages', 'spiritual_context', 'is_favorite'
        ]
    
    def get_spiritual_context(self, obj):
        context = {}
        if obj.journey_reason:
            context['journey_reason'] = obj.journey_reason.journey_reason.option
        if obj.denomination:
            context['denomination'] = obj.denomination.denomination_option.name if obj.denomination.denomination_option else obj.denomination.name
        if obj.faith_goal:
            context['faith_goal'] = obj.faith_goal.faith_goal_option.option if obj.faith_goal.faith_goal_option else obj.faith_goal.text
        if obj.tone_preference:
            context['tone_preference'] = obj.tone_preference.tone_preference_option.name
        if obj.bible_familiarity:
            context['bible_familiarity'] = obj.bible_familiarity.bible_familiarity_option.label
        if obj.bible_version:
            context['bible_version'] = obj.bible_version.bible_version_option.title
        return context


# API Views
class CreateChatSessionView(generics.CreateAPIView):
    """Create a new chat session for the authenticated user"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Create conversation manager to handle onboarding data
        conversation_manager = ConversationManager(user=self.request.user)
        
        # Get user's spiritual context
        user_context = conversation_manager.get_user_spiritual_context()
        
        # Generate session title
        title = self._generate_session_title(user_context)
        
        # Create session with all onboarding data
        session = serializer.save(
            user=self.request.user,
            title=title,
            context_snapshot=user_context,
            journey_reason=conversation_manager._get_user_journey_reason(),
            denomination=conversation_manager._get_user_denomination(),
            faith_goal=conversation_manager._get_user_faith_goal(),
            tone_preference=conversation_manager._get_user_tone_preference(),
            bible_familiarity=conversation_manager._get_user_bible_familiarity(),
            bible_version=conversation_manager._get_user_bible_version(),
        )
        
        return session
    
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


class ChatSessionListView(generics.ListAPIView):
    """List all chat sessions for the authenticated user"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ChatSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-updated_at')
        
        # Filter by favorites if requested
        is_favorite = self.request.query_params.get('favorite', None)
        if is_favorite == 'true':
            queryset = queryset.filter(is_favorite=True)
        
        return queryset


class ChatSessionDetailView(generics.RetrieveAPIView):
    """Get detailed chat session with all messages"""
    serializer_class = ChatSessionDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSessionUpdateView(generics.UpdateAPIView):
    """Update chat session (title, favorite status, etc.)"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSessionDeleteView(generics.DestroyAPIView):
    """Delete a chat session"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete - mark as inactive
        instance.is_active = False
        instance.save()


class BookmarkMessageView(APIView):
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
            
            return Response({
                'success': True,
                'message_id': message_id,
                'bookmarked': bookmark_status,
                'message': f"Message {'bookmarked' if bookmark_status else 'unbookmarked'} successfully"
            })
            
        except ChatMessage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)


class BookmarkedMessagesView(generics.ListAPIView):
    """List all bookmarked messages for the user"""
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatMessage.objects.filter(
            session__user=self.request.user,
            bookmark=True
        ).order_by('-created_at')


class RegenerateResponseView(APIView):
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
                
                return Response({
                    'success': True,
                    'message': ChatMessageSerializer(ai_message).data,
                    'regenerated': True
                })
            else:
                return Response({
                    'success': False,
                    'error': ai_response_data.get('error', 'Failed to regenerate response')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ChatMessage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)


class SearchChatHistoryView(generics.ListAPIView):
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


class FavoriteChatSessionView(APIView):
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
            
            return Response({
                'success': True,
                'session_id': session_id,
                'is_favorite': favorite_status,
                'message': f"Session {'marked as favorite' if favorite_status else 'removed from favorites'} successfully"
            })
            
        except ChatSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class NeedMoreClarityView(APIView):
    """Handle "Need more clarity?" feedback on AI responses"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, message_id):
        try:
            ai_message = ChatMessage.objects.get(
                id=message_id,
                session__user=request.user,
                is_user=False
            )
            
            needs_clarity = request.data.get('needs_clarity', True)
            
            # Update AI metadata with clarity feedback
            metadata = ai_message.ai_metadata or {}
            metadata['clarity_feedback'] = {
                'needs_clarity': needs_clarity,
                'timestamp': timezone.now().isoformat(),
                'feedback_provided': True
            }
            ai_message.ai_metadata = metadata
            ai_message.save()
            
            if needs_clarity:
                # Generate follow-up clarification
                conversation_manager = ConversationManager(
                    user=request.user,
                    session_id=str(ai_message.session.id)
                )
                
                # Create a clarification prompt
                clarification_prompt = f"""The user indicated they need more clarity on your previous response: "{ai_message.content[:200]}..."

Please provide a clearer, more detailed explanation that addresses potential confusion. Focus on:
1. Simplifying complex concepts
2. Providing additional context
3. Using more relatable examples
4. Breaking down the information into smaller parts"""
                
                # Get user context
                user_context = conversation_manager.get_user_spiritual_context()
                
                # Generate clarification
                ai_core = AIChatCore()
                clarification_history = [{"role": "user", "content": clarification_prompt}]
                
                clarification_response = ai_core.generate_bible_response(
                    conversation_history=clarification_history,
                    user=request.user,
                    user_context=user_context
                )
                
                if clarification_response["success"]:
                    # Create new clarification message
                    clarification_message = conversation_manager.add_message(
                        content=clarification_response["content"],
                        is_user=False,
                        ai_metadata=clarification_response
                    )
                    
                    return Response({
                        'success': True,
                        'needs_clarity': needs_clarity,
                        'clarification_provided': True,
                        'clarification_message': ChatMessageSerializer(clarification_message).data
                    })
            
            return Response({
                'success': True,
                'needs_clarity': needs_clarity,
                'clarification_provided': False,
                'message': 'Feedback recorded successfully'
            })
            
        except ChatMessage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ChatStatisticsView(APIView):
    """Get user's chat statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
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
        
        return Response(stats)


class ExportChatHistoryView(APIView):
    """Export chat history as JSON"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).prefetch_related('messages')
        
        export_data = {
            'user_id': request.user.id,
            'export_date': timezone.now().isoformat(),
            'sessions': []
        }
        
        for session in sessions:
            session_data = {
                'id': str(session.id),
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'is_favorite': session.is_favorite,
                'messages': []
            }
            
            for message in session.messages.all():
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'is_user': message.is_user,
                    'bookmark': message.bookmark,
                    'created_at': message.created_at.isoformat(),
                }
                session_data['messages'].append(message_data)
            
            export_data['sessions'].append(session_data)
        
        return Response(export_data)

