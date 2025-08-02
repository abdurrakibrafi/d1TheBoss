# models.py - Goal tracking models

from django.db import models
from apps.accounts.models import User 
from django.utils import timezone
from datetime import timedelta

class UserGoal(models.Model):
    GOAL_TYPES = [
        ('scripture', 'Scripture Knowledge'),
        ('share_faith', 'Inspiration Goal'), 
        ('conversation', 'Confidence Goal'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_count = models.IntegerField(default=0)
    current_count = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    week_start = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_goal_type_display()} ({self.current_count}/{self.target_count})"
    
    def is_completed(self):
        return self.current_count >= self.target_count
    
    def increment_count(self):
        """Increment the current count and check if goal is completed"""
        if self.target_count == self.current_count:
            self.current_count
        else:
            self.current_count += 1
            
        if self.current_count >= self.target_count:
            self.completed = True
        self.save()
        return self.completed
    
    def progress_percentage(self):
        """Get progress as percentage"""
        if self.target_count == 0:
            return 0
        return round((self.current_count / self.target_count) * 100, 1)
    
    @property
    def week_end(self):
        """Get the end date of the week"""
        return self.week_start + timedelta(days=6)
    
    @property
    def days_remaining(self):
        """Get days remaining in the week"""
        today = timezone.now().date()
        if today > self.week_end:
            return 0
        return (self.week_end - today).days + 1
    
    @classmethod
    def get_or_create_weekly_goal(cls, user):
        """Get or create this week's goal based on user's primary goal type"""
        from .utils import get_user_primary_goal_type  # Import here to avoid circular imports
        
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Check if goal already exists for this week
        existing_goal = cls.objects.filter(user=user, week_start=week_start).first()
        
        if existing_goal:
            return existing_goal, False
        
        # Determine user's primary goal type
        primary_goal_type = get_user_primary_goal_type(user)
        
        # Set target based on goal type
        target_count = 25 if primary_goal_type == 'scripture' else 10
        
        goal = cls.objects.create(
            user=user,
            goal_type=primary_goal_type,
            week_start=week_start,
            target_count=target_count
        )
        
        return goal, True
    
    @classmethod
    def update_goal_for_preference_change(cls, user):
        """Update current week's goal when user changes their faith preferences"""
        from .utils import get_user_primary_goal_type
        
        today = timezone.now().date() 
        week_start = today - timedelta(days=today.weekday())
        
        current_goal = cls.objects.filter(user=user, week_start=week_start).first()
        
        if current_goal:
            new_goal_type = get_user_primary_goal_type(user)
            
            if current_goal.goal_type != new_goal_type:
                current_goal.goal_type = new_goal_type
                current_goal.current_count = 0
                current_goal.completed = False
                current_goal.target_count = 25 if new_goal_type == 'scripture' else 10
                current_goal.save()
                
                return current_goal, True
        
        return current_goal, False
        
    @classmethod
    def get_current_week_goals(cls, user):
        """Get goals for current week (kept for backward compatibility)"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        return cls.objects.filter(user=user, week_start=week_start)
    
    @classmethod
    def get_goal_history(cls, user, goal_type=None):
        """Get user's goal history"""
        queryset = cls.objects.filter(user=user).order_by('-week_start')
        if goal_type:
            queryset = queryset.filter(goal_type=goal_type)
        return queryset
    
    class Meta:
        unique_together = ('user', 'goal_type', 'week_start')
        ordering = ['-week_start', 'goal_type']

class ChapterRead(models.Model):
    """Track which chapters user has read"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chapters_read')
    bible_id = models.CharField(max_length=50)
    chapter_id = models.CharField(max_length=100)
    read_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.bible_id}:{self.chapter_id}"
    
    class Meta:
        unique_together = ('user', 'bible_id', 'chapter_id')
        ordering = ['-read_at']

class ConversationInteraction(models.Model):
    """Track user interactions (thumbs up)"""
    INTERACTION_TYPES = [
        ('thumbs_up', 'Thumbs Up'),
        ('thumbs_down', 'Thumbs Down'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_interactions')
    content_type = models.CharField(max_length=50)  # 'chapter', 'verse', etc.
    content_id = models.CharField(max_length=100)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES, default='thumbs_up')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} on {self.content_type}:{self.content_id}"
    
    class Meta:
        ordering = ['-created_at']

class ShareActivity(models.Model):
    """Track when user shares content"""
    SHARE_PLATFORMS = [
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_activities')
    content_type = models.CharField(max_length=50)  # 'chapter', 'verse', etc.
    content_id = models.CharField(max_length=100)
    share_platform = models.CharField(max_length=50, choices=SHARE_PLATFORMS, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - shared {self.content_type}:{self.content_id} on {self.share_platform}"
    
    class Meta:
        ordering = ['-shared_at']