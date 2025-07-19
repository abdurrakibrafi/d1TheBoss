from typing import Dict, List, Optional
from apps.chat.models import ChatSession, ChatMessage
from apps.onboarding.models import (
    JourneyReason, Denomination, FaithGoal, TonePreference, 
    BibleFamiliarity, BibleVersion
)
from django.utils import timezone
import uuid


class ConversationManager:
    """Bible-focused conversation manager with spiritual context"""
    
    def __init__(self, user, session_id: Optional[str] = None):
        self.user = user
        self.session = self._get_or_create_session(session_id)
        self.max_history_messages = 20
        self._user_context = None

    def _get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create new one"""
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=self.user)
                if not session.is_active:
                    session.is_active = True
                    session.save()
                return session
            except ChatSession.DoesNotExist:
                pass

        # Get user's onboarding data
        user_context = self._get_user_spiritual_context()
        
        # Create session title based on user's journey
        title = self._generate_session_title(user_context)
        
        # Create new session with user's onboarding context
        session = ChatSession.objects.create(
            user=self.user,
            title=title,
            context_snapshot=user_context,
            # Link onboarding data
            journey_reason=self._get_user_journey_reason(),
            denomination=self._get_user_denomination(),
            faith_goal=self._get_user_faith_goal(),
            tone_preference=self._get_user_tone_preference(),
            bible_familiarity=self._get_user_bible_familiarity(),
            bible_version=self._get_user_bible_version(),
        )
        
        return session

    def _generate_session_title(self, user_context: Dict) -> str:
        """Generate meaningful session title based on user's spiritual journey"""
        journey_reason = user_context.get('journey_reason', '')
        faith_goal = user_context.get('faith_goal', '')
        
        if journey_reason:
            return f"Bible Chat - {journey_reason}"
        elif faith_goal:
            return f"Bible Study - {faith_goal}"
        else:
            return f"Bible Conversation - {timezone.now().strftime('%B %d')}"

    def get_user_spiritual_context(self) -> Dict:
        """Get comprehensive spiritual context for AI"""
        if self._user_context is None:
            self._user_context = self._get_user_spiritual_context()
        return self._user_context

    def _get_user_spiritual_context(self) -> Dict:
        """Build complete spiritual context from onboarding data"""
        context = {
            'user_id': self.user.id,
            'timestamp': timezone.now().isoformat(),
        }
        
        # Journey Reason
        journey_reason = self._get_user_journey_reason()
        if journey_reason:
            context['journey_reason'] = journey_reason.journey_reason.option
            context['journey_reason_id'] = journey_reason.id
        
        # Denomination
        denomination = self._get_user_denomination()
        if denomination:
            context['denomination'] = denomination.denomination_option.name if denomination.denomination_option else denomination.name
            context['denomination_id'] = denomination.id
        
        # Faith Goals
        faith_goal = self._get_user_faith_goal()
        if faith_goal:
            context['faith_goal'] = faith_goal.faith_goal_option.option if faith_goal.faith_goal_option else faith_goal.text
            context['faith_goal_question'] = faith_goal.faith_goal_option.faith_goal_question.question if faith_goal.faith_goal_option else None
            context['faith_goal_id'] = faith_goal.id
        
        # Tone Preference
        tone_preference = self._get_user_tone_preference()
        if tone_preference:
            context['tone_preference'] = {
                'title': tone_preference.tone_preference_option.title,
                'name': tone_preference.tone_preference_option.name,
                'description': tone_preference.tone_preference_option.description,
                'quote': tone_preference.tone_preference_option.quote,
            }
            context['tone_preference_id'] = tone_preference.id
        
        # Bible Familiarity
        bible_familiarity = self._get_user_bible_familiarity()
        if bible_familiarity:
            context['bible_familiarity'] = {
                'label': bible_familiarity.bible_familiarity_option.label,
                'title': bible_familiarity.bible_familiarity_option.title,
                'text1': bible_familiarity.bible_familiarity_option.text1,
                'text2': bible_familiarity.bible_familiarity_option.text2,
                'custom_text': bible_familiarity.text,
            }
            context['bible_familiarity_id'] = bible_familiarity.id
        
        # Bible Version
        bible_version = self._get_user_bible_version()
        if bible_version:
            context['bible_version'] = {
                'title': bible_version.bible_version_option.title,
                'subtitle': bible_version.bible_version_option.subtitle,
                'api_bible_id': bible_version.bible_version_option.api_bible_id,
            }
            context['bible_version_id'] = bible_version.id
        
        return context

    def _get_user_journey_reason(self) -> Optional[JourneyReason]:
        """Get user's journey reason"""
        try:
            return JourneyReason.objects.filter(user=self.user).first()  # Changed from .get() to .filter().first()
        except JourneyReason.DoesNotExist:
            return None

    def _get_user_denomination(self) -> Optional[Denomination]:
        """Get user's denomination"""
        try:
            return Denomination.objects.filter(user=self.user).first()  # Changed
        except Denomination.DoesNotExist:
            return None

    def _get_user_faith_goal(self) -> Optional[FaithGoal]:
        """Get user's faith goal"""
        try:
            return FaithGoal.objects.filter(user=self.user).first()  # Changed - THIS IS THE MAIN ERROR
        except FaithGoal.DoesNotExist:
            return None

    def _get_user_tone_preference(self) -> Optional[TonePreference]:
        """Get user's tone preference"""
        try:
            return TonePreference.objects.filter(user=self.user).first()  # Changed
        except TonePreference.DoesNotExist:
            return None

    def _get_user_bible_familiarity(self) -> Optional[BibleFamiliarity]:
        """Get user's Bible familiarity"""
        try:
            return BibleFamiliarity.objects.filter(user=self.user).first()  # Changed
        except BibleFamiliarity.DoesNotExist:
            return None

    def _get_user_bible_version(self) -> Optional[BibleVersion]:
        """Get user's preferred Bible version"""
        try:
            return BibleVersion.objects.filter(user=self.user).first()  # Changed
        except BibleVersion.DoesNotExist:
            return None

    def add_message(self, content: str, is_user: bool, ai_metadata: dict = None) -> ChatMessage:
        """Add message to conversation"""
        message = ChatMessage.objects.create(
            session=self.session,
            content=content,
            is_user=is_user,
            ai_metadata=ai_metadata or {},
            # AI-specific fields
            model_used=ai_metadata.get('model_used', '') if ai_metadata else '',
            tokens_consumed=ai_metadata.get('tokens_used', 0) if ai_metadata else 0,
            response_time=ai_metadata.get('response_time', 0.0) if ai_metadata else 0.0,
        )
        
        # Update session counters
        self.session.message_count += 1
        if ai_metadata:
            self.session.tokens_used += ai_metadata.get('tokens_used', 0)
        self.session.save()
        
        return message

    def format_for_ai(self) -> List[Dict]:
        """Format conversation history for AI API"""
        messages = self.session.messages.order_by('-created_at')[:self.max_history_messages]
        
        formatted = []
        for message in reversed(messages):
            role = "user" if message.is_user else "assistant"
            formatted.append({
                "role": role,
                "content": message.content
            })
        
        return formatted

    def get_session_summary(self) -> Dict:
        """Get session summary"""
        return {
            'id': str(self.session.id),
            'title': self.session.title,
            'message_count': self.session.message_count,
            'tokens_used': self.session.tokens_used,
            'created_at': self.session.created_at.isoformat(),
            'updated_at': self.session.updated_at.isoformat(),
            'spiritual_context': self.get_user_spiritual_context(),
        }

    def update_session_context(self, context: Dict):
        """Update session context"""
        current_context = self.session.context_snapshot or {}
        current_context.update(context)
        self.session.context_snapshot = current_context
        self.session.save()

    def end_session(self):
        """End conversation session"""
        self.session.is_active = False
        self.session.save()

    def get_bookmarked_messages(self) -> List[Dict]:
        """Get bookmarked messages from this session"""
        bookmarked = self.session.messages.filter(bookmark=True).order_by('-created_at')
        
        return [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'created_at': msg.created_at.isoformat(),
        } for msg in bookmarked]

    def get_conversation_insights(self) -> Dict:
        """Get insights about the conversation for AI context"""
        messages = self.session.messages.all()
        
        insights = {
            'total_messages': messages.count(),
            'user_messages': messages.filter(is_user=True).count(),
            'ai_messages': messages.filter(is_user=False).count(),
            'bookmarked_count': messages.filter(bookmark=True).count(),
            'session_duration': None,
            'common_topics': [],  # Could be enhanced with NLP
        }
        
        if messages.exists():
            first_message = messages.first()
            last_message = messages.last()
            duration = last_message.created_at - first_message.created_at
            insights['session_duration'] = duration.total_seconds()
        
        return insights