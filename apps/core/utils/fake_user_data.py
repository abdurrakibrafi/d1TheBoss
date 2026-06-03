from faker import Faker
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
import random
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
fake = Faker()


class FakeDataGenerator:
    """
    Generate fake data for testing and development
    """

    @staticmethod
    def create_fake_users(count=10):
        """
        Create fake users with profiles
        """
        users_created = []

        for i in range(count):
            email = fake.email()
            password = "password123"  # Simple password for testing
            user = User.objects.create_user(
                email=email,
                password=password,
                is_active=True,  # Skip OTP verification
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            profile = user.profile
            profile.name = f"{user.first_name} {user.last_name}"
            profile.phone = fake.phone_number()[:15]  # Limit to 15 chars
            profile.date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=80)
            profile.gender = random.choice(
                ["male", "female", "other", "prefer_not_to_say"]
            )
            profile.bio = fake.text(max_nb_chars=200)
            profile.motivational_quote = fake.sentence(nb_words=10)
            profile.profile_completed = random.choice([True, False])
            profile.save()

            users_created.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "name": profile.name,
                    "password": password,  # Include for easy testing
                }
            )

        return users_created

    @staticmethod
    def create_admin_user():
        """
        Create an admin user
        """
        email = "admin@example.com"
        password = "admin123"
        if User.objects.filter(email=email).exists():
            return {"message": "Admin user already exists", "email": email}

        admin_user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name="Admin",
            last_name="User",
            is_active=True,
        )
        profile = admin_user.profile
        profile.name = "Admin User"
        profile.phone = "+1234567890"
        profile.bio = "System Administrator"
        profile.profile_completed = True
        profile.save()

        return {
            "id": admin_user.id,
            "email": admin_user.email,
            "password": password,
            "message": "Admin user created successfully",
        }

    @staticmethod
    def create_test_users():
        """
        Create specific test users with known credentials
        """
        test_users_data = [
            {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
                "phone": "+1234567890",
                "gender": "male",
                "bio": "Software Developer from New York",
            },
            {
                "email": "jane.smith@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "name": "Jane Smith",
                "phone": "+1234567891",
                "gender": "female",
                "bio": "UX Designer from California",
            },
            {
                "email": "alex.johnson@example.com",
                "first_name": "Alex",
                "last_name": "Johnson",
                "name": "Alex Johnson",
                "phone": "+1234567892",
                "gender": "other",
                "bio": "Product Manager from Texas",
            },
        ]

        created_users = []
        password = "testuser123"

        for user_data in test_users_data:
            if User.objects.filter(email=user_data["email"]).exists():
                continue

            user = User.objects.create_user(
                email=user_data["email"],
                password=password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
            )
            profile = user.profile
            profile.name = user_data["name"]
            profile.phone = user_data["phone"]
            profile.gender = user_data["gender"]
            profile.bio = user_data["bio"]
            profile.date_of_birth = fake.date_of_birth(minimum_age=25, maximum_age=40)
            profile.motivational_quote = fake.sentence(nb_words=8)
            profile.profile_completed = True
            profile.save()

            created_users.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "password": password,
                    "name": profile.name,
                }
            )

        return created_users

    @staticmethod
    def clear_all_users():
        """
        Delete all users (except superusers for safety)
        """
        deleted_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        return {"deleted_users": deleted_count}

    @staticmethod
    def get_users_summary():
        """
        Get summary of existing users
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(is_superuser=True).count()
        deleted_users = User.objects.filter(is_deleted=True).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "deleted_users": deleted_users,
            "regular_users": total_users - admin_users,
        }
