from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
# ... other imports
from .mixins import BaseResponseMixin  # Import your mixin

User = get_user_model()

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
            data={"email": user.email, "user_type": user.user_type},
            message="Registration successful. Please check your email for verification code.",
            status_code=status.HTTP_201_CREATED
        )

class LoginView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return self.error_response(
                message="Email and password are required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

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
                        "user_type": user.user_type
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

class ResendOTPView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        try:
            user = User.objects.get(email=email)

            if purpose == "verification":
                if user.is_active:
                    return self.error_response(
                        message="Email is already verified",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                register_serializer = RegisterSerializer()
                register_serializer.send_verification_otp(user)
            elif purpose == "password_reset":
                reset_serializer = PasswordResetRequestSerializer()
                reset_serializer.send_reset_otp(email)

            return self.success_response(
                message="OTP has been sent to your email"
            )

        except User.DoesNotExist:
            # Return success message for security (don't reveal if email exists)
            return self.success_response(
                message="If the email exists, an OTP has been sent"
            )