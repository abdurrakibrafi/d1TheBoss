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
    DailyCheckinSerializer,
    UserStreakSerializer,
    UserBadgeSerializer,
    WeeklyCheckinQuestionSerializer,
    WeeklyCheckinResponseSerializer,
)
from apps.core.utils.mixins import BaseResponseMixin
from apps.notification.services.notification_service import NotificationService
from apps.goal.models import UserGoal, ConversationInteraction, ShareActivity, ChapterRead
from apps.checkin.tasks import check_and_award_badges_task


# ─── Streak Notification Helper ─────────────────────────────────────────────────

class StreakNotificationService:

    @staticmethod
    def get_streak_notification_data(current_streak, milestone_reached=False):
        if milestone_reached:
            return {
                "title": "🎉 Weekly Check-In Complete!",
                "message": f"You've completed another week of reflection! Keep growing."
            }
        if current_streak <= 7:
            return {
                "title": "🔥 Keep Your Streak Burning!",
                "message": f"Day {current_streak} strong — keep it going!"
            }
        elif current_streak <= 14:
            return {
                "title": "💪 Momentum Building!",
                "message": f"Day {current_streak} and you're unstoppable!"
            }
        elif current_streak <= 30:
            return {
                "title": "🚀 On Fire!",
                "message": f"{current_streak} days of dedication!"
            }
        else:
            return {
                "title": "🏆 Legendary Streak!",
                "message": f"Day {current_streak}! Extraordinary commitment."
            }

    @staticmethod
    def send_streak_notification(user, current_streak, is_milestone=False):
        notification_data = StreakNotificationService.get_streak_notification_data(
            current_streak, is_milestone
        )
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


# ─── Daily Check-In ─────────────────────────────────────────────────────────────

class DailyCheckinAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Auto check-in when user opens app"""
        user = request.user
        today = timezone.now().date()

        # Already checked in today?
        if DailyCheckin.objects.filter(user=user, checkin_date=today).exists():
            return self.success_response({
                'message': 'Already checked in today',
                'streak': user.streak.current_streak if hasattr(user, 'streak') else 0,
                'longest_streak': user.streak.longest_streak if hasattr(user, 'streak') else 0,
                'checkins': DailyCheckinSerializer(
                    DailyCheckin.objects.filter(user=user), many=True
                ).data
            }, status=status.HTTP_200_OK)

        # Get or create streak
        user_streak, _ = UserStreak.objects.get_or_create(user=user)

        # Reset streak if broken
        if user_streak.is_streak_broken():
            user_streak.current_streak = 0

        # Increment
        user_streak.current_streak += 1
        user_streak.last_checkin_date = today

        if user_streak.current_streak > user_streak.longest_streak:
            user_streak.longest_streak = user_streak.current_streak

        user_streak.save()

        # Create daily checkin record
        DailyCheckin.objects.create(
            user=user,
            checkin_date=today,
            streak_day=user_streak.current_streak
        )

        # Streak milestone notifications
        notification_days = [3, 7, 14, 21, 30, 45, 60, 90]
        if user_streak.current_streak in notification_days:
            StreakNotificationService.send_streak_notification(
                user, user_streak.current_streak, is_milestone=False
            )

        # Ensure this week's check-in record exists (in case Celery missed it)
        self._ensure_current_week_exists(user)

        return self.success_response({
            'message': 'Check-in successful',
            'current_streak': user_streak.current_streak,
            'longest_streak': user_streak.longest_streak,
            'checkins': DailyCheckinSerializer(
                DailyCheckin.objects.filter(user=user), many=True
            ).data
        }, status=status.HTTP_201_CREATED)

    def _ensure_current_week_exists(self, user):
        """
        Safety net: if no UserWeeklyCheckin exists for current week, create one.
        This handles edge cases where Celery task hasn't run yet.
        """
        week_start, week_end = get_current_week_boundaries()

        existing = UserWeeklyCheckin.objects.filter(
            user=user,
            week_start=week_start
        ).first()

        if not existing:
            existing_count = UserWeeklyCheckin.objects.filter(user=user).count()
            week_number = existing_count + 1

            UserWeeklyCheckin.objects.create(
                user=user,
                week_number=week_number,
                week_start=week_start,
                week_end=week_end,
                status='available',
                is_available=True,
                is_completed=False,
            )


# ─── Calendar ───────────────────────────────────────────────────────────────────

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
            goals = UserGoal.objects.filter(user=user)
            weekly_checkins = UserWeeklyCheckin.objects.filter(user=user, status='completed')

            if month and year:
                try:
                    month = int(month)
                    year = int(year)
                    checkins = checkins.filter(
                        checkin_date__month=month,
                        checkin_date__year=year
                    )
                    weekly_checkins = weekly_checkins.filter(
                        completed_at__month=month,
                        completed_at__year=year
                    )
                except (ValueError, TypeError):
                    pass

            checkin_data = DailyCheckinSerializer(checkins, many=True).data

            # Process weekly check-in completions
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
                        'total_responses': UserWeeklyCheckinResponse.objects.filter(
                            weekly_checkin=wc
                        ).count()
                    })
                except Exception as e:
                    continue

            # Build calendar events
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

            summary_stats = {
                'total_daily_checkins': len(checkin_data),
                'total_weekly_checkins_completed': len(weekly_checkin_data),
                'current_streak': user_streak.current_streak,
                'longest_streak': user_streak.longest_streak,
            }

            return self.success_response({
                'calendar_events': calendar_events,
                'summary': summary_stats,
                'has_data': len(calendar_events) > 0
            })

        except Exception as exc:
            return self.handle_exception(exc)


# ─── Profile Dashboard ───────────────────────────────────────────────────────────

class ProfileDashboardAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        streak_data = {}
        if hasattr(user, 'streak'):
            streak_data = UserStreakSerializer(user.streak).data

        badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
        from apps.checkin.serializers import UserAppBadgeSerializer
        badge_data = UserAppBadgeSerializer(badges, many=True).data

        # Total completed weeks (for badge progress display)
        total_completed = UserWeeklyCheckin.objects.filter(
            user=user, status='completed'
        ).count()

        # Current week checkin
        week_start, week_end = get_current_week_boundaries()
        current_week = UserWeeklyCheckin.objects.filter(
            user=user, week_start=week_start
        ).first()

        # Streak info
        current_streak = 0
        longest_streak = 0
        if hasattr(user, 'streak'):
            current_streak = user.streak.current_streak
            longest_streak = user.streak.longest_streak

        return self.success_response({
            'streak': streak_data,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'badges': badge_data,
            'total_completed_weekly_checkins': total_completed,
            'current_week_status': current_week.status if current_week else 'no_record',
            'current_week_available': current_week.status == 'available' if current_week else False,
        })


# ─── Weekly Check-In Questions ───────────────────────────────────────────────────

class WeeklyCheckinQuestionsAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        week_start, week_end = get_current_week_boundaries()

        # Get this week's checkin record
        current_week = UserWeeklyCheckin.objects.filter(
            user=user,
            week_start=week_start
        ).first()

        if not current_week:
            # Safety net: create it
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

        # If already has responses, just mark complete
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

            # Mark as completed
            weekly_checkin.status = 'completed'
            weekly_checkin.is_completed = True
            weekly_checkin.completed_at = timezone.now()
            weekly_checkin.save()

            # Fire badge check task asynchronously
            check_and_award_badges_task.delay(user.id)

            # Send milestone notification
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
                'week_number': weekly_checkin.week_number
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
                weekly_checkin = UserWeeklyCheckin.objects.get(
                    user=user, week_number=week_number
                )

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
                return Response({
                    "success": False,
                    "message": f"Week {week_number} not found"
                }, status=404)

        else:
            # List ALL weeks since user joined (including missed)
            all_weeks = UserWeeklyCheckin.objects.filter(user=user).order_by('week_number')

            total_completed = all_weeks.filter(status='completed').count()
            total_missed = all_weeks.filter(status='missed').count()
            total_available = all_weeks.filter(status='available').count()

            weeks_data = [{
                "weekly_checkin_id": wc.id,
                "week_number": wc.week_number,
                "week_start": wc.week_start,
                "week_end": wc.week_end,
                "status": wc.status,
                "completed_at": wc.completed_at,
                "total_responses": UserWeeklyCheckinResponse.objects.filter(
                    weekly_checkin=wc
                ).count()
            } for wc in all_weeks]

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
            # Current streak = consecutive completed from most recent
            for wc in all_weeks.order_by('-week_number'):
                if wc.status == 'completed':
                    current_streak += 1
                elif wc.status == 'missed':
                    break
                # skip 'available' (current open week)

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


# ─── Badge Views ─────────────────────────────────────────────────────────────────

 
class PopulateBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        # ✅ Matched by badge_type — safe to re-run, images never touched
        badge_data = [
            {
                'badge_type': 'default',
                'title': 'Called to Begin',
                'description': "You've answered the call to grow. This is where your journey starts. Complete your Weekly Check-in now.",
                'order': 1,
                'weeks_required': 0,
            },
            {
                'badge_type': 'first_week_checked',
                'title': 'The Seed of Faith',
                'description': "You showed up, and that's where growth begins. Keep planting what matters.",
                'order': 2,
                'weeks_required': 1,
            },
            {
                'badge_type': 'first_week',
                'title': 'Rooted in Grace',
                'description': "Your roots are taking hold. Stay grounded, what you've started is growing. 7 days of showing up. Keep growing.",
                'order': 3,
                'weeks_required': 2,
            },
            {
                'badge_type': 'two_week',
                'title': 'The Sprout',
                'description': "New growth is breaking through. Your consistency is bringing it to life.",
                'order': 4,
                'weeks_required': 3,
            },
            {
                'badge_type': 'one_month',
                'title': 'Reaching Toward the Light',
                'description': "You're leaning into truth and growing stronger with every step.",
                'order': 5,
                'weeks_required': 4,
            },
            {
                'badge_type': 'three_months',
                'title': 'Branches of Influence',
                'description': "Your growth is starting to reach others. What you build now matters.",
                'order': 6,
                'weeks_required': 8,
            },
            {
                'badge_type': 'six_months',
                'title': 'Flourishing Faith',
                'description': "Your faith is steady, growing, and alive. Keep walking in what you've built.",
                'order': 7,
                'weeks_required': 12,
            },
            {
                'badge_type': 'one_year',
                'title': 'A Life of Overflowing Abundance',
                'description': "Your words carry wisdom and grace. You're living what you believe. Proverbs 25:11",
                'order': 8,
                'weeks_required': 24,
            },
        ]
 
        created_count = 0
        updated_count = 0
 
        for data in badge_data:
            badge_type = data.pop('badge_type')
            _, created = BadgeTemplate.objects.update_or_create(
                badge_type=badge_type,    # lookup key — stable, never changes
                defaults=data,            # image field not in here — stays untouched
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
 
        return self.success_response({
            'message': f'Badges processed — {created_count} created, {updated_count} updated. No data deleted.',
            'total_badges': BadgeTemplate.objects.count(),
        }, status=status.HTTP_200_OK)

class UserAppBadgesListAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.checkin.serializers import UserAppBadgeSerializer
        user = request.user
        user_badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
        latest_badge = user_badges.first() if user_badges.exists() else None

        return self.success_response({
            'latest_badge': UserAppBadgeSerializer(latest_badge).data if latest_badge else None,
            'badges': UserAppBadgeSerializer(user_badges, many=True).data,
            'total_earned': user_badges.count()
        }, status=status.HTTP_200_OK)


class CheckAndAwardBadgesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        check_and_award_badges_task.delay(request.user.id)
        return self.success_response({
            'message': 'Badge check triggered'
        }, status=status.HTTP_200_OK)


class AllBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.checkin.serializers import BadgeTemplateSerializer
        templates = BadgeTemplate.objects.all()
        return self.success_response({
            'badge_templates': BadgeTemplateSerializer(templates, many=True).data
        }, status=status.HTTP_200_OK)