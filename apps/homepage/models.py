from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.onboarding.models import BibleVersionOption

class DailyVerse(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='daily_verses',
        blank=True, null=True

    )
    verse_id = models.CharField(max_length=250, blank=True, null=True)
    verse_text = models.TextField(blank=True, null=True)
    verse_reference = models.CharField(max_length=250, blank=True, null=True)
    bible_version = models.ForeignKey(
        BibleVersionOption, 
        on_delete=models.CASCADE,
        blank=True, 
        null=True
    )
    date_assigned = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'date_assigned']
        verbose_name_plural = "Daily Verses"

    def __str__(self):
        user_email = self.user.email if self.user else "Unknown User"
        return f"{user_email} - {self.verse_reference}"
    


class JourneyVerse(models.Model):
    day_number = models.PositiveIntegerField(unique=True) # ১ থেকে ৯০
    title = models.CharField(max_length=255)
    verse_text = models.TextField()
    verse_reference = models.CharField(max_length=100)

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"