from django.urls import path
from . import views

urlpatterns = [
    path('daily-verse/', views.DailyVerseView.as_view(), name='daily-verse'),
    # path('refresh-daily-verse/', views.RefreshDailyVerseView.as_view(), name='refresh-daily-verse'),
    path('refresh-daily-verse/', views.JourneyDailyVerseView.as_view(), name='journey-verse'),
]