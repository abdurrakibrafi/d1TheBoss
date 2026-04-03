from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
 
User = get_user_model()
 
 
@receiver(post_save, sender=User)
def create_week1_on_user_register(sender, instance, created, **kwargs):
    """When a new user is created, immediately create Week 1 for them."""
    if created:
        from apps.checkin.tasks import create_week1_for_new_user
        # Delay slightly to ensure user is fully committed to DB
        create_week1_for_new_user.apply_async(args=[instance.id], countdown=2)