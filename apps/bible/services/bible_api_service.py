import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from apps.bible.models import (
    BibleVersionCache,
    Book,
    Chapter,
    Verse,
)

class BibleAPIService:
    BASE_URL = "https://api.scripture.api.bible/v1"

    def __init__(self):
        self.api_key = settings.BIBLE_API_KEY
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    # -------------------- Public API Methods --------------------

    def get_bible_versions(self):
        """Fetch and cache Bible versions from API.Bible"""
        cache_key = "bible_versions"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(f"{self.BASE_URL}/bibles", headers=self.headers)
            response.raise_for_status()
            data = response.json().get("data", [])
            cache.set(cache_key, data, 60 * 60 * 24)  # 24 hours
            self._update_bible_versions(data)
            return data
        except requests.RequestException as e:
            print(f"Error fetching Bible versions: {e}")
            return []

    def get_books(self, bible_id):
        """Fetch books for a specific Bible version"""
        cache_key = f"books_{bible_id}"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(
                f"{self.BASE_URL}/bibles/{bible_id}/books", headers=self.headers
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            cache.set(cache_key, data, 60 * 60 * 24)  # 24 hours
            self._update_books(bible_id, data)
            return data
        except requests.RequestException as e:
            print(f"Error fetching books: {e}")
            return []

    def get_chapters(self, bible_id, book_id):
        """Fetch chapters for a specific book"""
        cache_key = f"chapters_{bible_id}_{book_id}"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(
                f"{self.BASE_URL}/bibles/{bible_id}/books/{book_id}/chapters",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            cache.set(cache_key, data, 60 * 60 * 12)  # 12 hours
            return data
        except requests.RequestException as e:
            print(f"Error fetching chapters: {e}")
            return []

    def get_chapter_content(self, bible_id, chapter_id):
        """Fetch chapter content with verses"""
        cache_key = f"chapter_content_{bible_id}_{chapter_id}"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(
                f"{self.BASE_URL}/bibles/{bible_id}/chapters/{chapter_id}",
                headers=self.headers,
                params={
                    "content-type": "json",
                    "include-notes": "false",
                    "include-titles": "true",
                },
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            cache.set(cache_key, data, 60 * 60 * 6)  # 6 hours
            self._update_chapter_content(bible_id, chapter_id, data)
            return data
        except requests.RequestException as e:
            print(f"Error fetching chapter content: {e}")
            return None

    def get_audio_chapter(self, audio_bible_id, chapter_id):
        """Fetch audio for a chapter"""
        cache_key = f"audio_chapter_{audio_bible_id}_{chapter_id}"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(
                f"{self.BASE_URL}/audio-bibles/{audio_bible_id}/chapters/{chapter_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            cache.set(cache_key, data, 60 * 60 * 24)  # 24 hours
            return data
        except requests.RequestException as e:
            print(f"Error fetching audio: {e}")
            return None

    def search_verses(self, bible_id, query, limit=50):
        """Search verses in a Bible version"""
        cache_key = f"search_{bible_id}_{query}_{limit}"
        data = cache.get(cache_key)
        if data:
            return data

        try:
            response = requests.get(
                f"{self.BASE_URL}/bibles/{bible_id}/search",
                headers=self.headers,
                params={"query": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            cache.set(cache_key, data, 60 * 30)  # 30 minutes
            return data
        except requests.RequestException as e:
            print(f"Error searching verses: {e}")
            return []

    # -------------------- Private Helper Methods --------------------

    def _update_bible_versions(self, data):
        """Update database with Bible versions from API"""
        for item in data:
            BibleVersionCache.objects.update_or_create(
                api_bible_id=item["id"],
                defaults={
                    "name": item["name"],
                    "abbreviation": item["abbreviation"],
                    "description": item.get("description", ""),
                    "language_code": item.get("language", {}).get("id", "en"),
                    "is_audio_available": "audioId" in item,
                    "audio_bible_id": item.get("audioId", ""),
                },
            )

    def _update_books(self, bible_id, data):
        """Update database with books from API"""
        try:
            bible_version = BibleVersionCache.objects.get(api_bible_id=bible_id)
            for item in data:
                Book.objects.update_or_create(
                    api_bible_id=item["id"],
                    bible_version=bible_version,
                    defaults={
                        "name": item["name"],
                        "abbreviation": item["abbreviation"],
                        "order": item.get("order", 0),
                        "testament": "NEW" if item.get("order", 0) > 39 else "OLD",
                        "chapter_count": len(item.get("chapters", [])),
                    },
                )
        except BibleVersionCache.DoesNotExist:
            print(f"Bible version {bible_id} not found in database")

    def _update_chapter_content(self, bible_id, chapter_id, data):
        """Update database with chapter content and verses"""
        try:
            chapter = Chapter.objects.get(api_bible_id=chapter_id)
            chapter.audio_url = data.get("audio", {}).get("url", "")
            chapter.audio_duration = data.get("audio", {}).get("duration", 0)
            chapter.content_cached = True
            chapter.cache_updated_at = timezone.now()
            chapter.save()

            verses_data = data.get("content", [])
            for verse_data in verses_data:
                if verse_data.get("type") == "verse":
                    Verse.objects.update_or_create(
                        api_bible_id=verse_data["id"],
                        chapter=chapter,
                        defaults={
                            "number": verse_data.get("number", 1),
                            "content": verse_data.get("text", ""),
                            "audio_start_time": verse_data.get("audio", {}).get("start", 0),
                            "audio_end_time": verse_data.get("audio", {}).get("end", 0),
                        },
                    )
        except Chapter.DoesNotExist:
            print(f"Chapter {chapter_id} not found in database")