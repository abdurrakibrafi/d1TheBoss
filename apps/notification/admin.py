from django.contrib import admin
from .models import Notification, UserNotificationPreference, FCMToken

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'push_enabled', 'email_enabled', 'sms_enabled')
    search_fields = ('user__email',)
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__email', 'token')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')
