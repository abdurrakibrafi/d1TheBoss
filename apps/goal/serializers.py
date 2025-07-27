# serializers.py - Goal serializers

from rest_framework import serializers
from .models import UserGoal, ChapterRead, ConversationInteraction, ShareActivity

class UserGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    goal_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    week_end = serializers.SerializerMethodField()
    
    class Meta:
        model = UserGoal
        fields = [
            'id',
            'goal_type', 
            'goal_display',
            'target_count', 
            'current_count', 
            'completed', 
            'progress_percentage',
            'week_start',
            'week_end',
            'days_remaining',
            'created_at'
        ]
    
    def get_progress_percentage(self, obj):
        if obj.target_count == 0:
            return 0
        return round((obj.current_count / obj.target_count) * 100, 1)
    
    def get_days_remaining(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        week_end = obj.week_start + timezone.timedelta(days=6)
        if today > week_end:
            return 0  # Week is over
        return (week_end - today).days + 1
    
    def get_week_end(self, obj):
        from django.utils import timezone
        return obj.week_start + timezone.timedelta(days=6)

class ChapterReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChapterRead
        fields = ['bible_id', 'chapter_id', 'read_at']

class ConversationInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationInteraction
        fields = ['content_type', 'content_id', 'interaction_type', 'created_at']

class ShareActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareActivity
        fields = ['content_type', 'content_id', 'share_platform', 'shared_at']

class GoalStatsSerializer(serializers.Serializer):
    """Serializer for goal statistics"""
    total_chapters_read = serializers.IntegerField()
    total_conversations = serializers.IntegerField()
    total_shares = serializers.IntegerField()
    current_week_scripture = serializers.IntegerField()
    current_week_conversations = serializers.IntegerField()
    current_week_shares = serializers.IntegerField()