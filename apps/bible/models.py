from django.db import models

# Create your models here.
from django.db import models
from apps.accounts.models import User
from django.utils import timezone
import uuid


class BibleVersionCache(models.Model):
    """Cache Bible versions from API.Bible"""
    api_bible_id = models.CharField(max_length=50, unique=True)  # From API.Bible
    name = models.CharField(max_length=200)  # "Revised Standard Version Catholic Edition"
    abbreviation = models.CharField(max_length=10)  # "RSVCE"
    description = models.TextField(blank=True)
    language_code = models.CharField(max_length=10)  # "en", "es", etc.
    is_audio_available = models.BooleanField(default=False)
    audio_bible_id = models.CharField(max_length=50, blank=True)  # Separate ID for audio
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
        
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Book(models.Model):
    """Cache Bible books from API.Bible"""
    api_bible_id = models.CharField(max_length=50)  # From API.Bible
    bible_version_cache = models.ForeignKey(BibleVersionCache, on_delete=models.CASCADE, related_name='books')
    name = models.CharField(max_length=100)  # "Genesis"
    abbreviation = models.CharField(max_length=10)  # "GEN"
    order = models.IntegerField()  # Order in Bible (1 for Genesis, 2 for Exodus)
    testament = models.CharField(max_length=3, choices=[('OLD', 'Old Testament'), ('NEW', 'New Testament')])
    chapter_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['bible_version_cache', 'api_bible_id']
        
    def __str__(self):
        return f"{self.name} ({self.bible_version_cache.abbreviation})"


class Chapter(models.Model):
    """Cache Bible chapters from API.Bible"""
    api_bible_id = models.CharField(max_length=50)  # From API.Bible
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    number = models.IntegerField()  # Chapter number
    title = models.CharField(max_length=200, blank=True)  # Optional chapter title
    verse_count = models.IntegerField(default=0)
    
    # Audio specific fields
    audio_url = models.URLField(blank=True)  # Audio file URL from API.Bible
    audio_duration = models.IntegerField(null=True, blank=True)  # Duration in seconds
    
    # Caching
    content_cached = models.BooleanField(default=False)
    cache_updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['number']
        unique_together = ['book', 'number']
        
    def __str__(self):
        return f"{self.book.name} {self.number}"


class Verse(models.Model):
    """Cache Bible verses from API.Bible - lightweight storage"""
    api_bible_id = models.CharField(max_length=50)  # From API.Bible
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='verses')
    number = models.IntegerField()  # Verse number
    content = models.TextField()  # Actual verse text
    
    # Audio timing for verse-by-verse playback
    audio_start_time = models.FloatField(null=True, blank=True)  # Start time in seconds
    audio_end_time = models.FloatField(null=True, blank=True)  # End time in seconds
    
    class Meta:
        ordering = ['number']
        unique_together = ['chapter', 'number']
        
    def __str__(self):
        return f"{self.chapter.book.name} {self.chapter.number}:{self.number}"


class ReadingProgress(models.Model):
    """Track user's reading progress"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bible_version_cache = models.ForeignKey(BibleVersionCache, on_delete=models.CASCADE)
    current_book = models.ForeignKey(Book, on_delete=models.CASCADE)
    current_chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    current_verse = models.ForeignKey(Verse, on_delete=models.CASCADE, null=True, blank=True)
    
    # Audio progress
    audio_position = models.FloatField(default=0.0)  # Current position in seconds
    is_audio_mode = models.BooleanField(default=False)
    
    # Reading stats
    reading_time_today = models.IntegerField(default=0)  # Minutes
    reading_streak = models.IntegerField(default=0)  # Days
    last_read_date = models.DateField(default=timezone.now)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'bible_version_cache']
        
    def __str__(self):
        return f"{self.user.username} - {self.current_book.name} {self.current_chapter.number}"


class Bookmark(models.Model):
    """User bookmarks for verses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#FFD700')  # Hex color code
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'verse']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.verse}"


class SearchHistory(models.Model):
    """Track user search queries for suggestions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=500)
    bible_version_cache = models.ForeignKey(BibleVersionCache, on_delete=models.CASCADE)
    result_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} searched: {self.query}"


class AudioSession(models.Model):
    """Track audio playback sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_listened = models.IntegerField(default=0)  # Seconds actually listened
    playback_speed = models.FloatField(default=1.0)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.chapter} session"


class PlaybackState(models.Model):
    """Current playback state for resuming"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True)
    current_verse = models.ForeignKey(Verse, on_delete=models.CASCADE, null=True, blank=True)
    position = models.FloatField(default=0.0)  # Current position in seconds
    is_playing = models.BooleanField(default=False)
    playback_speed = models.FloatField(default=1.0)
    volume = models.FloatField(default=1.0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s playback state"


class APICache(models.Model):
    """Cache API responses to reduce external calls"""
    cache_key = models.CharField(max_length=255, unique=True)  # Generated key
    endpoint = models.CharField(max_length=200)  # API endpoint called
    response_data = models.JSONField()  # Cached response
    expires_at = models.DateTimeField()  # When cache expires
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def is_expired(self):
        return timezone.now() > self.expires_at
        
    def __str__(self):
        return f"Cache: {self.cache_key}"


# Additional models for advanced features (Phase 2)
class ReadingPlan(models.Model):
    """Reading plans (daily, weekly, yearly)"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_days = models.IntegerField()  # How many days to complete
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class UserReadingPlan(models.Model):
    """User's participation in reading plans"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reading_plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    current_day = models.IntegerField(default=1)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'reading_plan']
        
    def __str__(self):
        return f"{self.user.username} - {self.reading_plan.name}"