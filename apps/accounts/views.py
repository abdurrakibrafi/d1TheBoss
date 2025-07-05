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
from .serializers import (
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
    VerifyEmailChangeSerializer,
    InitiateRegistrationSerializer,
    CompleteRegistrationSerializer,
    SocialAuthSerializer,
    LoginSerializer

)
from django.conf import settings
from apps.core.utils.mixins import BaseResponseMixin


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
                data={
                    "email": request.data.get("email", ""),
                    "is_sent": False
                },
                message="Invalid email format.",
                status_code=status.HTTP_200_OK
            )
        
        email = serializer.validated_data["email"]
        user, message = serializer.send_registration_otp(email)
        
        if user is None:
            # User already exists
            return self.success_response(
                data={
                    "email": email,
                    "is_sent": False
                },
                message=message,
                status_code=status.HTTP_200_OK
            )
        
        # Success case
        return self.success_response(
            data={
                "email": email,
                "user_id": user.id,
                "is_sent": True
            },
            message=message,
            status_code=status.HTTP_200_OK
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
                }
            },
            message="Registration completed successfully. You are now logged in.",
            status_code=status.HTTP_201_CREATED
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
            status_code=status.HTTP_201_CREATED
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

        return self.success_response(
            message="OTP has been sent to your email"
        )

  

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
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)
            return self.success_response(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "email": user.email,
                    }
                },
                message="Login successful"
            )
        else:
            return self.error_response(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
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
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return self.success_response(
                message="Logged out successfully",
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return self.error_response(
                message="Invalid or expired refresh token",
                status_code=status.HTTP_400_BAD_REQUEST
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
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return self.success_response(
            message="Password changed successfully"
        )


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
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.user
        user.restore()

        return self.success_response(
            data={"email": user.email},
            message="Account restored successfully"
        )

class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        instance, email_changed = serializer.save()

        response_data = self.get_serializer(instance).data

        if email_changed:
            response_data["email_verification_pending"] = True
            response_data["message"] = (
                "Profile updated. Please verify your new email address with the code sent."
            )
        else:
            response_data["message"] = "Profile updated successfully."

        return Response(response_data)


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
                    "name": user.profile.name if hasattr(user, 'profile') else '',
                    "social_auth_provider": user.social_auth_provider,  # Include provider info
                }
            },
            message="Login successful",
            status_code=status.HTTP_200_OK
        )