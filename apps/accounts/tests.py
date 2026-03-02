from django.test import TestCase
from unittest.mock import patch, ANY
from types import SimpleNamespace

from apps.accounts.utils.send_otp_email import send_otp_email


# Create your tests here.


def _make_user(email, name="Test User"):
    # simple object mimicking required attributes
    user = SimpleNamespace()
    user.email = email
    user.profile = SimpleNamespace(name=name)
    return user


class SendOTPEmailTests(TestCase):
    @patch("apps.accounts.utils.send_otp_email.BrevoEmailService")
    def test_default_recipient(self, mock_service_cls):
        mock_service = mock_service_cls.return_value
        # call the helper
        user = _make_user("user@example.com", name="Alice")
        send_otp_email(user, "0000", "verification")
        mock_service.send_transactional_email.assert_called_once_with(
            to_email="user@example.com",
            to_name="Alice",
            subject="Verification Code",
            html_content=ANY,
            text_content=ANY,
        )

    @patch("apps.accounts.utils.send_otp_email.BrevoEmailService")
    def test_override_recipient(self, mock_service_cls):
        mock_service = mock_service_cls.return_value
        user = _make_user("user@example.com", name="Bob")
        send_otp_email(user, "1234", "password_reset", to_email="other@domain.com")
        mock_service.send_transactional_email.assert_called_once_with(
            to_email="other@domain.com",
            to_name="Bob",
            subject="Password Reset Code",
            html_content=ANY,
            text_content=ANY,
        )

    def test_profile_update_email_change_triggers_otp(self):
        # ensure serializer invokes send_otp_email with the temp address
        from apps.accounts.serializers import ProfileUpdateSerializer
        from apps.accounts.models import UserProfile
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create(email="orig@example.com")
        profile = UserProfile.objects.create(user=user)
        data = {"email": "new@example.com"}
        serializer = ProfileUpdateSerializer(instance=profile, data=data, context={"request": None}, partial=True)
        assert serializer.is_valid(), serializer.errors
        with patch("apps.accounts.serializers.send_otp_email") as mock_send:
            serializer.save()
            mock_send.assert_called_once()
            called_args, called_kwargs = mock_send.call_args
            assert called_kwargs.get("to_email") == "new@example.com"
