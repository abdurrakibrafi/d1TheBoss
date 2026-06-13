from rest_framework import serializers
from apps.homepage.models import DailyVerse, JourneyVerse

class DailyVerseSerializer(serializers.ModelSerializer):
    bible_version_title = serializers.CharField(
        source='bible_version.title', 
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyVerse
        fields = [
            'id',
            'verse_id',
            'verse_text', 
            'verse_reference',
            'bible_version_title',
            'date_assigned',
            'expires_at',
            'is_expired'
        ]
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    

class JourneyVerseSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyVerse
        fields = ['day_number', 'title', 'verse_text', 'verse_reference']