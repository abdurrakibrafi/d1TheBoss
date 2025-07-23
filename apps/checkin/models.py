from django.db import models
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta

class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_streak_broken(self):
        """Check if 24+ hours passed since last checkin"""
        if not self.last_checkin_date:
            return False
        return timezone.now().date() > self.last_checkin_date + timedelta(days=1)
    
class DailyCheckin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_checkins')
    checkin_date = models.DateField(blank=True, null=True)
    streak_day = models.IntegerField(blank=True, null=True)  # Day number of current streak
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'checkin_date')
        ordering = ['-checkin_date']

class UserGoal(models.Model):
    GOAL_TYPES = [
        ('memorize_scripture', 'Memorize Scripture'),
        ('share_faith', 'Share Faith'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_count = models.IntegerField(blank=True, null=True)
    current_count = models.IntegerField(default=0)
    date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'goal_type', 'date')

class WeeklyCheckinQuestion(models.Model):
    question_text = models.TextField(blank=True, null=True)
    question_order = models.IntegerField(blank=True, null=True)  # 1-10
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['question_order']

class WeeklyCheckinOption(models.Model):
    question = models.ForeignKey(WeeklyCheckinQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255, blank=True, null=True)
    option_order = models.IntegerField(blank=True, null=True)  # 1-5
    
    class Meta:
        ordering = ['option_order']
        unique_together = ('question', 'option_order')


class UserWeeklyCheckin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_checkins')
    week_number = models.IntegerField(blank=True, null=True)  # Week since user joined app
    is_available = models.BooleanField(default=False)  # Available after 7 consecutive days
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def can_start_checkin(self):
        """User must have 7 consecutive days to start weekly checkin"""
        return self.user.streak.current_streak >= 7 and self.is_available
    
class UserWeeklyCheckinResponse(models.Model):
    weekly_checkin = models.ForeignKey(UserWeeklyCheckin, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(WeeklyCheckinQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(WeeklyCheckinOption, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('weekly_checkin', 'question')

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    weeks_completed = models.IntegerField(blank=True, null=True)  # 1, 2, 4, 8, 12, 16, 20, 24...
    badge_name = models.CharField(max_length=50, blank=True, null=True)  # "1 Week", "2 Weeks", "4 Weeks"...
    earned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'weeks_completed')
        ordering = ['-weeks_completed']
    
    @classmethod
    def get_badge_milestones(cls):
        """Define badge milestones - can be extended infinitely"""
        milestones = [1, 2, 4, 8, 12]
        # Add more milestones dynamically (every 4 weeks after 12)
        current = 16
        while current <= 100:  # Up to 100 weeks (can extend more)
            milestones.append(current)
            current += 4
        return milestones