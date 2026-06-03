
import random
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.goal.models import UserGoal, ChapterRead, ConversationInteraction, ShareActivity
from apps.core.utils.mixins import BaseResponseMixin


class GenerateTestDataView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate fake historical goal data for testing"""
        try:
            data = request.data
            weeks_to_generate = data.get('weeks', 8)  # Default 8 weeks
            clear_existing = data.get('clear_existing', False)  # Option to clear existing data
            
            if weeks_to_generate > 20:
                return self.bad_request_response(
                    message="Maximum 20 weeks allowed for test data generation"
                )
            
            user = request.user
            today = timezone.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            
            with transaction.atomic():
                if clear_existing:
                    UserGoal.objects.filter(user=user).delete()
                    ChapterRead.objects.filter(user=user).delete()
                    ConversationInteraction.objects.filter(user=user).delete()
                    ShareActivity.objects.filter(user=user).delete()
                
                created_weeks = []
                
                for i in range(weeks_to_generate):
                    week_start = current_week_start - timedelta(weeks=i)
                    week_end = week_start + timedelta(days=6)
                    if not clear_existing and UserGoal.objects.filter(user=user, week_start=week_start).exists():
                        continue
                    
                    week_data = {
                        'week_start': week_start,
                        'week_end': week_end,
                        'is_current_week': i == 0,
                        'goals': []
                    }
                    goal_configs = [
                        {
                            'goal_type': 'scripture',
                            'target_count': random.choice([20, 25, 30]),
                            'completion_rate': random.uniform(0.3, 1.0)  # 30% to 100% completion
                        },
                        {
                            'goal_type': 'conversation', 
                            'target_count': random.choice([8, 10, 12]),
                            'completion_rate': random.uniform(0.4, 1.0)  # 40% to 100% completion
                        },
                        {
                            'goal_type': 'share_faith',
                            'target_count': random.choice([7, 10, 15]),
                            'completion_rate': random.uniform(0.2, 1.0)  # 20% to 100% completion
                        }
                    ]
                    
                    for config in goal_configs:
                        target = config['target_count']
                        current_count = int(target * config['completion_rate'])
                        if current_count < target:
                            current_count = min(target, current_count + random.randint(0, 3))
                        goal = UserGoal.objects.create(
                            user=user,
                            goal_type=config['goal_type'],
                            week_start=week_start,
                            target_count=target,
                            current_count=current_count,
                            completed=current_count >= target
                        )
                        self._create_activity_records(user, config['goal_type'], current_count)
                        week_data['goals'].append({
                            'goal_type': goal.goal_type,
                            'goal_display': goal.get_goal_type_display(),
                            'current_count': goal.current_count,
                            'target_count': goal.target_count,
                            'completed': goal.completed,
                            'progress_percentage': round((goal.current_count / goal.target_count * 100), 1) if goal.target_count > 0 else 0
                        })
                    
                    created_weeks.append(week_data)
                
                response_data = {
                    'weeks_generated': len(created_weeks),
                    'total_goals_created': len(created_weeks) * 3,
                    'clear_existing': clear_existing,
                    'weeks': created_weeks
                }
                
                return self.success_response(
                    data=response_data,
                    message=f"Successfully generated test data for {len(created_weeks)} weeks"
                )
                
        except Exception as exc:
            return self.handle_exception(exc)
    
    def _create_activity_records(self, user, goal_type, count):
        """Create corresponding activity records for the goals (simplified)"""
        import time
        
        for i in range(count):
            timestamp = int(time.time() * 1000) + i  # Simple unique timestamp
            
            if goal_type == 'scripture':
                ChapterRead.objects.create(
                    user=user,
                    bible_id='bible',
                    chapter_id=f'test_chapter_{timestamp}_{i}'
                )
            elif goal_type == 'conversation':
                ConversationInteraction.objects.create(
                    user=user,
                    content_type='conversation',
                    content_id=f'test_thumbs_up_{timestamp}_{i}',
                    interaction_type='thumbs_up'
                )
            elif goal_type == 'share_faith':
                ShareActivity.objects.create(
                    user=user,
                    content_type='share',
                    content_id=f'test_share_{timestamp}_{i}',
                    share_platform=random.choice(['app', 'facebook', 'instagram', 'whatsapp'])
                )


class ClearTestDataView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Clear all goal data for the current user"""
        try:
            user = request.user
            
            with transaction.atomic():
                goals_deleted = UserGoal.objects.filter(user=user).count()
                chapters_deleted = ChapterRead.objects.filter(user=user).count()
                conversations_deleted = ConversationInteraction.objects.filter(user=user).count()
                shares_deleted = ShareActivity.objects.filter(user=user).count()
                UserGoal.objects.filter(user=user).delete()
                ChapterRead.objects.filter(user=user).delete()
                ConversationInteraction.objects.filter(user=user).delete()
                ShareActivity.objects.filter(user=user).delete()
                
                response_data = {
                    'goals_deleted': goals_deleted,
                    'chapters_deleted': chapters_deleted,
                    'conversations_deleted': conversations_deleted,
                    'shares_deleted': shares_deleted,
                    'total_records_deleted': goals_deleted + chapters_deleted + conversations_deleted + shares_deleted
                }
                
                return self.success_response(
                    data=response_data,
                    message="All test data cleared successfully"
                )
                
        except Exception as exc:
            return self.handle_exception(exc)


class QuickTestDataView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate quick test data with predefined scenarios"""
        try:
            user = request.user
            today = timezone.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            test_scenarios = [
                {
                    'week_offset': 0,
                    'goals': [
                        {'type': 'scripture', 'target': 25, 'current': 7},
                        {'type': 'conversation', 'target': 10, 'current': 4},
                        {'type': 'share_faith', 'target': 10, 'current': 7}
                    ]
                },
                {
                    'week_offset': 1,
                    'goals': [
                        {'type': 'scripture', 'target': 25, 'current': 23},
                        {'type': 'conversation', 'target': 10, 'current': 12},
                        {'type': 'share_faith', 'target': 10, 'current': 9}
                    ]
                },
                {
                    'week_offset': 2,
                    'goals': [
                        {'type': 'scripture', 'target': 20, 'current': 25},
                        {'type': 'conversation', 'target': 8, 'current': 10},
                        {'type': 'share_faith', 'target': 7, 'current': 8}
                    ]
                },
                {
                    'week_offset': 3,
                    'goals': [
                        {'type': 'scripture', 'target': 25, 'current': 8},
                        {'type': 'conversation', 'target': 10, 'current': 3},
                        {'type': 'share_faith', 'target': 10, 'current': 2}
                    ]
                },
                {
                    'week_offset': 4,
                    'goals': [
                        {'type': 'scripture', 'target': 30, 'current': 18},
                        {'type': 'conversation', 'target': 12, 'current': 15},
                        {'type': 'share_faith', 'target': 15, 'current': 12}
                    ]
                }
            ]
            
            created_weeks = []
            
            with transaction.atomic():
                for scenario in test_scenarios:
                    week_start = current_week_start - timedelta(weeks=scenario['week_offset'])
                    if UserGoal.objects.filter(user=user, week_start=week_start).exists():
                        continue
                    
                    week_goals = []
                    
                    for goal_data in scenario['goals']:
                        goal = UserGoal.objects.create(
                            user=user,
                            goal_type=goal_data['type'],
                            week_start=week_start,
                            target_count=goal_data['target'],
                            current_count=goal_data['current'],
                            completed=goal_data['current'] >= goal_data['target']
                        )
                        
                        week_goals.append({
                            'goal_type': goal.goal_type,
                            'current_count': goal.current_count,
                            'target_count': goal.target_count,
                            'completed': goal.completed,
                            'progress_percentage': round((goal.current_count / goal.target_count * 100), 1)
                        })
                    
                    created_weeks.append({
                        'week_start': week_start,
                        'goals': week_goals
                    })
            
            return self.success_response(
                data={
                    'weeks_created': len(created_weeks),
                    'weeks': created_weeks
                },
                message=f"Quick test data generated for {len(created_weeks)} weeks"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)
class SimpleTestDataView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate simple test data - goals only, no activity records"""
        try:
            user = request.user
            today = timezone.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            
            weeks_to_create = request.data.get('weeks', 5)
            created_weeks = []
            
            with transaction.atomic():
                for i in range(weeks_to_create):
                    week_start = current_week_start - timedelta(weeks=i)
                    if UserGoal.objects.filter(user=user, week_start=week_start).exists():
                        continue
                    goals_data = [
                        {
                            'goal_type': 'scripture',
                            'target_count': random.choice([20, 25, 30]),
                            'current_count': random.randint(5, 30)
                        },
                        {
                            'goal_type': 'conversation',
                            'target_count': random.choice([8, 10, 12]),
                            'current_count': random.randint(2, 15)
                        },
                        {
                            'goal_type': 'share_faith',
                            'target_count': random.choice([7, 10, 15]),
                            'current_count': random.randint(1, 12)
                        }
                    ]
                    
                    week_result = []
                    for goal_data in goals_data:
                        current = min(goal_data['current_count'], goal_data['target_count'] + 5)
                        
                        goal = UserGoal.objects.create(
                            user=user,
                            goal_type=goal_data['goal_type'],
                            week_start=week_start,
                            target_count=goal_data['target_count'],
                            current_count=current,
                            completed=current >= goal_data['target_count']
                        )
                        
                        week_result.append({
                            'goal_type': goal.goal_type,
                            'current_count': goal.current_count,
                            'target_count': goal.target_count,
                            'completed': goal.completed
                        })
                    
                    created_weeks.append({
                        'week_start': week_start,
                        'goals': week_result
                    })
            
            return self.success_response(
                data={
                    'weeks_created': len(created_weeks),
                    'weeks': created_weeks
                },
                message=f"Simple test data created for {len(created_weeks)} weeks"
            )
            
        except Exception as exc:
            return self.handle_exception(exc)