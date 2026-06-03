from rest_framework import serializers
from apps.onboarding.models import (
    JourneyReasonOption,
    JourneyReason,
    DenominationOption,
    Denomination,
    FaithGoalQuestion,
    FaithGoalOption,
    FaithGoal,
    TonePreferenceOption,
    TonePreference,
    BibleFamiliarityOption,
    BibleFamiliarity,
    BibleVersionOption,
    BibleVersion,
    UserGoalPreference
)
from apps.accounts.models import UserProfile


class JourneyReasonOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyReasonOption
        fields = ["id", "option", "is_active", "is_selected"]


class DenominationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenominationOption
        fields = ["id", "name", "is_active", "is_selected"]


class FaithGoalQuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = FaithGoalQuestion
        fields = ["id", "question", "is_active", "is_selected", "options"]

    def get_options(self, obj):
        options = obj.faithgoaloption_set.filter(is_active=True)
        return FaithGoalOptionSerializer(options, many=True).data


class FaithGoalOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaithGoalOption
        fields = ["id", "option", "is_active", "is_selected"]


class TonePreferenceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TonePreferenceOption
        fields = ["id", "title", "name", "description", "quote", "icon", "is_active", "is_selected"]


class BibleFamiliarityOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleFamiliarityOption
        fields = ["id", "label", "text1", "text2", "title", "name", "caption", "is_active", "is_selected"]


class BibleVersionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleVersionOption
        fields = ["id", "title", "subtitle", "api_bible_id", "is_active", "is_selected"]


class JourneyReasonSerializer(serializers.ModelSerializer):
    journey_reason_detail = JourneyReasonOptionSerializer(
        source="journey_reason", read_only=True
    )

    class Meta:
        model = JourneyReason
        fields = [
            "id",
            "journey_reason",
            "journey_reason_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class DenominationSerializer(serializers.ModelSerializer):
    denomination_detail = DenominationOptionSerializer(
        source="denomination_option", read_only=True
    )

    class Meta:
        model = Denomination
        fields = [
            "id",
            "denomination_option",
            "denomination_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class FaithGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaithGoal
        fields = ["id", "user", "faith_goal_option", "text", "created_at"]
        read_only_fields = ["user", "created_at"]


class BulkFaithGoalSerializer(serializers.Serializer):
    goals = FaithGoalSerializer(many=True)

    def create(self, validated_data):
        goals_data = validated_data["goals"]
        user = self.context["request"].user

        print(f"=== BULK FAITH GOAL SERIALIZER DEBUG ===")
        print(f"User: {user.id}")
        print(f"Goals data: {goals_data}")
        FaithGoal.objects.filter(user=user).delete()
        goals = []
        for goal_data in goals_data:
            goal_data["user"] = user
            goals.append(FaithGoal(**goal_data))

        created_goals = FaithGoal.objects.bulk_create(goals)
        print(f"Created {len(created_goals)} goals")
        saved_goals = FaithGoal.objects.filter(user=user).select_related('faith_goal_option')
        for goal in saved_goals:
            print(f"Saved goal - Option ID: {goal.faith_goal_option.id}, Option: {goal.faith_goal_option.option}, Goal Type: {goal.faith_goal_option.goal_type}")
        try:
            from apps.goal.models import UserGoal
            print("=== CALLING GOAL UPDATE ===")
            goal_updated = UserGoal.update_goal_for_preference_change(user)
            print(f"Goal update result: {goal_updated}")
            if goal_updated[1]:  # If goal was actually updated
                print(f"Goal updated for user {user.id} to {goal_updated[0].goal_type}")
            else:
                print(f"Goal NOT updated - current goal: {goal_updated[0].goal_type if goal_updated[0] else 'None'}")
        except Exception as e:
            print(f"Error updating goal after faith goal save: {str(e)}")
            
        return created_goals
    
class TonePreferenceSerializer(serializers.ModelSerializer):
    tone_preference_detail = TonePreferenceOptionSerializer(
        source="tone_preference_option", read_only=True
    )

    class Meta:
        model = TonePreference
        fields = [
            "id",
            "tone_preference_option",
            "tone_preference_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BibleFamiliaritySerializer(serializers.ModelSerializer):
    bible_familiarity_detail = BibleFamiliarityOptionSerializer(
        source="bible_familiarity_option", read_only=True
    )

    class Meta:
        model = BibleFamiliarity
        fields = [
            "id",
            "bible_familiarity_option",
            "bible_familiarity_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BibleVersionSerializer(serializers.ModelSerializer):
    bible_version_detail = BibleVersionOptionSerializer(
        source="bible_version_option", read_only=True
    )

    class Meta:
        model = BibleVersion
        fields = [
            "id",
            "bible_version_option",
            "bible_version_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class OnboardingOptionsSerializer(serializers.Serializer):
    """All master data in one response for onboarding"""

    journey_reasons = JourneyReasonOptionSerializer(many=True)
    denominations = DenominationOptionSerializer(many=True)
    faith_goal_questions = FaithGoalQuestionSerializer(many=True)
    tone_preferences = TonePreferenceOptionSerializer(many=True)
    bible_familiarity = BibleFamiliarityOptionSerializer(many=True)
    bible_versions = BibleVersionOptionSerializer(many=True)


class UserOnboardingProgressSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "onboarding_step",
            "onboarding_completed",
            "onboarding_completed_at",
            "progress_percentage",
        ]
        read_only_fields = ["onboarding_completed_at"]

    def get_progress_percentage(self, obj):
        total_steps = 7  # Based on your 6 onboarding sections
        return (obj.onboarding_step / total_steps) * 100 if obj.onboarding_step else 0


class UserOnboardingSummarySerializer(serializers.Serializer):
    """Complete user onboarding data for AI context"""

    journey_reason = serializers.SerializerMethodField()
    denomination = serializers.SerializerMethodField()
    faith_goals = serializers.SerializerMethodField()
    tone_preference = serializers.SerializerMethodField()
    bible_familiarity = serializers.SerializerMethodField()
    bible_version = serializers.SerializerMethodField()
    progress = UserOnboardingProgressSerializer(source="profile", read_only=True)

    def get_journey_reason(self, obj):
        journey = JourneyReason.objects.filter(user=obj).first()
        return JourneyReasonSerializer(journey).data if journey else None

    def get_denomination(self, obj):
        denomination = Denomination.objects.filter(user=obj).first()
        return DenominationSerializer(denomination).data if denomination else None

    def get_faith_goals(self, obj):
        goals = FaithGoal.objects.filter(user=obj)
        return FaithGoalSerializer(goals, many=True).data

    def get_tone_preference(self, obj):
        tone = TonePreference.objects.filter(user=obj).first()
        return TonePreferenceSerializer(tone).data if tone else None

    def get_bible_familiarity(self, obj):
        familiarity = BibleFamiliarity.objects.filter(user=obj).first()
        return BibleFamiliaritySerializer(familiarity).data if familiarity else None

    def get_bible_version(self, obj):
        version = BibleVersion.objects.filter(user=obj).first()
        return BibleVersionSerializer(version).data if version else None


class UserGoalPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGoalPreference
        fields = ['goal_type']
        
    def create(self, validated_data):
        user = self.context['request'].user
        goal_preference, created = UserGoalPreference.objects.update_or_create(
            user=user,
            defaults=validated_data
        )
        return goal_preference