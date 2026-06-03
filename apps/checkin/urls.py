from django.urls import path
from .views import *
from .tests import CreateTestDataAPIView, ResetTestDataAPIView, QuickTestScenariosAPIView, DataStatusAPIView

urlpatterns = [
    path('daily/', DailyCheckinAPIView.as_view(), name='daily-checkin'),
    path('calendar/', CalendarDataAPIView.as_view(), name='calendar-data'),
    path('dashboard/', ProfileDashboardAPIView.as_view(), name='profile-dashboard'),
    path('weekly/questions/', WeeklyCheckinQuestionsAPIView.as_view(), name='weekly-questions'),
    path('weekly/submit/', WeeklyCheckinSubmitAPIView.as_view(), name='weekly-submit'),
    path('weekly/history/', WeeklyCheckinHistoryAPIView.as_view(), name='weekly-history'),
    path('weekly/history/<int:week_number>/', WeeklyCheckinHistoryAPIView.as_view(), name='weekly-history-detail'),

    path('badges/populate/', PopulateBadgeTemplatesAPIView.as_view(), name='populate-badges'),
    path('badges/my-badges/', UserAppBadgesListAPIView.as_view(), name='user-badges'),
    path('badges/check-awards/', CheckAndAwardBadgesAPIView.as_view(), name='check-award-badges'),
    path('badges/templates/', AllBadgeTemplatesAPIView.as_view(), name='badge-templates'),
]
