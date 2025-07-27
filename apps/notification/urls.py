from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Use 'list' instead of empty string to avoid conflicts
router.register(r'list', views.NotificationViewSet, basename='notifications')
router.register(r'fcm-tokens', views.FCMTokenViewSet, basename='fcm-tokens')

urlpatterns = [
    path('', include(router.urls)),
    path('send/', views.SendNotificationView.as_view(), name='send-notification'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),
]