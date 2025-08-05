# checkin/urls.py
from django.urls import path
from .views import *
from .tests import CreateTestDataAPIView, ResetTestDataAPIView, QuickTestScenariosAPIView, DataStatusAPIView

urlpatterns = [
    # Daily check-in
    path('daily/', DailyCheckinAPIView.as_view(), name='daily-checkin'),
    
    # Calendar data
    path('calendar/', CalendarDataAPIView.as_view(), name='calendar-data'),
    
    # Profile dashboard
    path('dashboard/', ProfileDashboardAPIView.as_view(), name='profile-dashboard'),
    
    # Weekly check-ins
    path('weekly/questions/', WeeklyCheckinQuestionsAPIView.as_view(), name='weekly-questions'),
    path('weekly/submit/', WeeklyCheckinSubmitAPIView.as_view(), name='weekly-submit'),
    path('weekly/history/', WeeklyCheckinHistoryAPIView.as_view(), name='weekly-history'),
    path('weekly/history/<int:week_number>/', WeeklyCheckinHistoryAPIView.as_view(), name='weekly-history-detail'),

    # Test Data APIs
    path('test/create/', CreateTestDataAPIView.as_view(), name='create-test-data'),
    path('test/reset/', ResetTestDataAPIView.as_view(), name='reset-test-data'),
    path('test/scenarios/', QuickTestScenariosAPIView.as_view(), name='test-scenarios'),
    path('test/status/', DataStatusAPIView.as_view(), name='data-status'),    
    
    # Notifications
    # path('notifications/settings/', NotificationSettingsAPIView.as_view(), name='notification-settings'),

    path('badges/populate/', PopulateBadgeTemplatesAPIView.as_view(), name='populate-badges'),
    path('badges/my-badges/', UserAppBadgesListAPIView.as_view(), name='user-badges'),
    path('badges/check-awards/', CheckAndAwardBadgesAPIView.as_view(), name='check-award-badges'),
    path('badges/templates/', AllBadgeTemplatesAPIView.as_view(), name='badge-templates'),
]
