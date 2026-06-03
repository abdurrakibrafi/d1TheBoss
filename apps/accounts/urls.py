from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ParmanentAccountDeleteView,
    RegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    PasswordResetRequestView,
    PasswordResetOTPVerifyView,
    ChangePasswordView,
    GoogleLogin,
    AppleLogin,
    ResendOTPView,
    PasswordResetConfirmView,
    AccountSoftDeleteView,
    AccountRestoreView,
    ProfileUpdateView,
    VerifyEmailChangeView,
    ResendEmailChangeOTPView,
    CancelEmailChangeView,
    InitiateRegistrationView,
    CompleteRegistrationView,
    SocialAuthView,
)

urlpatterns = [
    path(
        "register/initiate/",
        InitiateRegistrationView.as_view(),
        name="initiate-register",
    ),
    path(
        "register/complete/",
        CompleteRegistrationView.as_view(),
        name="complete-register",
    ),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "password/reset-request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password/reset-verify-otp/",
        PasswordResetOTPVerifyView.as_view(),
        name="password-reset-verify-otp",
    ),
    path(
        "password/reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm-view",
    ),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path(
        "profile/verify-email-change/",
        VerifyEmailChangeView.as_view(),
        name="verify-email-change",
    ),
    path(
        "profile/resend-email-change-otp/",
        ResendEmailChangeOTPView.as_view(),
        name="resend-email-change-otp",
    ),
    path(
        "profile/cancel-email-change/",
        CancelEmailChangeView.as_view(),
        name="cancel-email-change",
    ),
    path("parmanent/delete/", ParmanentAccountDeleteView.as_view(), name="parmanent-delete"),
    path("social-auth/", SocialAuthView.as_view(), name="social-auth"),
]




 