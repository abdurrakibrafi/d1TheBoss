import random
import requests
from datetime import date, timedelta
from django.utils import timezone
from apps.onboarding.models import (
    Denomination, BibleVersion, JourneyReason, 
    FaithGoal, TonePreference, BibleFamiliarity, BibleVersionOption
)
from django.conf import settings
from apps.homepage.models import DailyVerse

class UserPreferenceService:
    """Service to handle user preference data"""
    
    def __init__(self, user):
        self.user = user
    
    def get_preferences(self):
        """Get all user preferences from onboarding data"""
        return {
            'journey_reason': self._get_journey_reason(),
            'faith_goals': self._get_faith_goals(),
            'tone_preference': self._get_tone_preference(),
            'bible_familiarity': self._get_bible_familiarity(),
            'bible_version': self._get_bible_version()
        }
    
    def _get_journey_reason(self):
        try:
            journey = JourneyReason.objects.filter(user=self.user).first()
            return journey.journey_reason.option if journey and journey.journey_reason else None
        except:
            return None
    
    def _get_faith_goals(self):
        try:
            faith_goals = FaithGoal.objects.filter(user=self.user)
            return [
                fg.text or (fg.faith_goal_option.option if fg.faith_goal_option else None)
                for fg in faith_goals
            ]
        except:
            return []
    
    def _get_tone_preference(self):
        try:
            tone_pref = TonePreference.objects.filter(user=self.user).first()
            return tone_pref.tone_preference_option.name if tone_pref and tone_pref.tone_preference_option else None
        except:
            return None
    
    def _get_bible_familiarity(self):
        try:
            bible_fam = BibleFamiliarity.objects.filter(user=self.user).first()
            return bible_fam.bible_familiarity_option.label if bible_fam and bible_fam.bible_familiarity_option else None
        except:
            return None
    
    def _get_bible_version(self):
        try:
            user_bible = BibleVersion.objects.filter(user=self.user).first()
            return user_bible.bible_version_option if user_bible and user_bible.bible_version_option else None
        except:
            return None


class BibleAPIService:
    """Service to handle Bible API interactions"""
    
    def __init__(self, api_key=None):
        self.api_key = settings.BIBLE_API_KEY  # Replace with your actual API key
        self.base_url = "https://api.scripture.api.bible/v1"
    
    def get_random_verse_dynamically(self, bible_version, user_preferences=None):
        """Get completely random verse from any book/chapter"""
        try:
            books = self._get_all_books(bible_version)
            if not books:
                return self._get_emergency_fallback()
            selected_books = self._filter_books_by_preference(books, user_preferences)
            random_book = random.choice(selected_books)
            chapters = self._get_chapters(bible_version, random_book['id'])
            if not chapters:
                return self._get_emergency_fallback()
            random_chapter = random.choice(chapters)
            verses = self._get_chapter_verses(bible_version, random_chapter['id'])
            if not verses:
                return self._get_emergency_fallback()
            random_verse = random.choice(verses)
            return self._get_verse_content(bible_version, random_verse['id'])
            
        except Exception as e:
            print(f"Error getting dynamic verse: {e}")
            return self._get_emergency_fallback()
    
    def _get_all_books(self, bible_version):
        """Get all books from Bible API"""
        try:
            url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/books"
            headers = {'api-key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            print(f"Error getting books: {e}")
        return []
    
    def _filter_books_by_preference(self, books, preferences):
        """Filter books based on user preferences"""
        if not preferences:
            return books
        comfort_books = ['PSA', 'ISA', 'JHN', 'ROM', 'PHP', '1PE', '2CO']
        wisdom_books = ['PRO', 'ECC', 'JOB', 'JAM']
        new_testament = ['MAT', 'MAR', 'LUK', 'JHN', 'ACT', 'ROM', 'GAL', 'EPH', 'PHP', 'COL', '1TH', '2TH']
        
        journey_reason = preferences.get('journey_reason', '').lower() if preferences.get('journey_reason') else ''
        bible_familiarity = preferences.get('bible_familiarity', '').lower() if preferences.get('bible_familiarity') else ''
        
        preferred_books = []
        if 'comfort' in journey_reason:
            preferred_books.extend(comfort_books)
        elif 'wisdom' in journey_reason or 'guidance' in journey_reason:
            preferred_books.extend(wisdom_books)
        if 'beginner' in bible_familiarity:
            preferred_books.extend(new_testament[:4])  # Gospels for beginners
        if preferred_books:
            filtered = [book for book in books if book.get('abbreviation') in preferred_books]
            return filtered if filtered else books
        
        return books
    
    def _get_chapters(self, bible_version, book_id):
        """Get chapters for a book"""
        try:
            url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/books/{book_id}/chapters"
            headers = {'api-key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                chapters = response.json().get('data', [])
                return [ch for ch in chapters if not ch.get('number', '').startswith('intro')]
        except Exception as e:
            print(f"Error getting chapters: {e}")
        return []
    
    def _get_chapter_verses(self, bible_version, chapter_id):
        """Get verses from a chapter"""
        try:
            url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/chapters/{chapter_id}/verses"
            headers = {'api-key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                verses = response.json().get('data', [])
                return verses[:50] if len(verses) > 50 else verses
        except Exception as e:
            print(f"Error getting verses: {e}")
        return []
    
    def _get_verse_content(self, bible_version, verse_id):
        """Get actual verse content"""
        try:
            url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/verses/{verse_id}"
            headers = {'api-key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'verse_id': verse_id,
                    'verse_text': self._clean_verse_text(data.get('content', '')),
                    'verse_reference': data.get('reference', 'Unknown'),
                }
        except Exception as e:
            print(f"Error getting verse content: {e}")
        
        raise Exception("Failed to get verse content")
    
    def _clean_verse_text(self, text):
        """Clean verse text from HTML tags and extra formatting"""
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = ' '.join(clean_text.split())
        return clean_text.strip()
    
    def _get_emergency_fallback(self):
        """Emergency fallback when everything fails"""
        fallback_verses = [
            {
                'verse_id': 'emergency_1',
                'verse_text': 'For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, to give you hope and a future.',
                'verse_reference': 'Jeremiah 29:11',
            },
            {
                'verse_id': 'emergency_2',
                'verse_text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
                'verse_reference': 'John 3:16',
            },
            {
                'verse_id': 'emergency_3',
                'verse_text': 'And we know that in all things God works for the good of those who love him, who have been called according to his purpose.',
                'verse_reference': 'Romans 8:28',
            }
        ]
        return random.choice(fallback_verses)


class DailyVerseService:
    """Main service to manage daily verses"""
    
    def __init__(self, user):
        self.user = user
        self.preference_service = UserPreferenceService(user)
        self.bible_api = BibleAPIService()
    
    def get_daily_verse(self):
        """Get or create daily verse for user - SAME verse for 24 hours"""
        existing_verse = self._get_current_valid_verse()
        if existing_verse:
            return existing_verse
        return self._generate_new_dynamic_verse()
    
    def _get_current_valid_verse(self):
        """Get user's current verse if still valid (within 24 hours)"""
        return DailyVerse.objects.filter(
            user=self.user,
            expires_at__gt=timezone.now()  # Not expired
        ).first()
    
    def _generate_new_dynamic_verse(self):
        """Generate completely new dynamic verse"""
        preferences = self.preference_service.get_preferences()
        bible_version = preferences.get('bible_version') or self._get_default_bible_version()
        verse_data = self.bible_api.get_random_verse_dynamically(bible_version, preferences)
        DailyVerse.objects.filter(user=self.user).delete()
        return DailyVerse.objects.create(
            user=self.user,
            verse_id=verse_data['verse_id'],
            verse_text=verse_data['verse_text'],
            verse_reference=verse_data['verse_reference'],
            bible_version=bible_version,
            expires_at=timezone.now() + timedelta(hours=24)
        )
    
    def _get_default_bible_version(self):
        """Get default bible version if user doesn't have preference"""
        return BibleVersionOption.objects.filter(is_active=True).first()
    
    def force_refresh_verse(self):
        """Force generate new verse (delete current and create new)"""
        DailyVerse.objects.filter(user=self.user).delete()
        return self._generate_new_dynamic_verse()