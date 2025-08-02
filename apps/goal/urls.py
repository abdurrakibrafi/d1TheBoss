# apps/goals/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Tracking endpoints
    path('track/scripture/', views.TrackScriptureReadingView.as_view(), name='track-scripture'),
    path('track/conversation/', views.TrackConversationInteractionView.as_view(), name='track-conversation'),
    path('track/share/', views.TrackShareActivityView.as_view(), name='track-share'),
    
    # Goal management endpoints
    path('current-week/', views.GetCurrentWeekGoalsView.as_view(), name='current-week-goal'),
    path('history/', views.GetGoalsHistoryView.as_view(), name='goals-history'),
    path('set-target/', views.SetGoalTargetView.as_view(), name='set-goal-target'),
    path('stats/', views.GoalStatsView.as_view(), name='goal-stats'),
]