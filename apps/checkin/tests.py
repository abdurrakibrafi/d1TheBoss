from django.test import TestCase

from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import WeeklyCheckinQuestion, WeeklyCheckinOption, DailyCheckin, UserStreak, UserBadge, UserWeeklyCheckin, UserWeeklyCheckinResponse

class CreateTestDataAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create test data for check-in system using existing questions"""
        days = request.data.get('days', 14)
        user = request.user
        
        try:
            # Check if we have questions in database
            questions_count = WeeklyCheckinQuestion.objects.filter(is_active=True).count()
            if questions_count == 0:
                return Response({
                    'error': 'No questions found in database. Please create questions first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create streak data
            result = self._create_streak_data(user, days)
            
            return Response({
                'message': f'Successfully created test data with {days} days streak',
                'user': user.email,
                'days_created': days,
                'weeks_completed': days // 7,
                'badges_earned': result['badges_count'],
                'questions_available': questions_count
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create test data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_streak_data(self, user, days):
        """Create streak data for testing"""
        # Clear existing data first
        DailyCheckin.objects.filter(user=user).delete()
        UserWeeklyCheckin.objects.filter(user=user).delete()
        UserBadge.objects.filter(user=user).delete()
        
        # Create or get user streak
        user_streak, _ = UserStreak.objects.get_or_create(user=user)
        user_streak.current_streak = days
        user_streak.longest_streak = days
        user_streak.last_checkin_date = timezone.now().date() if days > 0 else None
        user_streak.save()
        
        badges_count = 0
        
        if days > 0:
            # Create daily check-ins
            start_date = timezone.now().date() - timedelta(days=days-1)
            for i in range(days):
                checkin_date = start_date + timedelta(days=i)
                DailyCheckin.objects.create(
                    user=user,
                    checkin_date=checkin_date,
                    streak_day=i+1
                )
            
            # Create weekly check-ins and badges
            weeks_completed = days // 7
            if weeks_completed > 0:
                # Get all active questions from database
                questions = WeeklyCheckinQuestion.objects.filter(is_active=True).order_by('question_order')
                
                for week in range(1, weeks_completed + 1):
                    # Create weekly check-in
                    weekly_checkin = UserWeeklyCheckin.objects.create(
                        user=user,
                        week_number=week,
                        is_available=True,
                        is_completed=True,
                        completed_at=timezone.now() - timedelta(days=(weeks_completed-week)*7)
                    )
                    
                    # Create sample responses using your real questions
                    for question in questions:
                        options = question.options.all()
                        if options:
                            # Vary responses based on week for realistic data
                            option_index = (week + question.id) % len(options)
                            UserWeeklyCheckinResponse.objects.create(
                                weekly_checkin=weekly_checkin,
                                question=question,
                                selected_option=options[option_index]
                            )
                    
                    # Award badges for milestones
                    milestones = self._get_badge_milestones()
                    for milestone in milestones:
                        if week >= milestone:
                            badge, created = UserBadge.objects.get_or_create(
                                user=user,
                                weeks_completed=milestone,
                                defaults={'badge_name': f'{milestone} Week{"s" if milestone > 1 else ""}'}
                            )
                            if created:
                                badges_count += 1
            
            # Create current week check-in if user has 7+ days and completed a full week
            if days >= 7 and days % 7 < 7:  # Has started a new week but not completed it
                UserWeeklyCheckin.objects.get_or_create(
                    user=user,
                    week_number=weeks_completed + 1,
                    defaults={'is_available': True, 'is_completed': False}
                )
        
        return {'badges_count': badges_count}

    def _get_badge_milestones(self):
        """Get badge milestones"""
        milestones = [1, 2, 4, 8, 12]
        current = 16
        while current <= 100:
            milestones.append(current)
            current += 4
        return milestones


class ResetTestDataAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """Reset all test data for current user"""
        user = request.user
        
        try:
            # Count before deletion
            deleted_counts = {
                'daily_checkins': DailyCheckin.objects.filter(user=user).count(),
                'weekly_checkins': UserWeeklyCheckin.objects.filter(user=user).count(),
                'weekly_responses': UserWeeklyCheckinResponse.objects.filter(weekly_checkin__user=user).count(),
                'badges': UserBadge.objects.filter(user=user).count()
            }
            
            # Delete all user data
            DailyCheckin.objects.filter(user=user).delete()
            UserWeeklyCheckin.objects.filter(user=user).delete()
            UserBadge.objects.filter(user=user).delete()
            
            # Reset streak
            if hasattr(user, 'streak'):
                user.streak.current_streak = 0
                user.streak.longest_streak = 0
                user.streak.last_checkin_date = None
                user.streak.save()
            
            return Response({
                'message': 'Successfully reset all test data',
                'deleted': deleted_counts,
                'user': user.email
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to reset test data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class QuickTestScenariosAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create predefined test scenarios"""
        scenario = request.data.get('scenario', 'basic')
        user = request.user
        
        scenarios = {
            'new_user': {
                'days': 0,
                'description': 'Brand new user with no streak'
            },
            'basic': {
                'days': 3,
                'description': 'Basic user with 3-day streak (no weekly yet)'
            },
            'first_week': {
                'days': 7,
                'description': 'User who just completed first week'
            },
            'two_weeks': {
                'days': 14,
                'description': 'User with 2 weeks completed'
            },
            'one_month': {
                'days': 28,
                'description': 'User with 4 weeks (1 month)'
            },
            'power_user': {
                'days': 56,
                'description': 'Power user with 8 weeks completed'
            },
            'broken_streak': {
                'days': 1,
                'description': 'User who broke streak and restarted'
            },
            'almost_week': {
                'days': 6,
                'description': 'User almost at first week milestone'
            }
        }
        
        if scenario not in scenarios:
            return Response({
                'error': 'Invalid scenario',
                'available_scenarios': {k: v['description'] for k, v in scenarios.items()}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if questions exist
            questions_count = WeeklyCheckinQuestion.objects.filter(is_active=True).count()
            if questions_count == 0:
                return Response({
                    'error': 'No questions found in database. Please create questions first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset first - do it the same way as ResetTestDataAPIView
            DailyCheckin.objects.filter(user=user).delete()
            UserWeeklyCheckin.objects.filter(user=user).delete()
            UserBadge.objects.filter(user=user).delete()
            
            # Reset streak
            if hasattr(user, 'streak'):
                user.streak.current_streak = 0
                user.streak.longest_streak = 0
                user.streak.last_checkin_date = None
                user.streak.save()
            
            # Create scenario data
            days = scenarios[scenario]['days']
            result = {'badges_count': 0}
            if days > 0:
                # Use the same method as CreateTestDataAPIView
                create_api = CreateTestDataAPIView()
                result = create_api._create_streak_data(user, days)
            
            return Response({
                'message': f'Successfully created {scenario} scenario',
                'scenario': scenarios[scenario],
                'days_created': days,
                'weeks_completed': days // 7,
                'badges_earned': result['badges_count'],
                'questions_available': questions_count
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create scenario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


            
class DataStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current data status for user"""
        user = request.user
        
        # Count user data
        daily_checkins = DailyCheckin.objects.filter(user=user).count()
        weekly_checkins = UserWeeklyCheckin.objects.filter(user=user).count()
        completed_weeklies = UserWeeklyCheckin.objects.filter(user=user, is_completed=True).count()
        pending_weeklies = UserWeeklyCheckin.objects.filter(user=user, is_available=True, is_completed=False).count()
        badges = UserBadge.objects.filter(user=user).count()
        
        # System data
        questions = WeeklyCheckinQuestion.objects.filter(is_active=True).count()
        total_options = WeeklyCheckinOption.objects.count()
        
        # Get streak info
        streak_info = {'current_streak': 0, 'longest_streak': 0, 'last_checkin_date': None}
        if hasattr(user, 'streak'):
            streak_info = {
                'current_streak': user.streak.current_streak,
                'longest_streak': user.streak.longest_streak,
                'last_checkin_date': user.streak.last_checkin_date.isoformat() if user.streak.last_checkin_date else None
            }
        
        # Get latest badge info
        latest_badge = UserBadge.objects.filter(user=user).order_by('-weeks_completed').first()
        
        return Response({
            'user': user.email,
            'data_counts': {
                'daily_checkins': daily_checkins,
                'weekly_checkins': weekly_checkins,
                'completed_weekly_checkins': completed_weeklies,
                'pending_weekly_checkins': pending_weeklies,
                'badges_earned': badges,
                'questions_available': questions,
                'total_options': total_options
            },
            'streak_info': streak_info,
            'latest_badge': {
                'badge_name': latest_badge.badge_name if latest_badge else None,
                'weeks_completed': latest_badge.weeks_completed if latest_badge else 0
            },
            'system_ready': questions >= 10,  # System needs 10 questions to work
            'last_updated': timezone.now().isoformat()
        })