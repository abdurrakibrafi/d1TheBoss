from rest_framework import serializers
from .models import Notification, FCMToken, UserNotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'data', 'sent_at', 'created_at']
        read_only_fields = ['id', 'sent_at', 'created_at']

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']
    
    def validate_device_type(self, value):
        if value not in ['ios', 'android']:
            raise serializers.ValidationError("Device type must be 'ios' or 'android'")
        return value

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = ['push_enabled', 'email_enabled', 'sms_enabled']

class SendNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['push', 'in_app', 'email', 'sms']),
        default=['push', 'in_app']
    )
    data = serializers.JSONField(required=False, default=dict)
