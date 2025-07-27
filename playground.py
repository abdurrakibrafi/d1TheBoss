# Run this inside Django shell: python manage.py shell
from apps.notification.services.notification_service import NotificationService
from apps.accounts.models import User

# Get a user (replace with your user ID)
user = User.objects.first()

# Send test notification
NotificationService.send_notification(
    user_id=user.id,
    title="Hello World!",
    message="Your notification system is working!",
    notification_types=['in_app', 'email']
)

print("Test notification sent!")