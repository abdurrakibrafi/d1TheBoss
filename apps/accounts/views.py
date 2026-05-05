from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import UserProfile, OTP
from django.utils import timezone
from datetime import timedelta
import random
from .serializers import (
    ParmanentAccountDeleteSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetOTPVerifySerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    SocialLoginSerializer,
    ResendOTPSerializer,
    AccountSoftDeleteSerializer,
    AccountRestoreSerializer,
    ProfileUpdateSerializer,
    InitiateRegistrationSerializer,
    CompleteRegistrationSerializer,
    SocialAuthSerializer,
    LoginSerializer,
    VerifyEmailChangeSerializer,
    ResendEmailChangeOTPSerializer,
)
import logging
logger = logging.getLogger(__name__)
from apps.accounts.utils.send_otp_email import send_otp_email
from django.conf import settings
from apps.core.utils.mixins import BaseResponseMixin
from apps.notification.services.notification_service import NotificationService


User = get_user_model()


class InitiateRegistrationView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = InitiateRegistrationSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            # Handle basic validation errors (like invalid email format)
            return self.success_response(
                data={"email": request.data.get("email", ""), "is_sent": False},
                message="Invalid email format.",
                status_code=status.HTTP_200_OK,
            )

        email = serializer.validated_data["email"]
        user, message = serializer.send_registration_otp(email)

        if user is None:
            # User already exists
            return self.success_response(
                data={"email": email, "is_sent": False},
                message=message,
                status_code=status.HTTP_200_OK,
            )

        # Success case
        return self.success_response(
            data={"email": email, "user_id": user.id, "is_sent": True},
            message=message,
            status_code=status.HTTP_200_OK,
        )


class CompleteRegistrationView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = CompleteRegistrationSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return self.success_response(
            data={
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "email": user.email,
                },
            },
            message="Registration completed successfully. You are now logged in.",
            status_code=status.HTTP_201_CREATED,
        )


class RegisterView(BaseResponseMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return self.success_response(
            data={"email": user.email},
            message="Registration successful. Please check your email for verification code.",
            status_code=status.HTTP_201_CREATED,
        )


class VerifyEmailView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Email verified successfully",
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.send_otp()

        return self.success_response(message="OTP has been sent to your email")


class LoginView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        user = authenticate(username=email, password=password)

        if user is not None:
            if not user.is_active:
                return self.error_response(
                    message="Please verify your email before logging in",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            refresh = RefreshToken.for_user(user)
            return self.success_response(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "email": user.email,
                    },
                },
                message="Login successful",
            )
        else:
            return self.error_response(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return self.error_response(
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return self.success_response(
                message="Logged out successfully", status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return self.error_response(
                message="Invalid or expired refresh token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetRequestView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        serializer.send_reset_otp(email)

        return self.success_response(
            message="If the email exists, a password reset OTP has been sent",
            status_code=status.HTTP_200_OK,
        )


class PasswordResetOTPVerifyView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetOTPVerifySerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.success_response(
            data={"email": serializer.validated_data["email"]},
            message="OTP verified successfully",
            status_code=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.success_response(
            message="Password has been reset successfully",
            status_code=status.HTTP_200_OK,
        )


class ChangePasswordView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not check_password(old_password, user.password):
            return self.error_response(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return self.success_response(message="Password changed successfully")


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_CALLBACK_URL


class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.APPLE_CALLBACK_URL


class AccountSoftDeleteView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = AccountSoftDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.soft_delete()

        return self.success_response(
            message="Account has been deactivated successfully"
        )


class AccountRestoreView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        serializer = AccountRestoreSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Invalid data provided",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.user
        user.restore()

        return self.success_response(
            data={"email": user.email}, message="Account restored successfully"
        )


class VerifyEmailChangeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VerifyEmailChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Email successfully updated."}, status=status.HTTP_200_OK
        )


class SocialAuthView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = SocialAuthSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.create_or_login_user()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return self.success_response(
            data={
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "email": user.email,
                    "name": user.profile.name if hasattr(user, "profile") else "",
                    "social_auth_provider": user.social_auth_provider,  # Include provider info
                },
            },
            message="Login successful",
            status_code=status.HTTP_200_OK,
        )


class ProfileUpdateView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request):
        """Get current profile data"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile)

            # Include current user email in response
            data = serializer.data
            data["email"] = request.user.email

            return self.success_response(
                data=data, message="Profile retrieved successfully" 
            )

        except Exception as e:
            return self.handle_exception(e)

    def put(self, request):
        """Update profile - full update"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile, data=request.data, partial=False)

            if serializer.is_valid():
                updated_profile = serializer.save()
                print("🔥 NOTIFICATION BLOCK REACHED", flush=True)
                 # ─── Notification with logging ────────────────────────────
                try:
                    logger.info(f"📱 Sending profile update notification to user {request.user.id} ({request.user.email})")
                    
                    NotificationService.send_notification(
                        user_id=request.user.id,
                        title="Profile Updated!",
                        message="Your profile was just updated. Keep shining!",
                        notification_types=['push', 'in_app'],
                        data={"action": "profile_update"}
                    )
                    print("✅ NOTIFICATION SENT", flush=True)
                    
                    logger.info(f"✅ Notification sent successfully to user {request.user.id}")
                    
                except Exception as notif_error:
                    # Don't break profile update if notification fails
                    print(f"❌ NOTIF ERROR: {notif_error}", flush=True)
                    logger.error(f"❌ Notification failed for user {request.user.id}: {str(notif_error)}")
                # ────────────────────────────

                if (
                # Check if email change was requested
                    "email" in request.data
                    and request.data["email"] != request.user.email
                ):
                    return self.success_response(
                        data={
                            "profile": self.get_serializer(updated_profile).data,
                            "email_change_pending": True,
                            "temp_email": updated_profile.temp_email,
                            "current_email": request.user.email,
                        },
                        message="Profile updated. Please verify your new email address.",
                        action_required="EMAIL_VERIFICATION",
                    )
                

                # Regular profile update
                response_data = self.get_serializer(updated_profile).data
                response_data["email"] = request.user.email

                return self.success_response(
                    data=response_data, message="Profile updated successfully"
                )

            return self.error_response(
                message="Validation failed",
                error_code="VALIDATION_ERROR",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return self.handle_exception(e)

    def patch(self, request):
        """Update profile - partial update"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            print(f"🔥 SERIALIZER VALID: {serializer.is_valid()}", flush=True)  # add this
            print(f"🔥 ERRORS: {serializer.errors}", flush=True) 

            if serializer.is_valid():
                updated_profile = serializer.save()

                 # ─── Notification with logging ────────────────────────────
                try:
                    logger.info(f"📱 Sending profile update notification to user {request.user.id} ({request.user.email})")
                    
                    NotificationService.send_notification(
                        user_id=request.user.id,
                        title="Profile Updated!",
                        message="Your profile was just updated. Keep shining!",
                        notification_types=['push'],
                        data={"action": "profile_update"}
                    )
                    
                    logger.info(f"✅ Notification sent successfully to user {request.user.id}")
                    
                except Exception as notif_error:
                    # Don't break profile update if notification fails
                    logger.error(f"❌ Notification failed for user {request.user.id}: {str(notif_error)}")
                # ─────────────────────────────────────────────────────────


                # Check if email change was requested
                if (
                    "email" in request.data
                    and request.data["email"] != request.user.email
                ):
                    return self.success_response(
                        data={
                            "profile": self.get_serializer(updated_profile).data,
                            "email_change_pending": True,
                            "temp_email": updated_profile.temp_email,
                            "current_email": request.user.email,
                        },
                        message="Profile updated. Please verify your new email address.",
                        action_required="EMAIL_VERIFICATION",
                    )

                # Regular profile update
                response_data = self.get_serializer(updated_profile).data
                response_data["email"] = request.user.email

                return self.success_response(
                    data=response_data, message="Profile updated successfully"
                )

            return self.error_response(
                message="Validation failed",
                error_code="VALIDATION_ERROR",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return self.handle_exception(e)


class VerifyEmailChangeView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyEmailChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_code = serializer.validated_data["otp"]

        try:
            try:
                otp = OTP.objects.get(
                    user=request.user,
                    otp=otp_code,
                    purpose="email_change",
                    is_used=False,
                )

                if not otp.is_valid():
                    return self.bad_request_response(
                        message="OTP is invalid or expired", error_code="INVALID_OTP"
                    )

                # Get profile and update email
                profile = request.user.profile
                if not profile.temp_email:
                    return self.bad_request_response(
                        message="No pending email change found",
                        error_code="NO_PENDING_EMAIL_CHANGE",
                    )

                old_email = request.user.email
                new_email = profile.temp_email

                # Update user email
                request.user.email = new_email
                request.user.save()

                # Clear temp email
                profile.temp_email = None
                profile.save()

                # Mark OTP as used
                otp.is_used = True
                otp.save()

                return self.success_response(
                    data={
                        "old_email": old_email,
                        "new_email": new_email,
                        "email_changed": True,
                    },
                    message="Email changed successfully",
                )

            except OTP.DoesNotExist:
                return self.bad_request_response(
                    message="Invalid OTP", error_code="INVALID_OTP"
                )

        except Exception as e:
            return self.handle_exception(e)


class ResendEmailChangeOTPView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResendEmailChangeOTPSerializer

    def post(self, request):
        try:
            profile = request.user.profile

            if not profile.temp_email:
                return self.bad_request_response(
                    message="No pending email change found",
                )

            # Invalidate old OTPs
            OTP.objects.filter(
                user=request.user, purpose="email_change", is_used=False
            ).update(is_used=True)

            # Generate new OTP
            otp_code = str(random.randint(1000, 9999))
            OTP.objects.create(
                user=request.user,
                otp=otp_code,
                purpose="email_change",
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_otp_email(profile.user, otp_code, "email_change", to_email=profile.temp_email)


            return self.success_response(
                data={"temp_email": profile.temp_email, "otp_sent": True},
                message="OTP sent to your new email address",
            )

        except Exception as e:
            return self.handle_exception(e)


class CancelEmailChangeView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profile

            if not profile.temp_email:
                return self.bad_request_response(
                    message="No pending email change found",
                )

            # Clear temp email
            profile.temp_email = None
            profile.save()

            # Invalidate OTPs
            OTP.objects.filter(
                user=request.user, purpose="email_change", is_used=False
            ).update(is_used=True)

            return self.success_response(message="Email change cancelled successfully")

        except Exception as e:
            return self.handle_exception(e)


class ParmanentAccountDeleteView(BaseResponseMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = ParmanentAccountDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.delete()

        return self.success_response(
            message="Account has been deleted successfully"
        )
    