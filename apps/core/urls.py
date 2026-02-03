from django.urls import path, include
from apps.core import views

urlpatterns = [
    path(
        "legal/terms/", views.TermsAndConditionsView.as_view(), name="terms-conditions"
    ),
    path("legal/privacy/", views.PrivacyPolicyView.as_view(), name="privacy-policy"),
    path("guide/", views.APIGuideView.as_view(), name="api-guide"),
    path("fake-data/", views.FakeDataAPIView.as_view(), name="fake-data"),
    path(
        "populate-onboarding-data/",
        views.populate_onboarding_data,
        name="populate_onboarding_data",
    ),
    path('weekly-checkin/populate/', views.populate_weekly_checkin_questions, name='populate_weekly_checkin'),
    path('weekly-checkin/questions/', views.get_weekly_checkin_questions, name='get_weekly_checkin_questions'),
]
