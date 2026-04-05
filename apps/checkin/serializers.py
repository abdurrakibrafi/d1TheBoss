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


from rest_framework import serializers
from .models import BadgeTemplate, UserBadge

class BadgeTemplateSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = BadgeTemplate
        fields = ['id', 'badge_type', 'title', 'description', 'image', 'order', 'weeks_required']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
class UserAppBadgeSerializer(serializers.ModelSerializer):
    badge_template = BadgeTemplateSerializer(read_only=True)
    
    class Meta:
        model = UserAppBadge
        fields = ['id', 'badge_template', 'earned_at']