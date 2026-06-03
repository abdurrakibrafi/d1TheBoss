from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    if not created:
        return
    
    try:
        from apps.checkin.models import (
            UserWeeklyCheckin, 
            get_current_week_boundaries,
            BadgeTemplate,
            UserAppBadge
        )
        week_start, week_end = get_current_week_boundaries()
        UserWeeklyCheckin.objects.get_or_create(
            user=instance,
            week_number=1,
            defaults={
                'week_start': week_start,
                'week_end': week_end,
                'status': 'available',
                'is_available': True,
                'is_completed': False,
            }
        )
        try:
            default_template = BadgeTemplate.objects.get(badge_type='default')
            UserAppBadge.objects.get_or_create(
                user=instance,
                badge_template=default_template
            )
            print(f"Default badge awarded to {instance.email}")
        except BadgeTemplate.DoesNotExist:
            print("Default badge template not found")
            
    except Exception as e:
        print(f"Error in user creation signal: {e}")