from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def get_week_boundaries_for_date(d):
    """Get Sunday-Saturday week boundaries for a given date"""
    from datetime import timedelta
    days_since_sunday = (d.weekday() + 1) % 7
    week_start = d - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


@shared_task(name='checkin.create_weekly_checkins_for_all_users')
def create_weekly_checkins_for_all_users():
    """
    Runs every Sunday at 00:01 UTC.
    Creates a new UserWeeklyCheckin for every user for the new week.
    Also marks previous week as missed if not completed.
    """
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
            # Mark last week as missed if not completed
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

            # Calculate this user's week number
            existing_weeks = UserWeeklyCheckin.objects.filter(user=user).count()
            next_week_num = existing_weeks + 1

            # Create new week (avoid duplicates)
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


@shared_task(name='checkin.close_week_on_saturday')
def close_week_on_saturday():
    """
    Runs every Sunday at 00:00 UTC (just before create_weekly_checkins_for_all_users).
    Marks all still-available checkins from last week as missed.
    """
    from apps.checkin.models import UserWeeklyCheckin

    today = timezone.now().date()
    # Last week's boundaries
    last_week_end = today - timedelta(days=1)  # Yesterday = last Saturday
    last_week_start = last_week_end - timedelta(days=6)

    missed = UserWeeklyCheckin.objects.filter(
        week_start=last_week_start,
        status='available'
    ).update(
        status='missed',
        is_available=False
    )

    logger.info(f"Closed {missed} weekly checkins as missed")
    return f"Marked {missed} as missed"


@shared_task(name='checkin.check_and_award_badges')
def check_and_award_badges_task(user_id):
    """
    Award badges based on total completed weekly check-ins.
    Milestones: 1, 2, 3, 4, 8, 12, 24, 52 completed weeks.
    Badges NEVER reset.
    """
    from django.contrib.auth import get_user_model
    from apps.checkin.models import UserWeeklyCheckin, BadgeTemplate, UserAppBadge, BADGE_MILESTONES

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    # Count total completed weeks (not streak, TOTAL)
    total_completed = UserWeeklyCheckin.objects.filter(
        user=user,
        status='completed'
    ).count()

    # Badge type mapping by milestone index
    milestone_to_badge_type = {
        1: 'first_week_checked',
        2: 'first_week',
        3: 'two_week',
        4: 'one_month',
        8: 'three_months',
        12: 'six_months',
        24: 'one_year',
        52: 'one_year',  # Reuse one_year for 52 if no separate badge
    }

    newly_awarded = []

    for milestone in BADGE_MILESTONES:
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
                    newly_awarded.append(badge_type)
                    logger.info(f"Awarded badge '{badge_type}' to user {user.id}")
            except BadgeTemplate.DoesNotExist:
                logger.warning(f"BadgeTemplate '{badge_type}' not found")
                continue

    return f"Awarded: {newly_awarded}"


@shared_task(name='checkin.create_week1_for_new_user')
def create_week1_for_new_user(user_id):
    """
    Called immediately when a new user registers.
    Creates Week 1 so user can check in right away — no waiting.
    """
    from django.contrib.auth import get_user_model
    from apps.checkin.models import UserWeeklyCheckin
    from apps.checkin.models import get_current_week_boundaries

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