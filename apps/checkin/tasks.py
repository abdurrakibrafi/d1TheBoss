from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def get_week_boundaries_for_date(d):
    from datetime import timedelta
    days_since_sunday = (d.weekday() + 1) % 7
    week_start = d - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


@shared_task(name='checkin.create_weekly_checkins_for_all_users')
def create_weekly_checkins_for_all_users():
    """Every Sunday 00:01 UTC — creates new week, marks last week missed."""
    from django.contrib.auth import get_user_model
    from apps.checkin.models import UserWeeklyCheckin

    User = get_user_model()
    today = timezone.now().date()
    week_start, week_end = get_week_boundaries_for_date(today)

    users = User.objects.filter(is_active=True)
    created_count = 0
    missed_count = 0

    for user in users:
        try:
            # Mark last week missed if still available
            last_week_start = week_start - timedelta(days=7)
            last_week_checkin = UserWeeklyCheckin.objects.filter(
                user=user,
                week_start=last_week_start,
                status='available'
            ).first()

            if last_week_checkin:
                last_week_checkin.status = 'missed'
                last_week_checkin.is_available = False
                last_week_checkin.save()
                missed_count += 1

                # Reset weekly streak since week was missed
                _reset_weekly_streak(user)

            # Create new week
            existing_weeks = UserWeeklyCheckin.objects.filter(user=user).count()
            next_week_num = existing_weeks + 1

            checkin, created = UserWeeklyCheckin.objects.get_or_create(
                user=user,
                week_start=week_start,
                defaults={
                    'week_number': next_week_num,
                    'week_end': week_end,
                    'status': 'available',
                    'is_available': True,
                    'is_completed': False,
                }
            )

            if created:
                created_count += 1

        except Exception as e:
            logger.error(f"Error creating weekly checkin for user {user.id}: {str(e)}")
            continue

    logger.info(f"Weekly checkin task: {created_count} created, {missed_count} marked missed")
    return f"Created: {created_count}, Missed: {missed_count}"


def _reset_weekly_streak(user):
    """Reset weekly streak when user misses a week."""
    try:
        from apps.checkin.models import UserStreak
        streak, _ = UserStreak.objects.get_or_create(user=user)
        streak.current_weekly_streak = 0
        streak.has_red_flame = False
        streak.save()
    except Exception as e:
        logger.error(f"Error resetting weekly streak for user {user.id}: {str(e)}")


def _update_weekly_streak(user):
    """
    Increment weekly streak after check-in completion.
    Red flame appears when current_weekly_streak >= 2.
    """
    try:
        from apps.checkin.models import UserStreak
        streak, _ = UserStreak.objects.get_or_create(user=user)
        streak.current_weekly_streak += 1
        if streak.current_weekly_streak > streak.longest_weekly_streak:
            streak.longest_weekly_streak = streak.current_weekly_streak
        # Red flame = 2 or more consecutive completed weeks
        streak.has_red_flame = streak.current_weekly_streak >= 2
        streak.save()
        return streak
    except Exception as e:
        logger.error(f"Error updating weekly streak for user {user.id}: {str(e)}")
        return None


@shared_task(name='checkin.close_week_on_saturday')
def close_week_on_saturday():
    """Every Sunday 00:00 UTC — mark last week missed."""
    from apps.checkin.models import UserWeeklyCheckin

    today = timezone.now().date()
    last_week_end = today - timedelta(days=1)
    last_week_start = last_week_end - timedelta(days=6)

    missed = UserWeeklyCheckin.objects.filter(
        week_start=last_week_start,
        status='available'
    ).update(status='missed', is_available=False)

    logger.info(f"Closed {missed} weekly checkins as missed")
    return f"Marked {missed} as missed"


@shared_task(name='checkin.check_and_award_badges')
def check_and_award_badges_task(user_id):
    """
    Award badges based on TOTAL completed weekly check-ins.
    Milestones: 1, 2, 3, 4, 12, 24, 52
    Badges NEVER reset. NEVER awarded early.
    User needs EXACTLY that many completed weeks.
    """
    from django.contrib.auth import get_user_model
    from apps.checkin.models import UserWeeklyCheckin, BadgeTemplate, UserAppBadge, BADGE_MILESTONES

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return "User not found"

    # Count TOTAL completed weeks — not streak, not consecutive
    total_completed = UserWeeklyCheckin.objects.filter(
        user=user,
        status='completed'
    ).count()

    logger.info(f"Badge check for user {user.id}: {total_completed} completed weeks")

    # Correct badge type mapping per client doc
    milestone_to_badge_type = {
        1:  'week_1',   # Seed Planted
        2:  'week_2',   # Rooted in Grace
        3:  'week_3',   # New Life Rising
        4:  'week_4',   # Standing in the Light
        12: 'week_12',  # Branches of Influence
        24: 'week_24',  # Flourishing in Faith
        52: 'week_52',  # Fruit of a Faithful Life
    }

    newly_awarded = []

    for milestone in BADGE_MILESTONES:
        # Only award if user has reached this milestone
        if total_completed >= milestone:
            badge_type = milestone_to_badge_type.get(milestone)
            if not badge_type:
                continue

            try:
                template = BadgeTemplate.objects.get(badge_type=badge_type)
                badge, created = UserAppBadge.objects.get_or_create(
                    user=user,
                    badge_template=template
                )
                if created:
                    newly_awarded.append({
                        'badge_type': badge_type,
                        'title': template.title,
                        'description': template.description,
                        'image': template.image.url if template.image else None,
                        'weeks_required': template.weeks_required,
                    })
                    logger.info(f"Awarded badge '{badge_type}' to user {user.id}")
            except BadgeTemplate.DoesNotExist:
                logger.warning(f"BadgeTemplate '{badge_type}' not found — run /badges/populate/ first")
                continue

    return newly_awarded  # Return list so WeeklyCheckinSubmitAPIView can use it


@shared_task(name='checkin.create_week1_for_new_user')
def create_week1_for_new_user(user_id):
    """Called on new user register — creates Week 1 immediately."""
    from django.contrib.auth import get_user_model
    from apps.checkin.models import UserWeeklyCheckin, get_current_week_boundaries

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    week_start, week_end = get_current_week_boundaries()

    checkin, created = UserWeeklyCheckin.objects.get_or_create(
        user=user,
        week_number=1,
        defaults={
            'week_start': week_start,
            'week_end': week_end,
            'status': 'available',
            'is_available': True,
            'is_completed': False,
        }
    )

    logger.info(f"Week 1 {'created' if created else 'already exists'} for user {user.id}")
    return f"Week 1 {'created' if created else 'already exists'}"