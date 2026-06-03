from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.onboarding.models import FaithGoal
from apps.goal.models import UserGoal

@receiver([post_save, post_delete], sender=FaithGoal)
def update_user_weekly_goal(sender, instance, **kwargs):
    user_id = getattr(instance, 'user_id', None)
    if not user_id:
        return

    try:
        from apps.accounts.models import User
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return
        UserGoal.update_goal_for_preference_change(user)
    except Exception:
        return