# urls.py (add to your existing urls)
from django.urls import path
from . import views

urlpatterns = [
    
    # Daily verse endpoints
    path('daily-verse/', views.DailyVerseView.as_view(), name='daily-verse'),
    path('refresh-daily-verse/', views.RefreshDailyVerseView.as_view(), name='refresh-daily-verse'),
]