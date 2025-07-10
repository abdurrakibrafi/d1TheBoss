# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


# Core Bible Data Serializers
class BibleVersionCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleVersionCache
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class ChapterSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name', read_only=True)
    
    class Meta:
        model = Chapter
        fields = '__all__'


class VerseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verse
        fields = '__all__'


# Nested serializers for complex responses
class ChapterWithVersesSerializer(serializers.ModelSerializer):
    verses = VerseSerializer(many=True, read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    
    class Meta:
        model = Chapter
        fields = '__all__'


class BookWithChaptersSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    
    class Meta:
        model = Book
        fields = '__all__'


# User Profile Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# Reading Progress Serializers
class ReadingProgressSerializer(serializers.ModelSerializer):
    bible_version_name = serializers.CharField(source='bible_version.name', read_only=True)
    book_name = serializers.CharField(source='current_book.name', read_only=True)
    chapter_number = serializers.IntegerField(source='current_chapter.number', read_only=True)
    
    class Meta:
        model = ReadingProgress
        fields = '__all__'


# Bookmark Serializers
class BookmarkSerializer(serializers.ModelSerializer):
    verse_reference = serializers.SerializerMethodField()
    verse_content = serializers.CharField(source='verse.content', read_only=True)
    
    class Meta:
        model = Bookmark
        fields = '__all__'
        
    def get_verse_reference(self, obj):
        return f"{obj.verse.chapter.book.name} {obj.verse.chapter.number}:{obj.verse.number}"


# Audio Serializers
class AudioSessionSerializer(serializers.ModelSerializer):
    chapter_reference = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioSession
        fields = '__all__'
        
    def get_chapter_reference(self, obj):
        return f"{obj.chapter.book.name} {obj.chapter.number}"


class PlaybackStateSerializer(serializers.ModelSerializer):
    chapter_reference = serializers.SerializerMethodField()
    
    class Meta:
        model = PlaybackState
        fields = '__all__'
        
    def get_chapter_reference(self, obj):
        if obj.current_chapter:
            return f"{obj.current_chapter.book.name} {obj.current_chapter.number}"
        return None


# Search Serializers
class SearchHistorySerializer(serializers.ModelSerializer):
    bible_version_name = serializers.CharField(source='bible_version.name', read_only=True)
    
    class Meta:
        model = SearchHistory
        fields = '__all__'


# Reading Plan Serializers
class ReadingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingPlan
        fields = '__all__'


class UserReadingPlanSerializer(serializers.ModelSerializer):
    reading_plan_name = serializers.CharField(source='reading_plan.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserReadingPlan
        fields = '__all__'
        
    def get_progress_percentage(self, obj):
        return round((obj.current_day / obj.reading_plan.duration_days) * 100, 1)


# API Cache Serializer
class APICacheSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = APICache
        fields = '__all__'


# Custom serializers for specific API responses
class BibleVersionCacheListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for bible version selection"""
    class Meta:
        model = BibleVersionCache
        fields = ['id', 'api_bible_id', 'name', 'abbreviation', 'is_audio_available']


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book selection"""
    class Meta:
        model = Book
        fields = ['id', 'api_bible_id', 'name', 'abbreviation', 'testament', 'chapter_count']


class ChapterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chapter selection"""
    class Meta:
        model = Chapter
        fields = ['id', 'api_bible_id', 'number', 'title', 'verse_count', 'audio_url']


# Validation helpers
class CreateBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ['verse', 'note', 'color']
        
    def validate(self, data):
        user = self.context['request'].user
        verse = data['verse']
        
        if Bookmark.objects.filter(user=user, verse=verse).exists():
            raise serializers.ValidationError("You already bookmarked this verse.")
        
        return data


class UpdateReadingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingProgress
        fields = ['current_book', 'current_chapter', 'current_verse', 'audio_position', 'is_audio_mode']
        
    def validate(self, data):
        # Ensure chapter belongs to book
        if 'current_chapter' in data and 'current_book' in data:
            if data['current_chapter'].book != data['current_book']:
                raise serializers.ValidationError("Chapter must belong to the selected book.")
        
        # Ensure verse belongs to chapter
        if 'current_verse' in data and 'current_chapter' in data:
            if data['current_verse'] and data['current_verse'].chapter != data['current_chapter']:
                raise serializers.ValidationError("Verse must belong to the selected chapter.")
        
        return data