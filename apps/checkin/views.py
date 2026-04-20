from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from apps.checkin.models import (
    DailyCheckin,
    UserStreak,
    UserBadge,
    WeeklyCheckinQuestion,
    WeeklyCheckinOption,
    UserWeeklyCheckin,
    UserWeeklyCheckinResponse,
    BadgeTemplate,
    UserAppBadge,
    get_current_week_boundaries,
)
from apps.checkin.serializers import (
    BadgeTemplateSerializer,
    DailyCheckinSerializer,
    UserAppBadgeSerializer,
    UserStreakSerializer,
    UserBadgeSerializer,
    WeeklyCheckinQuestionSerializer,
    WeeklyCheckinResponseSerializer,
)
from apps.core.utils.mixins import BaseResponseMixin
from apps.notification.services.notification_service import NotificationService
from apps.goal.models import UserGoal, ConversationInteraction, ShareActivity, ChapterRead
from apps.checkin.tasks import check_and_award_badges_task


# ─── Streak Notification Helper ──────────────────────────────────────────────────

import logging
logger = logging.getLogger(__name__)

class StreakNotificationService:

    @staticmethod
    def get_streak_notification_data(current_streak, milestone_reached=False):
        if milestone_reached:
            return {
                "title": "🎉 Weekly Check-In Complete!",
                "message": "You've completed another week of reflection! Keep growing."
            }
        if current_streak <= 7:
            return {"title": "🔥 Keep Your Streak Burning!", "message": f"Day {current_streak} strong — keep it going!"}
        elif current_streak <= 14:
            return {"title": "💪 Momentum Building!", "message": f"Day {current_streak} and you're unstoppable!"}
        elif current_streak <= 30:
            return {"title": "🚀 On Fire!", "message": f"{current_streak} days of dedication!"}
        else:
            return {"title": "🏆 Legendary Streak!", "message": f"Day {current_streak}! Extraordinary commitment."}

    @staticmethod
    def send_streak_notification(user, current_streak, is_milestone=False):
        notification_data = StreakNotificationService.get_streak_notification_data(
            current_streak, is_milestone
        )
        try:
            logger.info(f"📱 Sending streak notification to user {user.id} — streak: {current_streak}, milestone: {is_milestone}")
            
            NotificationService.send_notification(
                user_id=user.id,
                title=notification_data["title"],
                message=notification_data["message"],
                notification_types=['push', 'in_app'],
                data={
                    "action": "streak_update",
                    "current_streak": current_streak,
                    "is_milestone": is_milestone
                }
            )
            
            logger.info(f"✅ Streak notification sent to user {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Streak notification failed for user {user.id}: {str(e)}")


# ─── Daily Check-In ──────────────────────────────────────────────────────────────

class DailyCheckinAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.now().date()

        if DailyCheckin.objects.filter(user=user, checkin_date=today).exists():
            user_streak, _ = UserStreak.objects.get_or_create(user=user)
            return self.success_response({
                'message': 'Already checked in today',
                'current_streak': user_streak.current_streak,
                'longest_streak': user_streak.longest_streak,
                'current_weekly_streak': user_streak.current_weekly_streak,
                'has_red_flame': user_streak.has_red_flame,
            }, status=status.HTTP_200_OK)

        user_streak, _ = UserStreak.objects.get_or_create(user=user)

        if user_streak.is_streak_broken():
            user_streak.current_streak = 0

        user_streak.current_streak += 1
        user_streak.last_checkin_date = today

        if user_streak.current_streak > user_streak.longest_streak:
            user_streak.longest_streak = user_streak.current_streak

        user_streak.save()

        DailyCheckin.objects.create(
            user=user,
            checkin_date=today,
            streak_day=user_streak.current_streak
        )

        notification_days = [3, 7, 14, 21, 30, 45, 60, 90]
        if user_streak.current_streak in notification_days:
            StreakNotificationService.send_streak_notification(user, user_streak.current_streak)

        self._ensure_current_week_exists(user)

        return self.success_response({
            'message': 'Check-in successful',
            'current_streak': user_streak.current_streak,
            'longest_streak': user_streak.longest_streak,
            'current_weekly_streak': user_streak.current_weekly_streak,
            'has_red_flame': user_streak.has_red_flame,
        }, status=status.HTTP_201_CREATED)

    def _ensure_current_week_exists(self, user):
        week_start, week_end = get_current_week_boundaries()

        # Fix null dates first
        UserWeeklyCheckin.objects.filter(
            user=user, week_start__isnull=True
        ).update(week_start=week_start, week_end=week_end)

        # Guard by week_start — main duplicate prevention
        if UserWeeklyCheckin.objects.filter(user=user, week_start=week_start).exists():
            return

        # Also check if any available week exists
        if UserWeeklyCheckin.objects.filter(user=user, status='available').exists():
            return

        existing_count = UserWeeklyCheckin.objects.filter(user=user).count()
        UserWeeklyCheckin.objects.create(
            user=user,
            week_number=existing_count + 1,
            week_start=week_start,
            week_end=week_end,
            status='available',
            is_available=True,
            is_completed=False,
        )


# ─── Calendar ────────────────────────────────────────────────────────────────────

class CalendarDataAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            month = request.GET.get('month')
            year = request.GET.get('year')
            user = request.user

            user_streak, _ = UserStreak.objects.get_or_create(
                user=user,
                defaults={'current_streak': 0, 'longest_streak': 0}
            )

            checkins = DailyCheckin.objects.filter(user=user)
            weekly_checkins = UserWeeklyCheckin.objects.filter(user=user, status='completed')

            if month and year:
                try:
                    month = int(month)
                    year = int(year)
                    checkins = checkins.filter(checkin_date__month=month, checkin_date__year=year)
                    weekly_checkins = weekly_checkins.filter(completed_at__month=month, completed_at__year=year)
                except (ValueError, TypeError):
                    pass

            checkin_data = DailyCheckinSerializer(checkins, many=True).data

            weekly_checkin_data = []
            for wc in weekly_checkins:
                try:
                    completion_date = wc.completed_at.date() if wc.completed_at else timezone.now().date()
                    weekly_checkin_data.append({
                        'id': wc.id,
                        'week_number': wc.week_number,
                        'week_start': wc.week_start,
                        'week_end': wc.week_end,
                        'completed_at': wc.completed_at,
                        'completion_date': completion_date,
                    })
                except Exception:
                    continue

            calendar_events = []
            for checkin in checkin_data:
                calendar_events.append({
                    'date': checkin['checkin_date'],
                    'type': 'daily_checkin',
                    'streak_day': checkin.get('streak_day', 0),
                })
            for wc in weekly_checkin_data:
                calendar_events.append({
                    'date': wc['completion_date'].strftime('%Y-%m-%d'),
                    'type': 'weekly_checkin_completion',
                    'weekly_checkin_id': wc['id'],
                    'week_number': wc['week_number'],
                    'completed_at': wc['completed_at'].isoformat() if wc['completed_at'] else None,
                })

            calendar_events.sort(key=lambda x: x['date'], reverse=True)

            return self.success_response({
                'calendar_events': calendar_events,
                'summary': {
                    'total_daily_checkins': len(checkin_data),
                    'total_weekly_checkins_completed': len(weekly_checkin_data),
                    'current_streak': user_streak.current_streak,
                    'longest_streak': user_streak.longest_streak,
                    'current_weekly_streak': user_streak.current_weekly_streak,
                    'has_red_flame': user_streak.has_red_flame,
                },
                'has_data': len(calendar_events) > 0
            })

        except Exception as exc:
            return self.handle_exception(exc)


# ─── Profile Dashboard ───────────────────────────────────────────────────────────

class ProfileDashboardAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_streak, _ = UserStreak.objects.get_or_create(
            user=user,
            defaults={'current_streak': 0, 'longest_streak': 0}
        )
        streak_data = UserStreakSerializer(user_streak).data

        badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
        latest_badge = badges.first()
        badge_data = UserAppBadgeSerializer(badges, many=True, context={'request': request}).data

        all_weekly = UserWeeklyCheckin.objects.filter(user=user)
        total_completed = all_weekly.filter(status='completed').count()
        total_missed = all_weekly.filter(status='missed').count()

        week_start, week_end = get_current_week_boundaries()
        current_week = all_weekly.filter(week_start=week_start).first()

        next_badge_template = (
            BadgeTemplate.objects
            .filter(weeks_required__gt=total_completed)
            .order_by('weeks_required')
            .first()
        )
        next_badge_progress = None
        if next_badge_template:
            next_badge_progress = {
                'badge_type': next_badge_template.badge_type,
                'title': next_badge_template.title,
                'weeks_required': next_badge_template.weeks_required,
                'weeks_completed': total_completed,
                'weeks_remaining': next_badge_template.weeks_required - total_completed,
            }

        return self.success_response({
            'streak': streak_data,
            'current_streak': user_streak.current_streak,
            'longest_streak': user_streak.longest_streak,
            # Weekly streak / red flame
            'current_weekly_streak': user_streak.current_weekly_streak,
            'longest_weekly_streak': user_streak.longest_weekly_streak,
            'has_red_flame': user_streak.has_red_flame,
            # Badges
            'latest_badge': UserAppBadgeSerializer(latest_badge, context={'request': request}).data if latest_badge else None,
            'badges': badge_data,
            'total_badges_earned': badges.count(),
            'next_badge_progress': next_badge_progress,
            # Weekly checkin
            'total_completed_weekly_checkins': total_completed,
            'total_missed_weekly_checkins': total_missed,
            'current_week_status': current_week.status if current_week else 'no_record',
            'current_week_available': current_week.status == 'available' if current_week else False,
        })


# ─── Weekly Check-In Questions ───────────────────────────────────────────────────

class WeeklyCheckinQuestionsAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        week_start, week_end = get_current_week_boundaries()

        current_week = UserWeeklyCheckin.objects.filter(
            user=user, week_start=week_start
        ).first()

        if not current_week:
            existing_count = UserWeeklyCheckin.objects.filter(user=user).count()
            current_week = UserWeeklyCheckin.objects.create(
                user=user,
                week_number=existing_count + 1,
                week_start=week_start,
                week_end=week_end,
                status='available',
                is_available=True,
                is_completed=False,
            )

        if current_week.status != 'available':
            return self.success_response({
                'available': False,
                'status': current_week.status,
                'message': 'No weekly check-in available right now.' if current_week.status == 'missed'
                           else 'Already completed this week.'
            }, status=status.HTTP_200_OK)

        questions = WeeklyCheckinQuestion.objects.filter(is_active=True)
        serializer = WeeklyCheckinQuestionSerializer(questions, many=True)

        return self.success_response({
            'available': True,
            'weekly_checkin_id': current_week.id,
            'week_number': current_week.week_number,
            'week_start': current_week.week_start,
            'week_end': current_week.week_end,
            'questions': serializer.data
        })


# ─── Weekly Check-In Submit ──────────────────────────────────────────────────────

class WeeklyCheckinSubmitAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        weekly_checkin_id = request.data.get('weekly_checkin_id')
        responses = request.data.get('responses', [])

        try:
            weekly_checkin = UserWeeklyCheckin.objects.get(
                id=weekly_checkin_id,
                user=user,
                status='available'
            )
        except UserWeeklyCheckin.DoesNotExist:
            return self.error_response({
                'error': 'Weekly check-in not available or already completed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Already has responses — just mark complete
        existing_responses = UserWeeklyCheckinResponse.objects.filter(weekly_checkin=weekly_checkin)
        if existing_responses.exists():
            weekly_checkin.status = 'completed'
            weekly_checkin.is_completed = True
            weekly_checkin.completed_at = timezone.now()
            weekly_checkin.save()
            return self.success_response({
                'message': 'Weekly check-in already completed',
                'week_number': weekly_checkin.week_number
            }, status=status.HTTP_200_OK)

        if len(responses) != 10:
            return self.error_response({
                'error': 'All 10 questions must be answered'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            for response_data in responses:
                UserWeeklyCheckinResponse.objects.create(
                    weekly_checkin=weekly_checkin,
                    question_id=response_data['question'],
                    selected_option_id=response_data['selected_option']
                )

            # Mark completed
            weekly_checkin.status = 'completed'
            weekly_checkin.is_completed = True
            weekly_checkin.completed_at = timezone.now()
            weekly_checkin.save()
            weekly_checkin.refresh_from_db()

            # Update weekly streak
            from apps.checkin.tasks import _update_weekly_streak
            updated_streak = _update_weekly_streak(user)

            # Award badges synchronously — get newly awarded list
            newly_awarded = check_and_award_badges_task(user.id)
            if not isinstance(newly_awarded, list):
                newly_awarded = []

            # Get the most recently awarded badge for popup
            newly_earned_badge = None
            if newly_awarded:
                latest = newly_awarded[-1]  # Last one awarded this submission
                newly_earned_badge = latest

            # Send notification
            try:
                StreakNotificationService.send_streak_notification(
                    user,
                    user.streak.current_streak if hasattr(user, 'streak') else 0,
                    is_milestone=True
                )
            except Exception:
                pass

            return self.success_response({
                'message': 'Weekly check-in completed successfully!',
                'week_number': weekly_checkin.week_number,
                # Weekly streak info
                'current_weekly_streak': updated_streak.current_weekly_streak if updated_streak else 0,
                'has_red_flame': updated_streak.has_red_flame if updated_streak else False,
                # Badge popup — frontend shows this as popup if not None
                'newly_earned_badge': newly_earned_badge,
                # All newly awarded badges this submission
                'newly_awarded_badges': newly_awarded,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return self.error_response({
                'error': f'Failed to save responses: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Weekly Check-In History ─────────────────────────────────────────────────────

class WeeklyCheckinHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, week_number=None):
        user = request.user

        if week_number:
            try:
                weekly_checkin = UserWeeklyCheckin.objects.get(user=user, week_number=week_number)

                responses = UserWeeklyCheckinResponse.objects.filter(
                    weekly_checkin=weekly_checkin
                ).select_related('question', 'selected_option').order_by('question__question_order')

                questions_and_answers = []
                for response in responses:
                    all_options = WeeklyCheckinOption.objects.filter(
                        question=response.question
                    ).order_by('option_order')

                    options_data = [{
                        "option_id": opt.id,
                        "option_text": opt.option_text,
                        "option_order": opt.option_order,
                        "is_selected": opt.id == response.selected_option.id
                    } for opt in all_options]

                    questions_and_answers.append({
                        "question_id": response.question.id,
                        "question_text": response.question.question_text,
                        "question_order": response.question.question_order,
                        "selected_answer": {
                            "option_id": response.selected_option.id,
                            "option_text": response.selected_option.option_text,
                        },
                        "all_options": options_data,
                        "answered_at": response.created_at
                    })

                return Response({
                    "success": True,
                    "data": {
                        "weekly_checkin": {
                            "id": weekly_checkin.id,
                            "week_number": weekly_checkin.week_number,
                            "week_start": weekly_checkin.week_start,
                            "week_end": weekly_checkin.week_end,
                            "status": weekly_checkin.status,
                            "completed_at": weekly_checkin.completed_at,
                        },
                        "questions_and_answers": questions_and_answers,
                    }
                })

            except UserWeeklyCheckin.DoesNotExist:
                return Response({"success": False, "message": f"Week {week_number} not found"}, status=404)

        else:
            all_weeks = UserWeeklyCheckin.objects.filter(user=user).order_by('week_number')

            total_completed = all_weeks.filter(status='completed').count()
            total_missed = all_weeks.filter(status='missed').count()
            total_available = all_weeks.filter(status='available').count()

            # Get badge earned per week for history display
            earned_badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
            badge_by_week = {}
            for badge in earned_badges:
                if badge.badge_template and badge.badge_template.weeks_required:
                    req = badge.badge_template.weeks_required
                    badge_by_week[req] = {
                        'badge_type': badge.badge_template.badge_type,
                        'title': badge.badge_template.title,
                        'earned_at': badge.earned_at.isoformat(),
                    }

            weeks_data = []
            completed_so_far = 0
            for wc in all_weeks:
                week_entry = {
                    "weekly_checkin_id": wc.id,
                    "week_number": wc.week_number,
                    "week_start": wc.week_start,
                    "week_end": wc.week_end,
                    "status": wc.status,
                    "completed_at": wc.completed_at,
                    "total_responses": UserWeeklyCheckinResponse.objects.filter(weekly_checkin=wc).count(),
                    "badge_earned": None,
                }
                # Check if a badge was earned at this week's completion count
                if wc.status == 'completed':
                    completed_so_far += 1
                    if completed_so_far in badge_by_week:
                        week_entry['badge_earned'] = badge_by_week[completed_so_far]

                weeks_data.append(week_entry)

            # Streak calculation
            current_streak = 0
            longest_streak = 0
            temp_streak = 0
            for wc in all_weeks.order_by('week_number'):
                if wc.status == 'completed':
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 0
            for wc in all_weeks.order_by('-week_number'):
                if wc.status == 'completed':
                    current_streak += 1
                elif wc.status == 'missed':
                    break

            return Response({
                "success": True,
                "data": {
                    "weeks": weeks_data,
                    "total_completed": total_completed,
                    "total_missed": total_missed,
                    "total_available": total_available,
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "message": f"You have completed {total_completed} week(s)."
                }
            })


# ─── Badge Views ──────────────────────────────────────────────────────────────────

class PopulateBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Upsert badge templates with correct client-spec names.
        Safe to re-run — images never touched.
        Uses new badge_type keys matching BADGE_MILESTONES.
        """
        badge_data = [
            {
                'badge_type': 'default',
                'title': 'Called to Begin',
                'description': "You've answered the call to grow. This is where your journey starts. Complete your first Weekly Reflection now.",
                'order': 1,
                'weeks_required': 0,
            },
            {
                'badge_type': 'week_1',
                'title': 'Seed Planted',
                'description': "You showed up. That's where growth begins. Keep planting what matters.",
                'order': 2,
                'weeks_required': 1,
            },
            {
                'badge_type': 'week_2',
                'title': 'Rooted in Grace',
                'description': "Your roots are taking hold. Stay grounded, what you've started is growing. 7 days of showing up. Keep going.",
                'order': 3,
                'weeks_required': 2,
            },
            {
                'badge_type': 'week_3',
                'title': 'New Life Rising',
                'description': "Growth is breaking through. Your consistency is bringing it to life.",
                'order': 4,
                'weeks_required': 3,
            },
            {
                'badge_type': 'week_4',
                'title': 'Standing in the Light',
                'description': "You're growing stronger. Rooted in truth. Reaching toward the light.",
                'order': 5,
                'weeks_required': 4,
            },
            {
                'badge_type': 'week_12',
                'title': 'Branches of Influence',
                'description': "Your growth is reaching outward. What you build now begins to touch others. Stay faithful.",
                'order': 6,
                'weeks_required': 12,
            },
            {
                'badge_type': 'week_24',
                'title': 'Flourishing in Faith',
                'description': "Your faith is steady. Your roots are deep. Your life is bearing strength. Keep walking forward.",
                'order': 7,
                'weeks_required': 24,
            },
            {
                'badge_type': 'week_52',
                'title': 'Fruit of a Faithful Life',
                'description': "Your life reflects wisdom. Your words carry weight. You're living what you believe. Proverbs 25:11",
                'order': 8,
                'weeks_required': 52,
            },
        ]

        created_count = 0
        updated_count = 0

        for data in badge_data:
            badge_type = data.pop('badge_type')
            _, created = BadgeTemplate.objects.update_or_create(
                badge_type=badge_type,
                defaults=data,  # image NOT in here — never touched
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        return self.success_response({
            'message': f'Badges processed — {created_count} created, {updated_count} updated. Images untouched.',
            'total_badges': BadgeTemplate.objects.count(),
        }, status=status.HTTP_200_OK)


class UserAppBadgesListAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
        latest_badge = user_badges.first() if user_badges.exists() else None

        return self.success_response({
            'latest_badge': UserAppBadgeSerializer(latest_badge, context={'request': request}).data if latest_badge else None,
            'badges': UserAppBadgeSerializer(user_badges, many=True, context={'request': request}).data,
            'total_earned': user_badges.count()
        }, status=status.HTTP_200_OK)


class CheckAndAwardBadgesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = check_and_award_badges_task(request.user.id)
        return self.success_response({
            'message': 'Badge check complete',
            'newly_awarded': result if isinstance(result, list) else []
        }, status=status.HTTP_200_OK)


class AllBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = BadgeTemplate.objects.all()
        return self.success_response({
            'badge_templates': BadgeTemplateSerializer(templates, many=True, context={'request': request}).data
        }, status=status.HTTP_200_OK)