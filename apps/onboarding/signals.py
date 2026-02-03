from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.onboarding.models import FaithGoal
from apps.goal.models import UserGoal

@receiver([post_save, post_delete], sender=FaithGoal)
def update_user_weekly_goal(sender, instance, **kwargs):
    
    if instance.user:
        UserGoal.update_goal_for_preference_change(instance.user)