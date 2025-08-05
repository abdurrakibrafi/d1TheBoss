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
    )
from apps.checkin.serializers import (
    DailyCheckinSerializer,
    UserStreakSerializer,
    UserBadgeSerializer,
    WeeklyCheckinQuestionSerializer,
    WeeklyCheckinOptionSerializer,
    WeeklyCheckinResponseSerializer,
    )
from apps.core.utils.mixins import BaseResponseMixin
from apps.notification.services.notification_service import NotificationService
from apps.goal.models import UserGoal, ConversationInteraction, ShareActivity, ChapterRead

class StreakNotificationService:
    
    @staticmethod
    def get_streak_notification_data(current_streak, milestone_reached=False):
        """Get notification data based on streak patterns"""
        
        if milestone_reached:
            # Milestone notifications (weekly achievements)
            milestone_messages = [
                {
                    "title": "🎉 Celebrate the Milestone!",
                    "message": f"You've hit {current_streak // 7} weekly check-ins in a row! Your consistency is building something powerful. Stay connected and see what's next!"
                },
                {
                    "title": "🔥 Incredible Achievement!",
                    "message": f"Week {current_streak // 7} completed! You're crushing your faith journey. Keep the momentum going!"
                },
                {
                    "title": "⭐ Amazing Progress!",
                    "message": f"You've maintained {current_streak} days of consistency! Your dedication is inspiring."
                }
            ]
            return milestone_messages[0]  # You can randomize this
        
        else:
            # Daily streak notifications with dynamic patterns
            if current_streak <= 7:
                # Early days - more encouraging
                return {
                    "title": "🔥 Keep Your Streak Burning!",
                    "message": f"Your faith journey is on fire! You're at {current_streak} days strong — keep it going! Check in today to grow deeper and stay on track."
                }
            elif current_streak <= 14:
                # Second week - building habit
                return {
                    "title": "💪 Momentum Building!",
                    "message": f"Day {current_streak} and you're unstoppable! Your consistency is creating lasting change. Don't break the chain!"
                }
            elif current_streak <= 30:
                # Month milestone approaching
                return {
                    "title": "🚀 On Fire!",
                    "message": f"{current_streak} days of dedication! You're building something incredible. Keep pushing forward!"
                }
            else:
                # Long-term streaks
                return {
                    "title": "🏆 Legendary Streak!",
                    "message": f"Day {current_streak}! Your commitment is extraordinary. You're an inspiration to others on this journey!"
                }

    @staticmethod
    def send_streak_notification(user, current_streak, is_milestone=False):
        """Send streak-based notification"""
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

class DailyCheckinAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Auto check-in when user opens app"""
        user = request.user
        today = timezone.now().date()
        
        # Check if already checked in today
        if DailyCheckin.objects.filter(user=user, checkin_date=today).exists():
            return self.success_response({
                'message': 'Already checked in today',
                'streak': user.streak.current_streak,
                'longest_streak': user.streak.longest_streak,
                'checkins': DailyCheckinSerializer(DailyCheckin.objects.filter(user=user), many=True).data
            }, status=status.HTTP_200_OK)
        
        # Get or create user streak
        user_streak, created = UserStreak.objects.get_or_create(user=user)
        
        # Check if streak is broken (24+ hours gap)
        if user_streak.is_streak_broken():
            user_streak.current_streak = 0
        
        # Increment streak
        user_streak.current_streak += 1
        user_streak.last_checkin_date = today
        
        # Update longest streak
        if user_streak.current_streak > user_streak.longest_streak:
            user_streak.longest_streak = user_streak.current_streak
        
        user_streak.save()
        
        # Create daily checkin record
        DailyCheckin.objects.create(
            user=user,
            checkin_date=today,
            streak_day=user_streak.current_streak
        )
        
        # **ADD THIS - Send streak notifications on specific days**
        notification_days = [3, 7, 14, 21, 30, 45, 60, 90]
        if user_streak.current_streak in notification_days:
            StreakNotificationService.send_streak_notification(
                user, user_streak.current_streak, is_milestone=False
            )
        
        # Check for badge milestones
        self._check_and_award_badges(user, user_streak.current_streak)
        
        # Check if weekly checkin should be available
        self._check_weekly_checkin_availability(user)
        
        return self.success_response({
            'message': 'Check-in successful',
            'current_streak': user_streak.current_streak,
            'longest_streak': user_streak.longest_streak,
            'checkins': DailyCheckinSerializer(DailyCheckin.objects.filter(user=user), many=True).data
        }, status=status.HTTP_201_CREATED)
    
    def _check_and_award_badges(self, user, current_streak):
        """Award badges for week milestones"""
        milestones = UserBadge.get_badge_milestones()
        weeks = current_streak // 7  # Convert days to weeks
        
        for milestone in milestones:
            if weeks >= milestone:
                badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    weeks_completed=milestone,
                    defaults={'badge_name': f'{milestone} Week{"s" if milestone > 1 else ""}'}
                )
                if created:
                    # Send badge notification
                    pass
        
    def _check_weekly_checkin_availability(self, user):
        current_streak = user.streak.current_streak
        
        # Every 7 days = new weekly check-in
        if current_streak > 0 and current_streak % 7 == 0:
            # Find next available week number
            existing_weeks = UserWeeklyCheckin.objects.filter(user=user).values_list('week_number', flat=True)
            next_week_num = max(existing_weeks) + 1 if existing_weeks else 1
        
            # Create weekly check-in for the next available week
            weekly_checkin, created = UserWeeklyCheckin.objects.get_or_create(
                user=user,
                week_number=next_week_num,
                defaults={'is_available': True, 'is_completed': False}
            )
                        
            if created:
                print(f"Created Week {next_week_num} checkin for user {user.id} at {current_streak} days streak")

class CalendarDataAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive calendar data with check-ins, goals, and weekly check-ins"""
        try:
            month = request.GET.get('month')
            year = request.GET.get('year')
            
            user = request.user
            
            # Safely get or create user streak to avoid errors
            user_streak, created = UserStreak.objects.get_or_create(
                user=user,
                defaults={
                    'current_streak': 0,
                    'longest_streak': 0
                }
            )
            
            # Base querysets - these will return empty QuerySets if no data exists
            checkins = DailyCheckin.objects.filter(user=user)
            goals = UserGoal.objects.filter(user=user)  # Don't filter by month/year here
            weekly_checkins = UserWeeklyCheckin.objects.filter(user=user, is_completed=True)
            
            # Filter checkins and weekly_checkins by month/year if provided
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
            
            # Serialize daily check-ins
            checkin_data = DailyCheckinSerializer(checkins, many=True).data
            
            # Process goal completions (filter by completion date, not week_start)
            completed_goals = []
            completed_goals_queryset = goals.filter(completed=True)
            
            for goal in completed_goals_queryset:
                completion_date = None
                
                try:
                    # Find completion date logic
                    if goal.goal_type == 'scripture':
                        last_chapter = ChapterRead.objects.filter(
                            user=user,
                            read_at__date__gte=goal.week_start,
                            read_at__date__lte=goal.week_end
                        ).order_by('-read_at').first()
                        if last_chapter:
                            completion_date = last_chapter.read_at.date()
                    
                    elif goal.goal_type == 'conversation':
                        last_interaction = ConversationInteraction.objects.filter(
                            user=user,
                            created_at__date__gte=goal.week_start,
                            created_at__date__lte=goal.week_end
                        ).order_by('-created_at').first()
                        if last_interaction:
                            completion_date = last_interaction.created_at.date()
                    
                    elif goal.goal_type == 'share_faith':
                        last_share = ShareActivity.objects.filter(
                            user=user,
                            shared_at__date__gte=goal.week_start,
                            shared_at__date__lte=goal.week_end
                        ).order_by('-shared_at').first()
                        if last_share:
                            completion_date = last_share.shared_at.date()
                    
                    if not completion_date:
                        completion_date = goal.week_end
                    
                    # NOW filter by month/year based on completion_date
                    if month and year:
                        if completion_date.month != month or completion_date.year != year:
                            continue  # Skip this goal if completion date doesn't match filter
                    
                    completed_goals.append({
                        'id': goal.id,
                        'goal_type': goal.goal_type,
                        'goal_display': goal.get_goal_type_display(),
                        'target_count': goal.target_count,
                        'current_count': goal.current_count,
                        'completion_date': completion_date,
                        'week_start': goal.week_start,
                        'week_end': goal.week_end,
                        'progress_percentage': goal.progress_percentage()
                    })
                
                except Exception as e:
                    print(f"Error processing goal {goal.id}: {str(e)}")
                    continue
            
            # Process weekly check-in completions
            weekly_checkin_data = []
            for weekly_checkin in weekly_checkins:
                try:
                    completion_date = weekly_checkin.completed_at.date() if weekly_checkin.completed_at else timezone.now().date()
                    
                    weekly_checkin_data.append({
                        'id': weekly_checkin.id,
                        'week_number': weekly_checkin.week_number,
                        'completed_at': weekly_checkin.completed_at,
                        'completion_date': completion_date,
                        'total_responses': UserWeeklyCheckinResponse.objects.filter(
                            weekly_checkin=weekly_checkin
                        ).count()
                    })
                except Exception as e:
                    print(f"Error processing weekly checkin {weekly_checkin.id}: {str(e)}")
                    continue
            
            # Create flat calendar events list
            calendar_events = []
            
            # Add daily check-ins
            for checkin in checkin_data:
                try:
                    calendar_events.append({
                        'date': checkin['checkin_date'],
                        'type': 'daily_checkin',
                        'streak_day': checkin.get('streak_day', 0),
                        'checkin_id': checkin.get('id'),
                        'created_at': checkin.get('created_at')
                    })
                except Exception as e:
                    print(f"Error processing checkin: {str(e)}")
                    continue
            
            # Add goal completions
            for goal in completed_goals:
                try:
                    calendar_events.append({
                        'date': goal['completion_date'].strftime('%Y-%m-%d'),
                        'type': 'goal_completion',
                        'goal_id': goal['id'],
                        'goal_type': goal['goal_type'],
                        'goal_display': goal['goal_display'],
                        'target_count': goal['target_count'],
                        'current_count': goal['current_count'],
                        'progress_percentage': goal['progress_percentage'],
                        'week_start': goal['week_start'],
                        'week_end': goal['week_end']
                    })
                except Exception as e:
                    print(f"Error processing goal completion: {str(e)}")
                    continue
            
            # Add weekly check-in completions
            for weekly_checkin in weekly_checkin_data:
                try:
                    calendar_events.append({
                        'date': weekly_checkin['completion_date'].strftime('%Y-%m-%d'),
                        'type': 'weekly_checkin_completion',
                        'weekly_checkin_id': weekly_checkin['id'],
                        'week_number': weekly_checkin['week_number'],
                        'completed_at': weekly_checkin['completed_at'],
                        'total_responses': weekly_checkin['total_responses']
                    })
                except Exception as e:
                    print(f"Error processing weekly checkin completion: {str(e)}")
                    continue
            
            # Sort by date (most recent first)
            calendar_events.sort(key=lambda x: x['date'], reverse=True)
            
            # Summary stats
            summary_stats = {
                'total_daily_checkins': len(checkin_data),
                'total_goals_completed': len(completed_goals),
                'total_weekly_checkins_completed': len(weekly_checkin_data),
                'current_streak': user_streak.current_streak,
                'longest_streak': user_streak.longest_streak,
                'filter_applied': {
                    'month': month,
                    'year': year,
                    'has_filter': bool(month and year)
                }
            }
            
            # Breakdown by type
            breakdown = {
                'daily_checkins': checkin_data,
                'completed_goals': completed_goals,
                'weekly_checkins_completed': weekly_checkin_data
            }
            
            # Message
            if len(calendar_events) == 0:
                message = "No activities found. Start your journey by checking in daily to build your streak!"
            else:
                message = f'Calendar data retrieved successfully. Found {len(calendar_events)} activities.'
            
            return self.success_response({
                'calendar_events': calendar_events,
                'breakdown': breakdown,
                'summary': summary_stats,
                'message': message,
                'has_data': len(calendar_events) > 0
            })
            
        except Exception as exc:
            return self.handle_exception(exc)
        

class ProfileDashboardAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get complete profile dashboard data"""
        user = request.user
        
        # Get streak data
        streak_data = {}
        if hasattr(user, 'streak'):
            streak_data = UserStreakSerializer(user.streak).data
        
        # Get badges
        badges = UserBadge.objects.filter(user=user)
        badge_data = UserBadgeSerializer(badges, many=True).data
        
        # Get weekly checkin status
        available_checkins = UserWeeklyCheckin.objects.filter(
            user=user, 
            is_available=True, 
            is_completed=False
        ).count()
        
        return self.success_response({
            'streak': streak_data,
            'badges': badge_data,
            'available_weekly_checkins': available_checkins,
            'total_weekly_checkins_completed': UserWeeklyCheckin.objects.filter(
                user=user, is_completed=True
            ).count()
        })


class WeeklyCheckinQuestionsAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get weekly checkin questions if available"""
        user = request.user
        
        # Check if user has available weekly checkin
        available_checkin = UserWeeklyCheckin.objects.filter(
            user=user,
            is_available=True,
            is_completed=False
        ).first()
        
        if not available_checkin:
            return self.success_response({
                'available': False,
                'message': 'No weekly check-in available. Complete 7 consecutive days.'
            }, status=status.HTTP_200_OK)
        
        # Get questions with options
        questions = WeeklyCheckinQuestion.objects.filter(is_active=True)
        serializer = WeeklyCheckinQuestionSerializer(questions, many=True)

        return self.success_response({
            'available': True,
            'weekly_checkin_id': available_checkin.id,
            'week_number': available_checkin.week_number,
            'questions': serializer.data
        })
    

class WeeklyCheckinSubmitAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Submit weekly checkin responses"""
        user = request.user
        weekly_checkin_id = request.data.get('weekly_checkin_id')
        responses = request.data.get('responses', [])  # [{'question': 1, 'selected_option': 2}, ...]
        
        try:
            weekly_checkin = UserWeeklyCheckin.objects.get(
                id=weekly_checkin_id,
                user=user,
                is_available=True,
                is_completed=False
            )
        except UserWeeklyCheckin.DoesNotExist:
            return self.error_response({
                'error': 'Weekly check-in not available'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if responses already exist
        existing_responses = UserWeeklyCheckinResponse.objects.filter(weekly_checkin=weekly_checkin)
        if existing_responses.exists():
            # Just mark as completed if responses exist but not marked complete
            weekly_checkin.is_completed = True
            weekly_checkin.completed_at = timezone.now()
            weekly_checkin.save()
            
            return self.success_response({
                'message': 'Weekly check-in already completed',
                'week_number': weekly_checkin.week_number
            }, status=status.HTTP_200_OK)
        
        # Validate all 10 questions answered
        if len(responses) != 10:
            return self.error_response({
                'error': 'All 10 questions must be answered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save responses
        try:
            for response_data in responses:
                UserWeeklyCheckinResponse.objects.create(
                    weekly_checkin=weekly_checkin,
                    question_id=response_data['question'],
                    selected_option_id=response_data['selected_option']
                )
            
            # Mark as completed
            weekly_checkin.is_completed = True
            weekly_checkin.completed_at = timezone.now()
            weekly_checkin.save()
            
            # **ADD THIS - Send milestone celebration notification**
            StreakNotificationService.send_streak_notification(
                user, user.streak.current_streak, is_milestone=True
            )
            
            return self.success_response({
                'message': 'Weekly check-in completed successfully',
                'week_number': weekly_checkin.week_number
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return self.error_response({
                'error': f'Failed to save responses: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       

class WeeklyCheckinHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, week_number=None):
        user = request.user
        
        if week_number:
            # Get specific weekly check-in details with questions and answers
            try:
                weekly_checkin = UserWeeklyCheckin.objects.get(
                    user=user, 
                    week_number=week_number
                )
                
                # Get all responses for this weekly check-in
                responses = UserWeeklyCheckinResponse.objects.filter(
                    weekly_checkin=weekly_checkin
                ).select_related('question', 'selected_option').order_by('question__question_order')
                
                # Build detailed response with questions and answers
                questions_and_answers = []
                for response in responses:
                    # Get all options for this question to show what was available
                    all_options = WeeklyCheckinOption.objects.filter(
                        question=response.question
                    ).order_by('option_order')
                    
                    options_data = []
                    for option in all_options:
                        options_data.append({
                            "option_id": option.id,
                            "option_text": option.option_text,
                            "option_order": option.option_order,
                            "is_selected": option.id == response.selected_option.id
                        })
                    
                    questions_and_answers.append({
                        "question_id": response.question.id,
                        "question_text": response.question.question_text,
                        "question_order": response.question.question_order,
                        "selected_answer": {
                            "option_id": response.selected_option.id,
                            "option_text": response.selected_option.option_text,
                            "option_order": response.selected_option.option_order
                        },
                        "all_options": options_data,
                        "answered_at": response.created_at
                    })
                
                data = {
                    "weekly_checkin": {
                        "weekly_checkin_id": weekly_checkin.id,
                        "week_number": weekly_checkin.week_number,
                        "completed_at": weekly_checkin.completed_at,
                        "is_completed": weekly_checkin.is_completed,
                        "is_available": weekly_checkin.is_available,
                        "days_required": weekly_checkin.week_number * 7,
                        "days_progress": user.streak.current_streak,
                        "status": "completed" if weekly_checkin.is_completed else "available" if weekly_checkin.is_available else "locked",
                        "total_responses": responses.count()
                    },
                    "questions_and_answers": questions_and_answers,
                    "summary": {
                        "total_questions": len(questions_and_answers),
                        "completion_rate": f"{len(questions_and_answers)}/10" if len(questions_and_answers) <= 10 else f"{len(questions_and_answers)}/{len(questions_and_answers)}"
                    },
                    "current_streak": user.streak.current_streak
                }
                
                return Response({
                    "success": True,
                    "message": "Weekly check-in details retrieved successfully",
                    "timestamp": timezone.now(),
                    "status_code": 200,
                    "data": data
                })
                
            except UserWeeklyCheckin.DoesNotExist:
                return Response({
                    "success": False,
                    "message": f"Weekly check-in for week {week_number} not found",
                    "timestamp": timezone.now(),
                    "status_code": 404,
                    "data": {}
                })
        
        else:
            # List all weekly check-ins (your existing logic)
            try:
                # Calculate how many weeks user should have based on their streak
                current_streak = user.streak.current_streak
                max_possible_weeks = (current_streak // 7) + 3  # Add buffer for future weeks
                
                weekly_checkins = []
                total_completed = 0
                total_available = 0
                
                for week_num in range(max_possible_weeks, 0, -1):  # Reverse order (newest first)
                    days_required = week_num * 7
                    
                    try:
                        weekly_checkin = UserWeeklyCheckin.objects.get(
                            user=user,
                            week_number=week_num
                        )
                        
                        # Count responses for this weekly checkin
                        response_count = UserWeeklyCheckinResponse.objects.filter(
                            weekly_checkin=weekly_checkin
                        ).count()
                        
                        status = "completed" if weekly_checkin.is_completed else "available" if weekly_checkin.is_available else "locked"
                        
                        if weekly_checkin.is_completed:
                            total_completed += 1
                        elif weekly_checkin.is_available:
                            total_available += 1
                        
                        weekly_checkins.append({
                            "weekly_checkin_id": weekly_checkin.id,
                            "week_number": week_num,
                            "completed_at": weekly_checkin.completed_at,
                            "total_responses": response_count,
                            "is_available": weekly_checkin.is_available,
                            "is_completed": weekly_checkin.is_completed,
                            "days_required": days_required,
                            "days_progress": current_streak,
                            "status": status
                        })
                        
                    except UserWeeklyCheckin.DoesNotExist:
                        # Weekly checkin doesn't exist yet
                        is_available = current_streak >= days_required
                        status = "available" if is_available else "locked"
                        
                        if is_available:
                            total_available += 1
                        
                        weekly_checkins.append({
                            "weekly_checkin_id": None,
                            "week_number": week_num,
                            "completed_at": None,
                            "total_responses": 0,
                            "is_available": is_available,
                            "is_completed": False,
                            "days_required": days_required,
                            "days_progress": current_streak,
                            "status": status
                        })
                
                # Generate appropriate message
                if total_available > 0:
                    message = f"You have {total_available} weekly check-in{'s' if total_available != 1 else ''} available to complete!"
                elif total_completed > 0:
                    message = f"Great job! You've completed {total_completed} weekly check-in{'s' if total_completed != 1 else ''}."
                else:
                    message = "Keep building your daily streak to unlock weekly check-ins!"
                
                data = {
                    "completed_weekly_checkins": weekly_checkins,
                    "total_completed_weekly_checkins": total_completed,
                    "total_available_weekly_checkins": total_available,
                    "current_streak": current_streak,
                    "message": message
                }
                
                return Response({
                    "success": True,
                    "message": "Success",
                    "timestamp": timezone.now(),
                    "status_code": 200,
                    "data": data
                })
                
            except Exception as e:
                return Response({
                    "success": False,
                    "message": f"Error retrieving weekly check-ins: {str(e)}",
                    "timestamp": timezone.now(),
                    "status_code": 500,
                    "data": {}
                })
            






from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import BadgeTemplate, UserAppBadge, UserWeeklyCheckin
from .serializers import BadgeTemplateSerializer, UserAppBadgeSerializer

class PopulateBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Populate badge templates with predefined data"""
        
        badge_data = [
            {
                'badge_type': 'default',
                'title': 'Welcome to the Glow-Up',
                'description': 'You just took the realest step: showing up. This little candle\'s your holy hype man, here to remind you that even small steps matter. You\'re not just checking in, you\'re planting seeds, watering roots, and building a flame that\'s gonna burn brighter than your screen on max brightness at midnight.',
                'order': 1,
                'days_required': 0
            },
            {
                'badge_type': 'first_week_checked',
                'title': 'The Seed of Faith',
                'description': 'Your faith may start small, but its potential is immeasurable. You\'ve taken the first step-watch as God works through your commitment to grow it into something extraordinary.',
                'order': 2,
                'days_required': None
            },
            {
                'badge_type': 'first_week',
                'title': 'Rooted in Grace',
                'description': 'Your roots are strengthening, sinking deeper, nourished by His grace and your growing connection to His Word. Keep going!',
                'order': 3,
                'days_required': 7
            },
            {
                'badge_type': 'two_week',
                'title': 'The Sprout',
                'description': 'Growth is visible now-your confidence is breaking ground and your consistency is bringing new life to your faith.',
                'order': 4,
                'days_required': 14
            },
            {
                'badge_type': 'one_month',
                'title': 'Reaching Towards the Light',
                'description': 'As a tree stretches toward the sun, you are reaching for God\'s truth. Your faith has been tested and refined, growing stronger with each step of your journey.',
                'order': 5,
                'days_required': 30
            },
            {
                'badge_type': 'three_months',
                'title': 'Branches of Influence',
                'description': 'Your journey is inspiring others, offering a haven of confidence, clarity, and a source of hope as they witness your faith flourish. Every check-in reflects your steady progress.',
                'order': 6,
                'days_required': 90
            },
            {
                'badge_type': 'six_months',
                'title': 'Flourishing Faith',
                'description': 'Your journey has brought you to a place of flourishing, where God\'s purpose shines through you. With His Spirit as your guide, your faith continues to inspire and bless others. You have to see where your journey leads you next!',
                'order': 7,
                'days_required': 180
            },
            {
                'badge_type': 'one_year',
                'title': 'A Life of Overflowing Abundance',
                'description': 'A word fitly spoken is like apples of gold in settings of silver\' (Proverbs 25:11). Your journey has brought you to a place of wisdom and grace, where your words reflect God\'s truth and love. With confidence rooted in His guidance, you are equipped to share your faith in ways that inspire and uplift others. You are a beacon of faith shining bright with His purpose.',
                'order': 8,
                'days_required': 365
            }
        ]
        
        created_count = 0
        for data in badge_data:
            badge_template, created = BadgeTemplate.objects.get_or_create(
                badge_type=data['badge_type'],
                defaults=data
            )
            if created:
                created_count += 1
        
        return self.success_response({
            'message': f'{created_count} badge templates created successfully',
            'total_badges': BadgeTemplate.objects.count()
        }, status=status.HTTP_201_CREATED)


class UserAppBadgesListAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's earned badges"""
        user = request.user
        user_badges = UserAppBadge.objects.filter(user=user).select_related('badge_template')
        serializer = UserAppBadgeSerializer(user_badges, many=True)
        
        return self.success_response({
            'badges': serializer.data,
            'total_earned': user_badges.count()
        }, status=status.HTTP_200_OK)


class CheckAndAwardBadgesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Check and award new badges to user"""
        user = request.user
        newly_awarded = []
        
        try:
            # Award default badge if not already awarded
            default_template = BadgeTemplate.objects.get(badge_type='default')
            default_badge, created = UserAppBadge.objects.get_or_create(
                user=user,
                badge_template=default_template
            )
            if created:
                newly_awarded.append(default_badge)
        except BadgeTemplate.DoesNotExist:
            pass
        
        # Check for first weekly checkin badge
        first_checkin_completed = UserWeeklyCheckin.objects.filter(
            user=user, 
            is_completed=True
        ).exists()
        
        if first_checkin_completed:
            try:
                first_checkin_template = BadgeTemplate.objects.get(badge_type='first_week_checked')
                first_checkin_badge, created = UserAppBadge.objects.get_or_create(
                    user=user,
                    badge_template=first_checkin_template
                )
                if created:
                    newly_awarded.append(first_checkin_badge)
            except BadgeTemplate.DoesNotExist:
                pass
        
        # Check time-based badges
        user_days_in_app = (timezone.now().date() - user.date_joined.date()).days
        
        time_based_templates = BadgeTemplate.objects.filter(
            days_required__isnull=False,
            days_required__lte=user_days_in_app
        ).exclude(badge_type='default')
        
        for template in time_based_templates:
            badge, created = UserAppBadge.objects.get_or_create(
                user=user,
                badge_template=template
            )
            if created:
                newly_awarded.append(badge)
        
        # Serialize newly awarded badges
        serializer = UserAppBadgeSerializer(newly_awarded, many=True)
        
        return self.success_response({
            'newly_awarded': serializer.data,
            'count': len(newly_awarded),
            'message': f'{len(newly_awarded)} new badges awarded!' if newly_awarded else 'No new badges to award'
        }, status=status.HTTP_200_OK)


class AllBadgeTemplatesAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all available badge templates"""
        templates = BadgeTemplate.objects.all()
        serializer = BadgeTemplateSerializer(templates, many=True)
        
        return self.success_response({
            'badge_templates': serializer.data
        }, status=status.HTTP_200_OK)