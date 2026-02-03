# models.py (with optional improvements)
from django.db import models
from apps.accounts.models import User
import uuid

class ReadingProgress(models.Model):
    """Track user's current reading position"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bible_version_id = models.CharField(max_length=50)  # API.Bible ID
    current_book_id = models.CharField(max_length=50, blank=True)
    current_chapter_id = models.CharField(max_length=50, blank=True)
    current_verse_number = models.IntegerField(default=1)
    
    # Audio state
    audio_position = models.FloatField(default=0.0)  # in seconds
    is_audio_mode = models.BooleanField(default=False)
    
    # Optional: Add reading streak tracking
    last_read_date = models.DateField(auto_now=True)
    consecutive_days = models.IntegerField(default=0)
    
    # Optional: Add reading speed tracking
    reading_speed_wpm = models.IntegerField(default=200)  # words per minute
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s progress"

    class Meta:
        verbose_name = "Reading Progress"
        verbose_name_plural = "Reading Progress"

class Bookmark(models.Model):
    """User bookmarks for verses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bible_version_id = models.CharField(max_length=50)
    book_id = models.CharField(max_length=50)
    chapter_id = models.CharField(max_length=50)
    verse_id = models.CharField(max_length=50)
    verse_content = models.TextField()
    note = models.TextField(blank=True)
    
    # Optional: Add categories/tags
    tags = models.CharField(max_length=200, blank=True)  # comma-separated
    
    # Optional: Add color coding
    COLOR_CHOICES = [
        ('yellow', 'Yellow'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('purple', 'Purple'),
    ]
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='yellow')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'verse_id']
        ordering = ['-created_at']
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"

    def __str__(self):
        return f"{self.user.username}'s bookmark: {self.verse_id}"

class SearchHistory(models.Model):
    """Track user search queries"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=500)
    bible_version_id = models.CharField(max_length=50)
    
    # Optional: Add result count
    result_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Search History"
        verbose_name_plural = "Search History"

    def __str__(self):
        return f"{self.user.username} searched: {self.query}"

# Optional: Add Reading Plan model for future features
class ReadingPlan(models.Model):
    """User's reading plans"""
    PLAN_TYPES = [
        ('daily', 'Daily Reading'),
        ('weekly', 'Weekly Reading'),
        ('monthly', 'Monthly Reading'),
        ('custom', 'Custom Plan'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    bible_version_id = models.CharField(max_length=50)
    
    # Schedule
    target_chapters_per_day = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Progress
    is_active = models.BooleanField(default=True)
    completion_percentage = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s plan: {self.name}"

# Optional: Add User Notes model
class UserNote(models.Model):
    """User personal notes on chapters/verses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bible_version_id = models.CharField(max_length=50)
    
    # Can be attached to book, chapter, or verse
    book_id = models.CharField(max_length=50, blank=True)
    chapter_id = models.CharField(max_length=50, blank=True)
    verse_id = models.CharField(max_length=50, blank=True)
    
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Optional: Add note type
    NOTE_TYPES = [
        ('reflection', 'Reflection'),
        ('prayer', 'Prayer'),
        ('question', 'Question'),
        ('insight', 'Insight'),
        ('application', 'Application'),
    ]
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='reflection')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s note: {self.title or 'Untitled'}"