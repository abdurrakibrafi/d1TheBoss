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
    UserGoal
    )
from apps.checkin.serializers import (
    DailyCheckinSerializer,
    UserStreakSerializer,
    UserBadgeSerializer,
    WeeklyCheckinQuestionSerializer,
    WeeklyCheckinOptionSerializer,
    WeeklyCheckinResponseSerializer,
    UserGoalSerializer
    )
from apps.core.utils.mixins import BaseResponseMixin

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
        """Make weekly checkin available after 7 consecutive days"""
        current_streak = user.streak.current_streak
        
        # Only create records when streak reaches exact multiples of 7
        if current_streak > 0 and current_streak % 7 == 0:
            week_num = current_streak // 7
            
            # Create weekly check-in for this specific week
            weekly_checkin, created = UserWeeklyCheckin.objects.get_or_create(
                user=user,
                week_number=week_num,
                defaults={'is_available': True}
            )
            
            if created:
                print(f"Created Week {week_num} checkin for user {user.id} at {current_streak} days streak")



class CalendarDataAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get calendar data with check-in history"""
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        user = request.user
        checkins = DailyCheckin.objects.filter(user=user)
        
        if month and year:
            checkins = checkins.filter(
                checkin_date__month=month,
                checkin_date__year=year
            )
        
        serializer = DailyCheckinSerializer(checkins, many=True)
        
        return self.success_response({
            'checkins': serializer.data,
            'current_streak': user.streak.current_streak if hasattr(user, 'streak') else 0
        })
    

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
        
        # Validate all 10 questions answered
        if len(responses) != 10:
            return self.error_response({
                'error': 'All 10 questions must be answered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save responses
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
        
        return self.success_response({
            'message': 'Weekly check-in completed successfully',
            'week_number': weekly_checkin.week_number
        }, status=status.HTTP_201_CREATED)
    

class WeeklyCheckinHistoryAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, week_number=None):
        """Get weekly check-in history - ALWAYS visible regardless of current streak"""
        user = request.user
        
        if week_number:
            # Get specific week (existing code unchanged)
            try:
                weekly_checkin = UserWeeklyCheckin.objects.get(
                    user=user,
                    week_number=week_number
                )
            except UserWeeklyCheckin.DoesNotExist:
                return self.success_response({
                    'error': 'Weekly check-in not found',
                    'week_number': week_number,
                    'is_completed': False
                })
            
            # If completed, get responses
            if weekly_checkin.is_completed:
                responses = UserWeeklyCheckinResponse.objects.filter(
                    weekly_checkin=weekly_checkin
                ).select_related('question', 'selected_option')
                
                response_data = []
                for response in responses:
                    response_data.append({
                        'question': {
                            'id': response.question.id,
                            'text': response.question.question_text,
                            'order': response.question.question_order
                        },
                        'selected_option': {
                            'id': response.selected_option.id,
                            'text': response.selected_option.option_text,
                            'order': response.selected_option.option_order
                        },
                        'answered_at': response.created_at
                    })
                
                return self.success_response({
                    'week_number': weekly_checkin.week_number,
                    'completed_at': weekly_checkin.completed_at,
                    'responses': response_data
                })
            else:
                return self.success_response({
                    'week_number': weekly_checkin.week_number,
                    'is_available': weekly_checkin.is_available,
                    'is_completed': False,
                    'message': 'Weekly check-in not completed yet'
                })
        
        else:
            # Get current streak
            current_streak = user.streak.current_streak if hasattr(user, 'streak') else 0
            
            # Get all existing weekly check-ins
            existing_checkins = UserWeeklyCheckin.objects.filter(user=user).order_by('-week_number')
            existing_checkins_dict = {checkin.week_number: checkin for checkin in existing_checkins}
            
            # Always show at least 4 weeks for consistent UI
            # But also include any existing weeks beyond 4
            max_existing_week = existing_checkins.first().week_number if existing_checkins.exists() else 0
            max_weeks_to_show = max(4, max_existing_week)
            
            checkins_data = []
            
            # Create consistent weekly check-in structure
            for week_num in range(1, max_weeks_to_show + 1):
                days_required = week_num * 7
                days_progress = min(current_streak, days_required)
                
                if week_num in existing_checkins_dict:
                    # Use existing checkin data
                    checkin = existing_checkins_dict[week_num]
                    checkins_data.append({
                        'weekly_checkin_id': checkin.id,
                        'week_number': checkin.week_number,
                        'completed_at': checkin.completed_at,
                        'total_responses': checkin.responses.count() if checkin.is_completed else 0,
                        'is_available': checkin.is_available and not checkin.is_completed and current_streak >= days_required,
                        'is_completed': checkin.is_completed,
                        'days_required': days_required,
                        'days_progress': days_progress,
                        'status': self._get_consistent_status(checkin, current_streak, days_required)
                    })
                else:
                    # Create placeholder for non-existing weeks
                    is_unlocked = current_streak >= days_required
                    checkins_data.append({
                        'weekly_checkin_id': None,
                        'week_number': week_num,
                        'completed_at': None,
                        'total_responses': 0,
                        'is_available': False,  # Only available when actual record exists
                        'is_completed': False,
                        'days_required': days_required,
                        'days_progress': days_progress,
                        'status': 'available' if is_unlocked else ('in_progress' if days_progress > (days_required - 7) else 'locked')
                    })
            
            # Sort by week number descending
            checkins_data.sort(key=lambda x: x['week_number'], reverse=True)
            
            # Calculate stats
            completed_count = len([c for c in checkins_data if c['is_completed']])
            available_count = len([c for c in checkins_data if c['is_available']])
            
            return self.success_response({
                'completed_weekly_checkins': checkins_data,
                'total_completed_weekly_checkins': completed_count,
                'total_available_weekly_checkins': available_count,
                'current_streak': current_streak,
                'message': self._get_status_message(current_streak, available_count)
            })
    
    def _get_consistent_status(self, checkin, current_streak, days_required):
        """Consistent status logic for existing weekly check-ins"""
        if checkin.is_completed:
            return 'completed'
        elif current_streak >= days_required and checkin.is_available:
            return 'available'
        elif current_streak < days_required:
            return 'locked'
        else:
            return 'missed'
    
    def _get_week_status(self, checkin, current_streak, days_required):
        """Determine status for existing weekly check-ins"""
        if checkin.is_completed:
            return 'completed'
        elif checkin.is_available and current_streak >= days_required:
            return 'available'
        elif checkin.is_available and current_streak < days_required:
            return 'locked'  # Was available but streak broke
        else:
            return 'missed'
    
    def _get_placeholder_status(self, current_streak, days_required):
        """Determine status for non-existing weekly check-ins"""
        if current_streak >= days_required:
            return 'missed'  # Should have been available
        elif current_streak >= (days_required - 7):
            return 'in_progress'
        else:
            return 'locked'
    
    def _get_status_message(self, current_streak, available_count):
        """Generate contextual message based on current state"""
        if current_streak == 0:
            return 'Start your daily check-in streak to unlock weekly check-ins!'
        elif current_streak < 7:
            days_needed = 7 - current_streak
            return f'Continue your streak! {days_needed} more day{"s" if days_needed > 1 else ""} to unlock your first weekly check-in.'
        elif available_count > 0:
            return f'You have {available_count} weekly check-in{"s" if available_count > 1 else ""} available to complete!'
        else:
            next_unlock_days = ((current_streak // 7) + 1) * 7
            days_to_next = next_unlock_days - current_streak
            next_week = (current_streak // 7) + 1
            return f'Great progress! {days_to_next} more day{"s" if days_to_next > 1 else ""} to unlock week {next_week} check-in.'