from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.onboarding.models import FaithGoal
from apps.goal.models import UserGoal

@receiver([post_save, post_delete], sender=FaithGoal)
def update_user_weekly_goal(sender, instance, **kwargs):
    # When a FaithGoal is deleted as part of a User cascade, accessing
    # `instance.user` can raise User.DoesNotExist because the user may
    # already have been deleted. Use the raw FK id to safely check if
    # the user still exists and only then call the update helper.
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
        # Be defensive: don't let signal failures break bulk deletes
        return