# apps/goals/views.py

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


class TrackScriptureReadingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user reads scripture"""
        try:
            # Create chapter read record
            ChapterRead.objects.create(
                user=request.user,
                bible_id='bible',
                chapter_id=f'chapter_{timezone.now().timestamp()}'
            )
            
            # Get user's weekly goal
            goal, created = UserGoal.get_or_create_weekly_goal(request.user)
            
            # Only increment if this week's goal is scripture
            if goal.goal_type == 'scripture':
                completed = goal.increment_count()
                
                data = {
                    'goal_completed': completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': True
                }
                
                return self.success_response(
                    data=data,
                    message="Scripture reading tracked and counted toward your weekly goal!"
                )
            else:
                # Still record the activity but don't count toward goal
                data = {
                    'goal_completed': goal.completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': False,
                    'message': f'Great job reading! This week your focus is {goal.get_goal_type_display()}'
                }
                
                return self.success_response(
                    data=data,
                    message="Scripture reading recorded!"
                )
            
        except Exception as exc:
            return self.handle_exception(exc)


class TrackConversationInteractionView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user gives thumbs up"""
        try:
            # Create interaction record
            ConversationInteraction.objects.create(
                user=request.user,
                content_type='conversation',
                content_id='thumbs_up',
                interaction_type='thumbs_up'
            )
            
            # Get user's weekly goal
            goal, created = UserGoal.get_or_create_weekly_goal(request.user)
            
            # Only increment if this week's goal is conversation
            if goal.goal_type == 'conversation':
                completed = goal.increment_count()
                
                data = {
                    'goal_completed': completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': True
                }
                
                return self.success_response(
                    data=data,
                    message="Conversation interaction tracked and counted toward your weekly goal!"
                )
            else:
                data = {
                    'goal_completed': goal.completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': False,
                    'message': f'Great engagement! This week your focus is {goal.get_goal_type_display()}'
                }
                
                return self.success_response(
                    data=data,
                    message="Conversation interaction recorded!"
                )
            
        except Exception as exc:
            return self.handle_exception(exc)


class TrackShareActivityView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API to track when user shares content"""
        try:
            import time
            content_id = f'share_{int(time.time() * 1000)}'
            
            # Create share record
            ShareActivity.objects.create(
                user=request.user,
                content_type='share',
                content_id=content_id,
                share_platform=request.data.get('platform', 'app')
            )
            
            # Get user's weekly goal
            goal, created = UserGoal.get_or_create_weekly_goal(request.user)
            
            # Only increment if this week's goal is share_faith
            if goal.goal_type == 'share_faith':
                completed = goal.increment_count()
                
                data = {
                    'goal_completed': completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': True
                }
                
                return self.success_response(
                    data=data,
                    message="Share activity tracked and counted toward your weekly goal!"
                )
            else:
                data = {
                    'goal_completed': goal.completed,
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'progress_percentage': goal.progress_percentage(),
                    'activity_counted': False,
                    'message': f'Great sharing! This week your focus is {goal.get_goal_type_display()}'
                }
                
                return self.success_response(
                    data=data,
                    message="Share activity recorded!"
                )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GetCurrentWeekGoalsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current week's single goal based on user's faith preferences"""
        try:
            # Get user's weekly goal
            goal, created = UserGoal.get_or_create_weekly_goal(request.user)
            
            today = timezone.now().date()
            week_start = goal.week_start
            week_end = week_start + timedelta(days=6)
            
            goal_data = {
                'goal_type': goal.goal_type,
                'goal_display': goal.get_goal_type_display(),
                'current_count': goal.current_count,
                'target_count': goal.target_count,
                'completed': goal.completed,
                'progress_percentage': goal.progress_percentage()
            }
            
            data = {
                'week_start': week_start,
                'week_end': week_end,
                'days_remaining': goal.days_remaining,
                'goal': goal_data,
                'is_new_goal': created,
                'week_number': week_start.isocalendar()[1]  # Week number of the year
            }
            
            return self.success_response(
                data=data,
                message="Current week goal retrieved successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GetGoalsHistoryView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get weekly goals history"""
        try:
            weeks = int(request.query_params.get('weeks', 8))
            
            # Get user's goal history
            goals_history = UserGoal.objects.filter(user=request.user).order_by('-week_start')[:weeks]
            
            history = []
            for goal in goals_history:
                week_data = {
                    'week_start': goal.week_start,
                    'week_end': goal.week_end,
                    'week_number': goal.week_start.isocalendar()[1],
                    'goal': {
                        'goal_type': goal.goal_type,
                        'goal_display': goal.get_goal_type_display(),
                        'current_count': goal.current_count,
                        'target_count': goal.target_count,
                        'completed': goal.completed,
                        'progress_percentage': goal.progress_percentage()
                    }
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
        """API to set custom goal target for current week"""
        try:
            target_count = request.data.get('target_count')
            
            if not target_count or target_count <= 0:
                return self.bad_request_response(
                    message="Invalid target count",
                    errors={'target_count': ['Target count must be greater than 0']}
                )
            
            # Get current week's goal
            goal, created = UserGoal.get_or_create_weekly_goal(request.user)
            
            # Update target
            goal.target_count = target_count
            goal.save()
            
            response_data = {
                'goal_type': goal.goal_type,
                'goal_display': goal.get_goal_type_display(),
                'target_count': goal.target_count,
                'current_count': goal.current_count,
                'progress_percentage': goal.progress_percentage()
            }
            
            return self.success_response(
                data=response_data,
                message="Goal target updated successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)


class GoalStatsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get comprehensive goal statistics"""
        try:
            user = request.user
            
            # Get current week goal
            current_goal, created = UserGoal.get_or_create_weekly_goal(user)
            
            # All time stats
            all_time_stats = {
                'total_chapters_read': ChapterRead.objects.filter(user=user).count(),
                'total_conversations': ConversationInteraction.objects.filter(user=user).count(),
                'total_shares': ShareActivity.objects.filter(user=user).count(),
                'total_goals_completed': UserGoal.objects.filter(user=user, completed=True).count(),
                'weeks_active': UserGoal.objects.filter(user=user).count()
            }
            
            # Current week stats
            current_week_stats = {
                'goal_type': current_goal.goal_type,
                'goal_display': current_goal.get_goal_type_display(),
                'current_count': current_goal.current_count,
                'target_count': current_goal.target_count,
                'completed': current_goal.completed,
                'progress_percentage': current_goal.progress_percentage(),
                'days_remaining': current_goal.days_remaining
            }
            
            # Last 4 weeks performance
            last_4_weeks = []
            recent_goals = UserGoal.objects.filter(user=user).order_by('-week_start')[:4]
            
            for goal in recent_goals:
                week_data = {
                    'week_start': goal.week_start,
                    'week_end': goal.week_end,
                    'goal_type': goal.goal_type,
                    'goal_display': goal.get_goal_type_display(),
                    'current_count': goal.current_count,
                    'target_count': goal.target_count,
                    'completed': goal.completed,
                    'progress_percentage': goal.progress_percentage()
                }
                last_4_weeks.append(week_data)
            
            data = {
                'current_week': current_week_stats,
                'all_time': all_time_stats,
                'last_4_weeks': last_4_weeks
            }
            
            return self.success_response(
                data=data,
                message="Goal statistics retrieved successfully"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)