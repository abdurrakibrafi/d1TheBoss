from rest_framework import serializers
from apps.chat.models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'content', 'is_user', 'bookmark', 'model_used', 'voice_file', 'voice_transcript', 'has_voice',
            'tokens_consumed', 'response_time', 'ai_metadata', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.ReadOnlyField()
    last_message_at = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    preview = serializers.SerializerMethodField()
 
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'is_saved', 'message_count', 'tokens_used',
            'created_at', 'updated_at', 'last_message_at', 'is_favorite', 'preview'
        ]
        read_only_fields = ['id', 'message_count', 'tokens_used', 'created_at', 'updated_at']
 
    def get_last_message_at(self, obj):
        last_message = obj.messages.last()
        return last_message.created_at if last_message else obj.created_at
 
    def get_preview(self, obj):
        """Return the first user question — truncated with '...' if too long"""
        first_user_message = obj.messages.filter(is_user=True).order_by('created_at').first()
        if not first_user_message or not first_user_message.content:
            return ""
        content = first_user_message.content
        if len(content) > 100:
            return content[:97] + "..."
        return content


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    spiritual_context = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'is_saved', 'message_count', 'tokens_used',
            'created_at', 'updated_at', 'messages', 'spiritual_context', 'is_favorite'
        ]
    
    def get_spiritual_context(self, obj):
        context = {}
        if obj.journey_reason:
            context['journey_reason'] = obj.journey_reason.journey_reason.option
        if obj.denomination:
            context['denomination'] = (
                obj.denomination.denomination_option.name
                if obj.denomination.denomination_option else obj.denomination.name
            )
        if obj.faith_goal:
            context['faith_goal'] = (
                obj.faith_goal.faith_goal_option.option
                if obj.faith_goal.faith_goal_option else obj.faith_goal.text
            )
        if obj.tone_preference:
            option = obj.tone_preference.tone_preference_option
            context['tone_preference'] = option.name if option else None
        if obj.bible_familiarity:
            option = obj.bible_familiarity.bible_familiarity_option
            context['bible_familiarity'] = option.label if option else None
        if obj.bible_version:
            option = obj.bible_version.bible_version_option
            context['bible_version'] = option.title if option else None
        return context