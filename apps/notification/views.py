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

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """GET /api/notifications/unread_count/"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """POST /api/notifications/mark_all_read/"""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'success', 'updated_count': updated})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """POST /api/notifications/{id}/mark_read/"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """DELETE /api/notifications/clear_all/"""
        deleted_count = self.get_queryset().count()
        self.get_queryset().delete()
        return Response({'status': 'success', 'deleted_count': deleted_count})

class FCMTokenViewSet(viewsets.ModelViewSet):
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
            return Response({'status': 'success'})
        return Response({'error': 'Token required'}, status=400)

class SendNotificationView(APIView):
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
                    continue  # Log error but continue with other users
            
            return Response({
                'status': 'success',
                'message': f'Notifications sent to {len(data["user_ids"])} users'
            })
        
        return Response(serializer.errors, status=400)

class NotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        return Response(serializer.data)
    
    def put(self, request):
        """PUT /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)