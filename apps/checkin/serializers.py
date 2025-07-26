from rest_framework import serializers
from apps.checkin.models import *

class DailyCheckinSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCheckin
        fields = ['checkin_date', 'streak_day', 'created_at']

class UserStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreak
        fields = ['current_streak', 'longest_streak', 'last_checkin_date']

class UserBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBadge
        fields = ['weeks_completed', 'badge_name', 'earned_date']

class WeeklyCheckinOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyCheckinOption
        fields = ['id', 'option_text', 'option_order']

class WeeklyCheckinQuestionSerializer(serializers.ModelSerializer):
    options = WeeklyCheckinOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = WeeklyCheckinQuestion
        fields = ['id', 'question_text', 'question_order', 'options']

class WeeklyCheckinResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWeeklyCheckinResponse
        fields = ['question', 'selected_option']


# class NotificationSettingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NotificationSetting
#         fields = '__all__'