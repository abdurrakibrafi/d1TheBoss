from django.db import models
from apps.accounts.models import User
from apps.onboarding.models import JourneyReason, Denomination, FaithGoal, TonePreference, BibleFamiliarity, BibleVersion
import uuid

class ChatSession(models.Model):
    """
    Represents a chat session between a user and the AI.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    journey_reason = models.ForeignKey(JourneyReason, on_delete=models.CASCADE, blank=True, null=True)
    denomination = models.ForeignKey(Denomination, on_delete=models.CASCADE, blank=True, null=True)
    faith_goal = models.ForeignKey(FaithGoal, on_delete=models.CASCADE, blank=True, null=True)
    tone_preference = models.ForeignKey(TonePreference, on_delete=models.CASCADE, blank=True, null=True)
    bible_familiarity = models.ForeignKey(BibleFamiliarity, on_delete=models.CASCADE, blank=True, null=True)
    bible_version = models.ForeignKey(BibleVersion, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    context_snapshot = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)

    message_count = models.PositiveIntegerField(default=0)
    tokens_used = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            user_email = self.user.email or f"User #{self.user.pk}"
        else:
            user_email = "Anonymous"
        return f"ChatSession {self.pk} - User: {user_email}"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True, null=True)
    is_user = models.BooleanField()
    bookmark = models.BooleanField(default=False)

    
    # AI metadata
    model_used = models.CharField(max_length=100, blank=True, null=True)
    tokens_consumed = models.PositiveIntegerField(default=0)
    response_time = models.FloatField(default=0.0)
    ai_metadata = models.JSONField(blank=True, null=True)

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        content = self.content or "(No content)"
        return f"{'User' if self.is_user else 'AI'}: {content[:50]}..."