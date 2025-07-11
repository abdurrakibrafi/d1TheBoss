from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import random
from .models import OTP, UserProfile
from django.core.mail import send_mail
from django.conf import settings
from apps.accounts.utils.send_otp_email import send_otp_email

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={"input_type": "password"})


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create(
            email=validated_data["email"],
            is_active=False,
        )
        user.set_password(validated_data["password"])
        user.save()

        self.send_verification_otp(user)
        return user

    def send_verification_otp(self, user):
        otp_code = "".join(random.choices("0123456789", k=4))

        otp = OTP.objects.create(
            user=user,
            otp=otp_code,
            purpose="verification",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        send_mail(
            "Verify Your Email",
            f"Your verification code is: {otp_code}. Valid for 10 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return otp


class InitiateRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # Remove the validation error - we'll handle this in the view
        return value

    def send_registration_otp(self, email):
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return None, "User with this email already exists."

        otp_code = "".join(random.choices("0123456789", k=4))

        # Create inactive user first
        user = User.objects.create(
            email=email,
            is_active=False,
        )

        otp = OTP.objects.create(
            user=user,
            otp=otp_code,
            purpose="verification",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        send_otp_email(user, otp_code, "Verification")

        return user, "Verification code sent to your email."


class CompleteRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        email = attrs.get("email")
        otp_code = attrs.get("otp")

        try:
            user = User.objects.get(email=email)

            # SMART CHECK: Look for unused password_setup OTP instead
            password_setup_otp_exists = OTP.objects.filter(
                user=user, purpose="password_setup", is_used=False
            ).exists()

            if not password_setup_otp_exists:
                raise serializers.ValidationError(
                    {
                        "email": "No valid password setup session found. Please verify your email first."
                    }
                )

        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        try:
            otp = OTP.objects.filter(
                user=user, purpose="password_setup", otp=otp_code, is_used=False
            ).latest("created_at")

            if not otp.is_valid():
                raise serializers.ValidationError({"otp": "OTP has expired."})

            attrs["user"] = user
            attrs["otp_object"] = otp
            return attrs

        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

    def save(self):
        user = self.validated_data["user"]
        otp = self.validated_data["otp_object"]
        password = self.validated_data["password"]

        # Mark OTP as used
        otp.is_used = True
        otp.save()

        # Set password
        user.set_password(password)
        user.save()

        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        email = attrs.get("email")
        otp_code = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        try:
            otp = OTP.objects.filter(
                user=user, purpose="verification", otp=otp_code, is_used=False
            ).latest("created_at")

            if not otp.is_valid():
                raise serializers.ValidationError({"otp": "OTP has expired."})

            # Mark verification OTP as used
            otp.is_used = True
            otp.save()

            # Activate user
            user.is_active = True
            user.save()

            # Create password_setup OTP
            OTP.objects.create(
                user=user,
                purpose="password_setup",
                otp=otp_code,  # Reuse same OTP code
                expires_at=otp.expires_at,  # Same expiry
            )

            attrs["user"] = user
            return attrs

        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            pass
        return value

    def send_reset_otp(self, email):
        try:
            user = User.objects.get(email=email)

            otp_code = "".join(random.choices("0123456789", k=4))

            otp = OTP.objects.create(
                user=user,
                otp=otp_code,
                purpose="password_reset",
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_otp_email(user, otp_code, "password_reset")

            return True
        except User.DoesNotExist:
            return True


class PasswordResetOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        email = attrs.get("email")
        otp_code = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        try:
            otp = OTP.objects.filter(
                user=user, purpose="password_reset", otp=otp_code, is_used=False
            ).latest("created_at")

            if not otp.is_valid():
                raise serializers.ValidationError({"otp": "OTP has expired."})

            attrs["user"] = user
            attrs["otp_object"] = otp

            return attrs

        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)
    new_password = serializers.CharField(validators=[validate_password])
    new_password2 = serializers.CharField()

    def validate(self, attrs):
        email = attrs["email"]
        otp_code = attrs["otp"]
        new_password = attrs["new_password"]
        new_password2 = attrs["new_password2"]

        if new_password != new_password2:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email doesn't exist."}
            )

        try:
            otp = OTP.objects.filter(
                user=user, purpose="password_reset", otp=otp_code, is_used=False
            ).latest("created_at")

            if not otp.is_valid():
                raise serializers.ValidationError({"otp": "OTP has expired."})

            otp.is_used = True
            otp.save()

            user.set_password(new_password)
            user.save()

            attrs["user"] = user
            return attrs

        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP"})


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["verification", "password_reset"])

    def validate(self, attrs):
        email = attrs["email"]
        purpose = attrs["purpose"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, pretend success — don't expose info
            attrs["user"] = None
            return attrs

        if purpose == "verification":
            if user.is_active:
                raise serializers.ValidationError("Email is already verified.")
            attrs["user"] = user

        elif purpose == "password_reset":
            attrs["user"] = user

        return attrs

    def send_otp(self):
        user = self.validated_data.get("user")
        purpose = self.validated_data["purpose"]

        if purpose == "verification":
            if user:
                # Mark old OTPs as used
                OTP.objects.filter(
                    user=user, purpose="verification", is_used=False
                ).update(is_used=True)

                otp_code = "".join(random.choices("0123456789", k=4))

                OTP.objects.create(
                    user=user,
                    otp=otp_code,
                    purpose="verification",
                    expires_at=timezone.now() + timedelta(minutes=10),
                )

                send_otp_email(user, otp_code, purpose)

        elif purpose == "password_reset":
            reset_serializer = PasswordResetRequestSerializer()
            reset_serializer.send_reset_otp(user.email)  # assuming method takes email

        return True


class AccountSoftDeleteSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=True)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm to delete your account."
            )
        return value


class AccountRestoreSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(  # Fixed typo here
                {"email": "User with this email does not exist."}
            )
        if not user.is_deleted:
            raise serializers.ValidationError({"email": "This account is not deleted."})
        # Store the user in the serializer for later use
        self.user = user
        return value


from apps.accounts.models import SOCIAL_AUTH_PROVIDERS


class SocialAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    provider = serializers.ChoiceField(choices=SOCIAL_AUTH_PROVIDERS)  # Add validation
    name = serializers.CharField(required=False, allow_blank=True)

    def create_or_login_user(self):
        email = self.validated_data["email"]
        provider = self.validated_data["provider"]
        name = self.validated_data.get("name", "")

        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # User exists, just login
            if not user.is_active:
                user.is_active = True
                user.save()

            # Update provider if not set
            if not user.social_auth_provider:
                user.social_auth_provider = provider
                user.save()

        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                email=email,
                is_active=True,
                social_auth_provider=provider,  # Set provider
            )

        # Update profile with social data
        if name and hasattr(user, "profile"):
            user.profile.name = name
            user.profile.save()

        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    # User fields
    email = serializers.EmailField(required=False)

    # Profile fields
    name = serializers.CharField(max_length=100, required=False)
    date_of_birth = serializers.DateField(required=False)

    profile_picture = serializers.ImageField(required=False, allow_null=True)

    # Add this field to handle image deletion
    remove_profile_picture = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "name",
            "date_of_birth",
            "profile_picture",
            "remove_profile_picture",
        ]

    def validate_profile_picture(self, value):
        if value:
            # Check file size (e.g., max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Image file too large. Maximum size is 5MB."
                )

            # Check file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Only JPEG, PNG, GIF, and WebP images are allowed."
                )

        return value

    def validate_email(self, value):
        user = self.context["request"].user
        if value and value != user.email:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        user = instance.user
        email = validated_data.pop("email", None)
        remove_profile_picture = validated_data.pop("remove_profile_picture", False)

        # Handle profile picture removal
        if remove_profile_picture:
            if instance.profile_picture:
                # Delete the old image file
                instance.profile_picture.delete(save=False)
            instance.profile_picture = None

        # Handle email change separately
        if email and email != user.email:
            # Store new email temporarily
            instance.temp_email = email
            instance.save()

            # Generate OTP for email verification
            otp_code = self.generate_otp()
            OTP.objects.create(
                user=user,
                otp=otp_code,
                purpose="email_change",
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_otp_email(user, otp_code, "email_change", to_email=instance.temp_email)

        # Update other profile fields
        for attr, value in validated_data.items():
            if attr == "profile_picture" and value:
                # Delete old image if exists
                if instance.profile_picture:
                    instance.profile_picture.delete(save=False)
            setattr(instance, attr, value)

        instance.save()
        return instance

    def generate_otp(self):
        return str(random.randint(1000, 9999))

    def to_representation(self, instance):
        """Custom representation to include full image URL"""
        data = super().to_representation(instance)
        request = self.context.get("request")

        if instance.profile_picture and request:
            data["profile_picture"] = request.build_absolute_uri(
                instance.profile_picture.url
            )

        return data


class VerifyEmailChangeSerializer(serializers.Serializer):
    otp = serializers.CharField(
        max_length=4,
        min_length=4,
        required=True,
        help_text="4-digit OTP code sent to your new email address",
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class ResendEmailChangeOTPSerializer(serializers.Serializer):
    # This serializer doesn't need any input fields since it just resends OTP
    # to the temp_email already stored in the user's profile
    pass
