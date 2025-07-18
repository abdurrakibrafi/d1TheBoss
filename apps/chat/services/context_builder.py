from typing import Dict, List, Optional
# from apps.chat.models import ChatSession, ChatMessage
# from apps.aipersona.models import AIPersona


class ConversationManager:
    """Enhanced conversation manager with persona support"""
    
    # def __init__(self, user, session_id: Optional[str] = None, persona: AIPersona = None):
    #     self.user = user
    #     self.session = self._get_or_create_session(session_id, persona)
    #     self.context_data = None
    #     self.max_history_messages = 20

    # def _get_or_create_session(self, session_id: Optional[str] = None, persona: AIPersona = None) -> ChatSession:
    #     """Get existing session or create new one"""
    #     if session_id:
    #         try:
    #             session = ChatSession.objects.get(id=session_id, user=self.user)
    #             if not session.is_active:
    #                 session.is_active = True
    #                 session.save()
    #             return session
    #         except ChatSession.DoesNotExist:
    #             pass
        
    #     # Get default persona if not provided
    #     if not persona:
    #         persona = AIPersona.objects.filter(is_active=True).first()
        
    #     # Create new session
    #     return ChatSession.objects.create(
    #         user=self.user,
    #         persona=persona,
    #         title=f"Chat with {persona.name}" if persona else "New Chat"
    #     )

    # def add_message(self, content: str, is_user: bool, ai_metadata: dict = None) -> ChatMessage:
    #     """Add message to conversation"""
    #     message = ChatMessage.objects.create(
    #         session=self.session,
    #         content=content,
    #         is_user=is_user,
    #         ai_metadata=ai_metadata or {}
    #     )
        
    #     # Update session counters
    #     self.session.message_count += 1
    #     if ai_metadata:
    #         self.session.tokens_used += ai_metadata.get('tokens_used', 0)
    #     self.session.save()
        
    #     return message

    # def format_for_ai(self) -> List[Dict]:
    #     """Format conversation history for AI API"""
    #     messages = self.session.messages.order_by('-created_at')[:self.max_history_messages]
        
    #     formatted = []
    #     for message in reversed(messages):
    #         role = "user" if message.is_user else "assistant"
    #         formatted.append({
    #             "role": role,
    #             "content": message.content
    #         })
        
    #     return formatted

    # def get_session_summary(self) -> Dict:
    #     """Get session summary"""
    #     return {
    #         'id': str(self.session.id),
    #         'title': self.session.title,
    #         'message_count': self.session.message_count,
    #         'tokens_used': self.session.tokens_used,
    #         'created_at': self.session.created_at.isoformat(),
    #         'updated_at': self.session.updated_at.isoformat()
    #     }

    # def update_session_context(self, context: Dict):
    #     """Update session context"""
    #     self.session.context_snapshot = context
    #     self.session.save()

    # def end_session(self):
    #     """End conversation session"""
    #     self.session.is_active = False
    #     self.session.save()
    pass