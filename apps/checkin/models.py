from django.db import models
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta, date


def get_current_week_boundaries():
    """Get current Sunday-Saturday week boundaries"""
    today = timezone.now().date()
    # Sunday = weekday 6 in Python (Mon=0, Sun=6)
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)  # This Sunday
    week_end = week_start + timedelta(days=6)               # This Saturday
    return week_start, week_end


def get_week_boundaries_for_date(d):
    """Get Sunday-Saturday week boundaries for a given date"""
    days_since_sunday = (d.weekday() + 1) % 7
    week_start = d - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_streak_broken(self):
        """Check if more than 1 day passed since last checkin"""
        if not self.last_checkin_date:
            return False
        return timezone.now().date() > self.last_checkin_date + timedelta(days=1)

    def __str__(self):
        return f"{self.user.email} - streak: {self.current_streak}"


class DailyCheckin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_checkins')
    checkin_date = models.DateField(blank=True, null=True)
    streak_day = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'checkin_date')
        ordering = ['-checkin_date']

    def __str__(self):
        return f"{self.user.email} - {self.checkin_date}"


class WeeklyCheckinQuestion(models.Model):
    question_text = models.TextField(blank=True, null=True)
    question_order = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_order']

    def __str__(self):
        return f"Q{self.question_order}: {self.question_text[:50] if self.question_text else ''}"


class WeeklyCheckinOption(models.Model):
    question = models.ForeignKey(WeeklyCheckinQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255, blank=True, null=True)
    option_order = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['option_order']
        unique_together = ('question', 'option_order')

    def __str__(self):
        return f"{self.option_text}"


class UserWeeklyCheckin(models.Model):
    """
    One record per user per calendar week (Sunday-Saturday).
    Created automatically by Celery task every Sunday.
    Week 1 is created immediately on user join.
    """
    STATUS_CHOICES = [
        ('available', 'Available'),    # Current week, not yet completed
        ('completed', 'Completed'),    # User completed this week's check-in
        ('missed', 'Missed'),          # Week passed without completing
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_checkins', blank=True, null=True)
    week_number = models.IntegerField(blank=True, null=True)          # Sequential: 1, 2, 3...
    week_start = models.DateField(blank=True, null=True)              # Sunday of that week
    week_end = models.DateField(blank=True, null=True)                # Saturday of that week
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    # Legacy fields kept for backward compat
    is_available = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'week_number')
        ordering = ['week_number']

    def __str__(self):
        return f"{self.user.email} - Week {self.week_number} ({self.status})"

    def save(self, *args, **kwargs):
        # Keep legacy fields in sync with status
        self.is_completed = (self.status == 'completed')
        self.is_available = (self.status == 'available')
        super().save(*args, **kwargs)

    @property
    def is_current_week(self):
        today = timezone.now().date()
        return self.week_start <= today <= self.week_end

    def can_complete(self):
        """User can complete if status is available and it's still this week or a current open week"""
        return self.status == 'available'


class UserWeeklyCheckinResponse(models.Model):
    weekly_checkin = models.ForeignKey(UserWeeklyCheckin, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(WeeklyCheckinQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(WeeklyCheckinOption, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('weekly_checkin', 'question')

    def __str__(self):
        return f"Week {self.weekly_checkin.week_number} - Q{self.question.question_order}"


# ─── Badge System ───────────────────────────────────────────────────────────────

BADGE_MILESTONES = [1, 2, 3, 4, 8, 12, 24, 52]  # Total completed weeks


class BadgeTemplate(models.Model):
    BADGE_TYPE = [
        ('default', 'Default'),
        ('first_week_checked', 'First Week Checked'),
        ('first_week', 'First Week'),
        ('two_week', 'Two Week'),
        ('one_month', 'One Month'),
        ('three_months', 'Three Months'),
        ('six_months', 'Six Months'),
        ('one_year', 'One Year'),
    ]

    badge_type = models.CharField(max_length=100, choices=BADGE_TYPE, unique=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='checkin/badges/', blank=True, null=True)
    order = models.IntegerField(default=0)
    weeks_required = models.IntegerField(null=True, blank=True)  # Based on completed weeks not days

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title or self.badge_type


class UserAppBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_badges', blank=True, null=True)
    badge_template = models.ForeignKey(BadgeTemplate, on_delete=models.CASCADE, blank=True, null=True)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge_template')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.email} - {self.badge_template.title if self.badge_template else 'Unknown'}"


# Keep UserBadge for backward compat
class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges', blank=True, null=True)
    weeks_completed = models.IntegerField(blank=True, null=True)
    badge_name = models.CharField(max_length=50, blank=True, null=True)
    earned_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'weeks_completed')
        ordering = ['-weeks_completed']

    @classmethod
    def get_badge_milestones(cls):
        return BADGE_MILESTONES