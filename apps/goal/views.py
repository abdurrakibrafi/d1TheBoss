# views.py - Goal tracking views with BaseResponseMixin

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, date
from django.db import transaction
from .models import UserGoal, ChapterRead, ConversationInteraction, ShareActivity
from .serializers import UserGoalSerializer
from apps.core.utils.mixins import BaseResponseMixin  


# Option 1: Convert function-based views to class-based views (Recommended)
class TrackScriptureReadingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user reads scripture"""
        try:
            # Create chapter read record (simple)
            ChapterRead.objects.create(
                user=request.user,
                bible_id='bible',
                chapter_id=f'chapter_{timezone.now().timestamp()}'  # Simple unique value
            )
            
            # Update scripture goal
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            goal, created = UserGoal.objects.get_or_create(
                user=request.user,
                goal_type='scripture',
                week_start=week_start,
                defaults={'target_count': 25}
            )
            
            completed = goal.increment_count()
            
            data = {
                'goal_completed': completed,
                'current_count': goal.current_count,
                'target_count': goal.target_count
            }
            
            return self.success_response(
                data=data,
                message="Scripture reading tracked successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class TrackConversationInteractionView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user gives thumbs up"""
        try:
            # Create interaction record (simple)
            ConversationInteraction.objects.create(
                user=request.user,
                content_type='conversation',
                content_id='thumbs_up',  # Simple fixed value
                interaction_type='thumbs_up'
            )
            
            # Update conversation goal
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            goal, created = UserGoal.objects.get_or_create(
                user=request.user,
                goal_type='conversation',
                week_start=week_start,
                defaults={'target_count': 10}
            )
            
            completed = goal.increment_count()
            
            data = {
                'goal_completed': completed,
                'current_count': goal.current_count,
                'target_count': goal.target_count
            }
            
            return self.success_response(
                data=data,
                message="Conversation interaction tracked successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class TrackShareActivityView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user shares content"""
        try:
            # Generate unique content_id automatically
            import time
            content_id = f'share_{int(time.time() * 1000)}'  # More unique with milliseconds
            
            # Create share record (simple)
            ShareActivity.objects.create(
                user=request.user,
                content_type='share',
                content_id=content_id,
                share_platform='app'
            )
            
            # Update share goal
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            goal, created = UserGoal.objects.get_or_create(
                user=request.user,
                goal_type='share_faith',
                week_start=week_start,
                defaults={'target_count': 10}
            )
            
            completed = goal.increment_count()
            
            data = {
                'goal_completed': completed,
                'current_count': goal.current_count,
                'target_count': goal.target_count
            }
            
            return self.success_response(
                data=data,
                message="Share activity tracked successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GetCurrentWeekGoalsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current week goals (7 days - Monday to Sunday)"""
        try:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())  # Monday
            week_end = week_start + timedelta(days=6)  # Sunday
            
            # Create goals for current week if they don't exist
            for goal_type_key in ['scripture', 'conversation', 'share_faith']:
                target = 25 if goal_type_key == 'scripture' else 10
                UserGoal.objects.get_or_create(
                    user=request.user,
                    goal_type=goal_type_key,
                    week_start=week_start,
                    defaults={'target_count': target}
                )
            
            # Get current week goals
            goals = UserGoal.objects.filter(user=request.user, week_start=week_start)
            
            goals_data = []
            for goal in goals:
                goals_data.append({
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'completed': goal.completed,
                    'progress_percentage': round((goal.current_count / goal.target_count * 100), 1) if goal.target_count > 0 else 0
                })
            
            data = {
                'week_start': week_start,
                'week_end': week_end,
                'days_remaining': (week_end - today).days + 1 if today <= week_end else 0,
                'goals': goals_data
            }
            
            return self.success_response(
                data=data,
                message="Current week goals retrieved successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GetGoalsHistoryView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get weekly goals history"""
        try:
            weeks = int(request.query_params.get('weeks', 8))  # Default last 8 weeks
            
            today = timezone.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            
            history = []
            
            for i in range(weeks):
                week_start = current_week_start - timedelta(weeks=i)
                week_end = week_start + timedelta(days=6)
                
                # Get goals for this week
                week_goals = UserGoal.objects.filter(user=request.user, week_start=week_start)
                
                if week_goals.exists():  # Only show weeks where user had activity
                    goals_data = []
                    for goal in week_goals:
                        goals_data.append({
                            'goal_type': goal.goal_type,
                            'goal_display': goal.get_goal_type_display(),
                            'current_count': goal.current_count,
                            'target_count': goal.target_count,
                            'completed': goal.completed,
                            'progress_percentage': round((goal.current_count / goal.target_count * 100), 1) if goal.target_count > 0 else 0
                        })
                    
                    week_data = {
                        'week_start': week_start,
                        'week_end': week_end,
                        'is_current_week': i == 0,
                        'goals': goals_data
                    }
                    
                    history.append(week_data)
            
            data = {
                'total_weeks': len(history),
                'weeks': history
            }
            
            return self.success_response(
                data=data,
                message="Goals history retrieved successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class SetGoalTargetView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to set custom goal targets"""
        try:
            data = request.data
            goal_type = data.get('goal_type')
            target_count = data.get('target_count')
            
            if goal_type not in ['scripture', 'conversation', 'share_faith']:
                return self.bad_request_response(
                    message="Invalid goal type",
                    errors={'goal_type': ['Must be one of: scripture, conversation, share_faith']}
                )
            
            if not target_count or target_count <= 0:
                return self.bad_request_response(
                    message="Invalid target count",
                    errors={'target_count': ['Target count must be greater than 0']}
                )
            
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            goal, created = UserGoal.objects.get_or_create(
                user=request.user,
                goal_type=goal_type,
                week_start=week_start,
                defaults={'target_count': target_count}
            )
            
            if not created:
                goal.target_count = target_count
                goal.save()
            
            response_data = {
                'goal_type': goal_type,
                'target_count': goal.target_count,
                'current_count': goal.current_count
            }
            
            message = "Goal target created successfully" if created else "Goal target updated successfully"
            
            return self.success_response(
                data=response_data,
                message=message
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GoalStatsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get comprehensive goal statistics"""
        try:
            user = request.user
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            # Current week stats
            current_goals = UserGoal.objects.filter(user=user, week_start=week_start)
            current_stats = {}
            for goal in current_goals:
                current_stats[goal.goal_type] = {
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'completed': goal.completed,
                    'progress_percentage': round((goal.current_count / goal.target_count * 100), 1) if goal.target_count > 0 else 0
                }
            
            # All time stats
            all_time_stats = {
                'total_chapters_read': ChapterRead.objects.filter(user=user).count(),
                'total_conversations': ConversationInteraction.objects.filter(user=user).count(),
                'total_shares': ShareActivity.objects.filter(user=user).count(),
                'total_goals_completed': UserGoal.objects.filter(user=user, completed=True).count(),
                'weeks_active': UserGoal.objects.filter(user=user).values('week_start').distinct().count()
            }
            
            # Last 4 weeks performance
            last_4_weeks = []
            for i in range(4):
                week_date = week_start - timedelta(weeks=i)
                week_goals = UserGoal.objects.filter(user=user, week_start=week_date)
                week_data = {
                    'week_start': week_date,
                    'goals': {}
                }
                for goal in week_goals:
                    week_data['goals'][goal.goal_type] = {
                        'current_count': goal.current_count,
                        'target_count': goal.target_count,
                        'completed': goal.completed
                    }
                last_4_weeks.append(week_data)
            
            data = {
                'current_week': current_stats,
                'all_time': all_time_stats,
                'last_4_weeks': last_4_weeks
            }
            
            return self.success_response(
                data=data,
                message="Goal statistics retrieved successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


# Option 2: If you want to keep function-based views, create a helper function
class ResponseHelper(BaseResponseMixin):
    """Helper class to use BaseResponseMixin methods in function-based views"""
    pass

# Helper instance
response_helper = ResponseHelper()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_scripture_reading_fbv(request):
    """Function-based view example using response helper"""
    try:
        # Your existing logic here...
        ChapterRead.objects.create(
            user=request.user,
            bible_id='bible',
            chapter_id=f'chapter_{timezone.now().timestamp()}'
        )
        
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        goal, created = UserGoal.objects.get_or_create(
            user=request.user,
            goal_type='scripture',
            week_start=week_start,
            defaults={'target_count': 25}
        )
        
        completed = goal.increment_count()
        
        data = {
            'goal_completed': completed,
            'current_count': goal.current_count,
            'target_count': goal.target_count
        }
        
        return response_helper.success_response(
            data=data,
            message="Scripture reading tracked successfully"
        )
        
    except Exception as exc:
        return response_helper.handle_exception(exc)