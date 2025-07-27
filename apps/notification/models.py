from django.db import models
from django.utils import timezone
from apps.accounts.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('email', 'Email Notification'),
        ('sms', 'SMS Notification'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.notification_type})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = timezone.now()
        self.save()

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Preferences"
    
    class Meta:
        verbose_name_plural = "User Notification Preferences"

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # e.g. 'android', 'ios'
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.token}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'token')