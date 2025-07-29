from celery import shared_task
from firebase_admin import messaging
from django.utils import timezone
from apps.accounts.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

# Initialize Firebase (do this once)
from django.conf import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

@shared_task(bind=True, max_retries=3)
def send_push_notification(self, notification_id):
    try:
        from .models import Notification, FCMToken
        
        notification = Notification.objects.get(id=notification_id)
        tokens = FCMToken.objects.filter(
            user=notification.user, 
            is_active=True
        ).values_list('token', flat=True)
        
        if not tokens:
            logger.warning(f"No active FCM tokens for user {notification.user.id}")
            return
        
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message,
            ),
            data={str(k): str(v) for k, v in notification.data.items()},  # FCM needs strings
            tokens=list(tokens),
        )
        
        # FIXED: Use send_each_for_multicast instead of send_multicast
        response = messaging.send_each_for_multicast(message)
        
        # Handle failed tokens
        _handle_failed_tokens(response, tokens, notification.user)
        
        # Mark as sent
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Push notification sent to {len(tokens)} tokens, {response.failure_count} failures")
        
    except Exception as exc:
        logger.error(f"Push notification error: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def send_websocket_notification(notification_id):
    try:
        from .models import Notification
        from .serializers import NotificationSerializer
        
        notification = Notification.objects.get(id=notification_id)
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.user.id}",
            {
                "type": "notification_message",
                "notification": NotificationSerializer(notification).data
            }
        )
        
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"WebSocket notification sent to user {notification.user.id}")
        
    except Exception as e:
        logger.error(f"WebSocket notification error: {e}")

@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    try:
        from django.core.mail import send_mail
        from .models import Notification
        
        notification = Notification.objects.get(id=notification_id)
        
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email='noreply@yourdomain.com',
            recipient_list=[notification.user.email],
            fail_silently=False,
        )
        
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Email sent to {notification.user.email}")
        
    except Exception as exc:
        logger.error(f"Email notification error: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def _handle_failed_tokens(response, tokens, user):
    """Remove invalid FCM tokens"""
    from .models import FCMToken
    
    if response.failure_count > 0:
        failed_tokens = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                failed_tokens.append(tokens[idx])
                logger.warning(f"FCM token failed: {resp.exception}")
        
        # Deactivate failed tokens
        FCMToken.objects.filter(
            user=user,
            token__in=failed_tokens
        ).update(is_active=False)