from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Notification, FCMToken, UserNotificationPreference
from .serializers import *
from .services.notification_service import NotificationService
import logging
from apps.core.utils.mixins import BaseResponseMixin

logger = logging.getLogger(__name__)

from rest_framework.response import Response

class NotificationViewSet(BaseResponseMixin, viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return self.success_response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return self.success_response({'updated_count': updated})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return self.success_response({'notification_id': notification.id})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        deleted_count = self.get_queryset().count()
        self.get_queryset().delete()
        return self.success_response({'deleted_count': deleted_count})



class FCMTokenViewSet(BaseResponseMixin, viewsets.ModelViewSet):
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FCMToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Deactivate old tokens for this device type
        FCMToken.objects.filter(
            user=self.request.user,
            device_type=serializer.validated_data['device_type']
        ).update(is_active=False)
        
        serializer.save(user=self.request.user, is_active=True)
    
    @action(detail=True, methods=['post'])
    def refresh_token(self, request, pk=None):
        """POST /api/fcm-tokens/{id}/refresh_token/"""
        token_obj = self.get_object()
        new_token = request.data.get('token')
        if new_token:
            token_obj.token = new_token
            token_obj.save()
            return self.success_response({'status': 'success'})
        return self.error_response({'error': 'Token required'}, status_code=400)

class SendNotificationView(BaseResponseMixin, APIView):
    """POST /api/notifications/send/ - Admin/System use"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            for user_id in data['user_ids']:
                try:
                    NotificationService.send_notification(
                        user_id=user_id,
                        title=data['title'],
                        message=data['message'],
                        notification_types=data['notification_types'],
                        data=data.get('data', {})
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
                    continue
            
            return self.success_response(
                message=f'Notifications sent to {len(data["user_ids"])} users'
            )
        
        return self.error_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class NotificationPreferencesView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        return self.success_response(serializer.data)

    def put(self, request):
        """PUT /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(serializer.data)
        return self.error_response(serializer.errors, status_code=400)