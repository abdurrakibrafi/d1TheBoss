
from django.urls import path, include
from . import views
from . import tests


urlpatterns = [
    # Goal tracking endpoints
    path('track-scripture/', views.TrackScriptureReadingView.as_view(), name='track-scripture-reading'),
    path('track-conversation/', views.TrackConversationInteractionView.as_view(), name='track-conversation-interaction'),
    path('track-share/', views.TrackShareActivityView.as_view(), name='track-share-activity'),
    
    # Goal retrieval endpoints
    path('current-week/', views.GetCurrentWeekGoalsView.as_view(), name='get-current-week-goals'),
    path('history/', views.GetGoalsHistoryView.as_view(), name='get-goals-history'),
    path('stats/', views.GoalStatsView.as_view(), name='goal-stats'),
    
    # Goal management endpoints
    path('set-target/', views.SetGoalTargetView.as_view(), name='set-goal-target'),

    
      # Test data endpoints (for development/testing only)
    path('test/generate/', tests.GenerateTestDataView.as_view(), name='generate-test-data'),
    path('test/quick/', tests.QuickTestDataView.as_view(), name='quick-test-data'),
    path('test/clear/', tests.ClearTestDataView.as_view(), name='clear-test-data'),

]
