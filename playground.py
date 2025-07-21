# services.py (Updated for Dynamic Verses)
import random
import requests
from datetime import date, timedelta
from django.utils import timezone
from .models import DailyVerse, BibleVersion

class BibleAPIService:
    """Service to handle Bible API interactions"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or 'your-bible-api-key'
        self.base_url = "https://api.scripture.api.bible/v1"
    
    def get_random_verse_dynamically(self, bible_version, user_preferences=None):
        """Get completely random verse from any book/chapter"""
        try:
            # First, get all available books
            books = self._get_all_books(bible_version)
            
            # Filter books based on user preferences if needed
            selected_books = self._filter_books_by_preference(books, user_preferences)
            
            # Pick random book
            random_book = random.choice(selected_books)
            
            # Get chapters for that book
            chapters = self._get_chapters(bible_version, random_book['id'])
            
            # Pick random chapter
            random_chapter = random.choice(chapters)
            
            # Get verses from that chapter
            verses = self._get_chapter_verses(bible_version, random_chapter['id'])
            
            # Pick random verse
            random_verse = random.choice(verses)
            
            # Get verse content
            return self._get_verse_content(bible_version, random_verse['id'])
            
        except Exception as e:
            print(f"Error getting dynamic verse: {e}")
            return self._get_emergency_fallback()
    
    def _get_all_books(self, bible_version):
        """Get all books from Bible API"""
        url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/books"
        headers = {'api-key': self.api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    
    def _filter_books_by_preference(self, books, preferences):
        """Filter books based on user preferences"""
        if not preferences:
            return books
        
        # Define book categories
        comfort_books = ['PSA', 'ISA', 'JHN', 'ROM', 'PHP', '1PE', '2CO']
        wisdom_books = ['PRO', 'ECC', 'JOB', 'JAM']
        new_testament = ['MAT', 'MAR', 'LUK', 'JHN', 'ACT', 'ROM', 'GAL', 'EPH', 'PHP', 'COL', '1TH', '2TH']
        
        journey_reason = preferences.get('journey_reason', '').lower()
        bible_familiarity = preferences.get('bible_familiarity', '').lower()
        
        preferred_books = []
        
        # Based on journey reason
        if 'comfort' in journey_reason:
            preferred_books.extend(comfort_books)
        elif 'wisdom' in journey_reason or 'guidance' in journey_reason:
            preferred_books.extend(wisdom_books)
        
        # Based on familiarity
        if 'beginner' in bible_familiarity:
            preferred_books.extend(new_testament[:4])  # Gospels for beginners
        
        # Filter actual books
        if preferred_books:
            filtered = [book for book in books if book.get('abbreviation') in preferred_books]
            return filtered if filtered else books
        
        return books
    
    def _get_chapters(self, bible_version, book_id):
        """Get chapters for a book"""
        url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/books/{book_id}/chapters"
        headers = {'api-key': self.api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            chapters = response.json().get('data', [])
            # Remove intro chapters (they usually don't have verses)
            return [ch for ch in chapters if not ch.get('number', '').startswith('intro')]
        return []
    
    def _get_chapter_verses(self, bible_version, chapter_id):
        """Get verses from a chapter"""
        url = f"{self.base_url}/bibles/{bible_version.api_bible_id}/chapters/{chapter_id}/verses"
        headers = {'api-key': self.api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            verses = response.json().get('data', [])
            # Limit to reasonable verse length (avoid very long verses)
            return verses[:50] if len(verses) > 50 else verses
        return []
    
    def _get_verse_content(self, bible_version, verse_id):
        """Get actual verse content"""
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
        raise Exception("Failed to get verse content")
    
    def _clean_verse_text(self, text):
        """Clean verse text"""
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = ' '.join(clean_text.split())
        return clean_text.strip()
    
    def _get_emergency_fallback(self):
        """Emergency fallback when everything fails"""
        return {
            'verse_id': 'emergency',
            'verse_text': 'For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, to give you hope and a future.',
            'verse_reference': 'Jeremiah 29:11',
        }


class DailyVerseService:
    """Main service to manage daily verses"""
    
    def __init__(self, user):
        self.user = user
        self.preference_service = UserPreferenceService(user)
        self.bible_api = BibleAPIService()
    
    def get_daily_verse(self):
        """Get or create daily verse for user - SAME verse for 24 hours"""
        # Check for existing valid verse (within 24 hours)
        existing_verse = self._get_current_valid_verse()
        if existing_verse:
            return existing_verse
        
        # Generate completely new dynamic verse
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
        
        # Get completely random verse from API
        verse_data = self.bible_api.get_random_verse_dynamically(bible_version, preferences)
        
        # Delete any old verses for this user
        DailyVerse.objects.filter(user=self.user).delete()
        
        # Create new verse record
        return DailyVerse.objects.create(
            user=self.user,
            verse_id=verse_data['verse_id'],
            verse_text=verse_data['verse_text'],
            verse_reference=verse_data['verse_reference'],
            bible_version=bible_version,
            expires_at=timezone.now() + timedelta(hours=24)
        )
    
    def _get_default_bible_version(self):
        """Get default bible version"""
        from .models import BibleVersionOption
        return BibleVersionOption.objects.filter(is_active=True).first()
    

# urls.py
urlpatterns = [
    path('daily-verse/', views.DailyVerseView.as_view(), name='daily-verse'),
]


GET http://localhost:8000/api/daily-verse/
Headers:
Authorization: Bearer your_jwt_token
Content-Type: application/json


{
    "success": true,
    "message": "New daily verse generated",
    "data": {
        "id": 123,
        "verse_id": "ROM.8.28",
        "verse_text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.",
        "verse_reference": "Romans 8:28",
        "bible_version_title": "New International Version",
        "date_assigned": "2025-07-22T14:30:00Z",
        "expires_at": "2025-07-23T14:30:00Z",
        "is_expired": false
    }
}


{
    "success": true,
    "message": "Current daily verse retrieved",
    "data": {
        "id": 123,
        "verse_id": "ROM.8.28",
        "verse_text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.",
        "verse_reference": "Romans 8:28",
        "bible_version_title": "New International Version",
        "date_assigned": "2025-07-22T14:30:00Z",
        "expires_at": "2025-07-23T14:30:00Z",
        "is_expired": false
    }
}


{
    "success": true,
    "message": "New daily verse generated",
    "data": {
        "id": 124,
        "verse_id": "PSA.46.1",
        "verse_text": "God is our refuge and strength, an ever-present help in trouble.",
        "verse_reference": "Psalm 46:1",
        "bible_version_title": "New International Version",
        "date_assigned": "2025-07-23T14:35:00Z",
        "expires_at": "2025-07-24T14:35:00Z",
        "is_expired": false
    }
}


3. Testing Flow in Postman
Test Scenario 1: First Time User

User hits API → Gets new random verse
User hits API again (same day) → Gets same verse
Wait 24 hours → Gets completely new verse

Test Scenario 2: User with Preferences

User completes onboarding (comfort-seeking)
User hits API → Gets verse from comfort-related books (Psalms, Isaiah, etc.)
Next day → Gets different comfort verse

Postman Collection:


{
    "info": {
        "name": "Daily Verse API Tests"
    },
    "item": [
        {
            "name": "Get Daily Verse",
            "request": {
                "method": "GET",
                "header": [
                    {
                        "key": "Authorization",
                        "value": "Bearer {{jwt_token}}"
                    }
                ],
                "url": {
                    "raw": "{{base_url}}/api/daily-verse/",
                    "host": ["{{base_url}}"],
                    "path": ["api", "daily-verse", ""]
                }
            }
        }
    ]
}