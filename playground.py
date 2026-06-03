from apps.notification.services.notification_service import NotificationService
from apps.accounts.models import User
user = User.objects.first()
NotificationService.send_notification(
    user_id=user.id,
    title="Hello World!",
    message="Your notification system is working!",
    notification_types=['in_app', 'email']
)

print("Test notification sent!")