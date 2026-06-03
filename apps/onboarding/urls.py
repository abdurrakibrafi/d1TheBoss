from django.urls import path
from apps.onboarding import views

urlpatterns = [
    path("options/", views.OnboardingOptionsView.as_view(), name="onboarding-options"),
    path("journey-reason/", views.JourneyReasonView.as_view(), name="journey-reason"),
    path("denomination/", views.DenominationView.as_view(), name="denomination"),
    path("faith-goals/", views.FaithGoalView.as_view(), name="faith-goals"),
    path(
        "tone-preference/", views.TonePreferenceView.as_view(), name="tone-preference"
    ),
    path(
        "bible-familiarity/",
        views.BibleFamiliarityView.as_view(),
        name="bible-familiarity",
    ),
    path("bible-version/", views.BibleVersionView.as_view(), name="bible-version"),
    path(
        "user-data/",
        views.UserOnboardingDataView.as_view(),
        name="user-onboarding-data",
    ),
    path(
        "progress/", views.OnboardingProgressView.as_view(), name="onboarding-progress"
    ),
    path("summary/", views.OnboardingSummaryView.as_view(), name="onboarding-summary"),
    path("status/", views.OnboardingStatusView.as_view(), name="onboarding-status"),
    path(
        "complete/", views.CompleteOnboardingView.as_view(), name="complete-onboarding"
    ),
]
