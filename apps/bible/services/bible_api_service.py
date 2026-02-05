# Updated services/bible_api_service.py
import requests
import re
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache


class BibleAPIService:
    def __init__(self):
        self.api_key = settings.BIBLE_API_KEY
        self.base_url = "https://api.scripture.api.bible/v1"
        self.headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # This will be populated from database
        self.available_bibles = self.get_available_bibles_from_db()
    
    def get_available_bibles_from_db(self):
        """Get available Bible versions from database"""
        try:
            from apps.onboarding.models import BibleVersionOption
            active_versions = BibleVersionOption.objects.filter(is_active=True)
            
            bible_dict = {}
            for version in active_versions:
                if version.api_bible_id:
                    bible_dict[version.title] = version.api_bible_id
            
            return bible_dict
        except ImportError:
            # Fallback to hardcoded versions if onboarding app not available
            return {
                'ASV': '06125adad2d5898a-01',
                'ASV-BYZ': '685d1470fe4d5c3b-01',
                'WEB': '72f4e6dc683324df-01',
                'KJV': '2eb94132ad61ae75-01'
            }
    
    def get_bible_versions(self):
        """Get list of available Bible versions from database"""
        print("DEBUG: Starting get_bible_versions")  # Debug log
        
        try:
            from apps.onboarding.models import BibleVersionOption
            print("DEBUG: Successfully imported BibleVersionOption")  # Debug log
            
            cache_key = "bible_versions_from_db"
            cached_versions = cache.get(cache_key)
            
            if cached_versions:
                print("DEBUG: Returning cached versions")  # Debug log
                return cached_versions
            
            print("DEBUG: Querying active versions from DB")  # Debug log
            active_versions = BibleVersionOption.objects.filter(is_active=True)
            print(f"DEBUG: Found {active_versions.count()} active versions")  # Debug log
            
            versions = []
            
            for version_option in active_versions:
                print(f"DEBUG: Processing version {version_option.title}")  # Debug log
                if version_option.api_bible_id:
                    # Get details from API.Bible
                    bible_info = self.get_bible_details(version_option.api_bible_id)
                    print(f"DEBUG: Got bible info for {version_option.api_bible_id}")  # Debug log
                    
                    versions.append({
                        'id': version_option.api_bible_id,
                        'title': version_option.title,
                        'subtitle': version_option.subtitle,
                        'name': bible_info.get('name', version_option.title) if bible_info else version_option.title,
                        'description': bible_info.get('description', '') if bible_info else '',
                        'language': bible_info.get('language', {}).get('name', 'English') if bible_info else 'English',
                        'is_default': False
                    })
            
            # Cache for 1 hour
            cache.set(cache_key, versions, 3600)
            print(f"DEBUG: Returning {len(versions)} versions from DB")  # Debug log
            return versions
            
        except ImportError as e:
            print(f"DEBUG: ImportError - {str(e)}")  # Debug log
            # Fallback to hardcoded versions
            return self.get_hardcoded_versions()
        except Exception as e:
            print(f"DEBUG: Unexpected error - {str(e)}")  # Debug log
            return self.get_hardcoded_versions()


    
    def get_hardcoded_versions(self):
        """Fallback hardcoded versions"""
        versions = []
        hardcoded = {
            'NIV': '06125adad2d5898a-01',
            'ASV': '685d1470fe4d5c3b-01',
            'WEB': '72f4e6dc683324df-01',
            'KJV': '2eb94132ad61ae75-01'
        }
        
        for name, bible_id in hardcoded.items():
            bible_info = self.get_bible_details(bible_id)
            if bible_info:
                versions.append({
                    'id': bible_id,
                    'title': name,
                    'subtitle': '',
                    'name': bible_info.get('name', name),
                    'description': bible_info.get('description', ''),
                    'language': bible_info.get('language', {}).get('name', 'English'),
                    'is_default': False
                })
        
        return versions
    
    # ... rest of your existing methods remain the same ...
    
    def clean_html_content(self, html_content):
        """Clean HTML content and return plain text"""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def parse_verses_from_content(self, content):
        """Parse verses from HTML content"""
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        verses = []
        
        # Find all verse spans
        verse_spans = soup.find_all('span', {'data-number': True})
        
        for span in verse_spans:
            verse_number = span.get('data-number')
            data_sid = span.get('data-sid', '')
            
            # Extract the verse ID from data-sid (e.g., "NUM 1:5" -> "NUM.1.5")
            verse_id = self.extract_verse_id_from_sid(data_sid)
            
            # Get the verse text (everything after this span until the next verse)
            verse_text = self.extract_verse_text(span)
            
            if verse_text:
                verses.append({
                    'id': verse_id,  # This will be "NUM.1.5" format
                    'number': verse_number,
                    'text': verse_text.strip()
                })
        
        return verses

    def extract_verse_id_from_sid(self, data_sid):
        """Convert data-sid format to verse ID format"""
        # data-sid format: "NUM 1:5" -> "NUM.1.5"
        if not data_sid:
            return ""
        
        # Remove extra spaces and split
        parts = data_sid.strip().split()
        if len(parts) >= 2:
            book_chapter = parts[0] + " " + parts[1]  # "NUM 1:5"
            # Replace space with dot and colon with dot
            verse_id = book_chapter.replace(" ", ".").replace(":", ".")
            return verse_id
        
        return data_sid

    def extract_verse_text(self, span):
        """Extract text content for a verse"""
        # Get all text after the verse number span until the next verse
        text_parts = []
        current = span.next_sibling
        
        while current:
            if hasattr(current, 'name') and current.name == 'span' and current.get('data-number'):
                # Stop when we hit the next verse
                break
            
            if hasattr(current, 'get_text'):
                text_parts.append(current.get_text())
            elif isinstance(current, str):
                text_parts.append(current)
            
            current = current.next_sibling
        
        return ''.join(text_parts).strip()
    
    def get_bible_details(self, bible_id):
        """Get detailed information about a Bible version"""
        cache_key = f"bible_details_{bible_id}"
        cached_details = cache.get(cache_key)
        
        if cached_details:
            return cached_details
        
        url = f"{self.base_url}/bibles/{bible_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                cache.set(cache_key, data, 3600)
                return data
            else:
                print(f"Error getting Bible details: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def get_books(self, bible_id):
        """Get all books for a Bible version"""
        cache_key = f"books_{bible_id}"
        cached_books = cache.get(cache_key)
        
        if cached_books:
            return cached_books
        
        url = f"{self.base_url}/bibles/{bible_id}/books"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', [])
                
                books = []
                for book in data:
                    books.append({
                        'id': book['id'],
                        'name': book['name'],
                        'abbreviation': book.get('abbreviation', ''),
                        'chapters': book.get('chapters', [])
                    })
                
                cache.set(cache_key, books, 3600)
                return books
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Failed to fetch books'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}
    
    def get_chapters(self, bible_id, book_id):
        """Get all chapters for a specific book"""
        cache_key = f"chapters_{bible_id}_{book_id}"
        cached_chapters = cache.get(cache_key)
        
        if cached_chapters:
            return cached_chapters
        
        url = f"{self.base_url}/bibles/{bible_id}/books/{book_id}/chapters"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', [])
                
                chapters = []
                for chapter in data:
                    if chapter.get('number') != 'intro':
                        chapters.append({
                            'id': chapter['id'],
                            'number': chapter['number'],
                            'reference': chapter.get('reference', ''),
                            'verse_count': chapter.get('verseCount', 0)
                        })
                
                cache.set(cache_key, chapters, 3600)
                return chapters
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Failed to fetch chapters'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}
    
    def get_chapter_content(self, bible_id, chapter_id):
        """Get the full content of a chapter with verses"""
        cache_key = f"chapter_content_{bible_id}_{chapter_id}"
        cached_content = cache.get(cache_key)
        
        if cached_content:
            return cached_content
        
        url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                print(data, "🥵") 
                
                verses = self.parse_verses_from_content(data.get('content', ''))
                
                result = {
                    'id': data.get('id'),
                    'reference': data.get('reference'),
                    'verse_count': data.get('verseCount', 0),
                    'content': self.clean_html_content(data.get('content', '')),
                    'verses': verses
                }
                
                cache.set(cache_key, result, 1800)
                return result
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Failed to fetch chapter content'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}
    
    def search_verses(self, bible_id, query, limit=10):
        """Search for verses containing specific keywords"""
        url = f"{self.base_url}/bibles/{bible_id}/search"
        params = {
            'query': query,
            'limit': limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                verses = data.get('verses', [])
                
                cleaned_verses = []
                for verse in verses:
                    cleaned_verses.append({
                        'id': verse.get('id'),
                        'reference': verse.get('reference'),
                        'text': self.clean_html_content(verse.get('text', '')),
                        'book_id': verse.get('bookId'),
                        'chapter_id': verse.get('chapterId')
                    })
                
                return {
                    'query': query,
                    'total': data.get('total', 0),
                    'verses': cleaned_verses
                }
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Search failed'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}
        
    def verse_clean_html_content(self, html_content):
        """Clean HTML content and return plain text with better formatting, removing verse numbers."""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted tags
        for tag in soup(['script', 'style', 'meta', 'link', 'head', 'footer', 'nav']):
            tag.decompose()

        # Remove verse number spans
        for span in soup.find_all("span", {"class": "v"}):
            span.decompose()
        for span in soup.find_all("span", {"data-number": True}):
            span.decompose()

        # Optionally replace <br> and <p> with newlines for readability
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for p in soup.find_all("p"):
            p.insert_before("\n")

        # Remove all attributes from tags
        for tag in soup.find_all(True):
            tag.attrs = {}

        # Get text and unescape HTML entities
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)  # Remove non-printable chars

        # Optionally, collapse multiple newlines
        text = re.sub(r'\n+', '\n', text)

        return text
    
    def get_verse_content(self, bible_id, verse_id):
        """Get specific verse content"""
        cache_key = f"verse_{bible_id}_{verse_id}"
        cached_verse = cache.get(cache_key)
        
        if cached_verse:
            return cached_verse
        
        url = f"{self.base_url}/bibles/{bible_id}/verses/{verse_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                print(data, "🥵") 
                
                result = {
                    'id': data.get('id'),
                    'reference': data.get('reference'),
                    'text': self.verse_clean_html_content(data.get('content', '')),
                    'book_id': data.get('bookId'),
                    'chapter_id': data.get('chapterId')
                }
                
                cache.set(cache_key, result, 1800)
                return result
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Failed to fetch verse'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}
        

    def get_chapter_navigation(self, bible_id, chapter_id):
        """Get next and previous chapter information"""
        cache_key = f"chapter_nav_{bible_id}_{chapter_id}"
        cached_nav = cache.get(cache_key)
        
        if cached_nav:
            return cached_nav
        
        url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                navigation = {
                    'current': {
                        'id': data.get('id'),
                        'number': data.get('number'),
                        'bookId': data.get('bookId'),
                        'reference': data.get('reference')
                    },
                    'next': data.get('next'),
                    'previous': data.get('previous')
                }
                
                cache.set(cache_key, navigation, 1800)
                return navigation
            else:
                return {'error': f'HTTP {response.status_code}', 'message': 'Failed to fetch chapter navigation'}
        except requests.RequestException as e:
            return {'error': 'Request failed', 'message': str(e)}

    def get_next_chapter_content(self, bible_id, current_chapter_id):
        """Get the next chapter's full content"""
        # First get navigation info
        nav_info = self.get_chapter_navigation(bible_id, current_chapter_id)
        
        if 'error' in nav_info:
            return nav_info
        
        next_chapter = nav_info.get('next')
        if not next_chapter:
            return {'error': 'No next chapter', 'message': 'This is the last chapter'}
        
        # Get the full content of the next chapter
        next_chapter_id = next_chapter.get('id')
        return self.get_chapter_content(bible_id, next_chapter_id)

    def get_previous_chapter_content(self, bible_id, current_chapter_id):
        """Get the previous chapter's full content"""
        # First get navigation info
        nav_info = self.get_chapter_navigation(bible_id, current_chapter_id)
        
        if 'error' in nav_info:
            return nav_info
        
        previous_chapter = nav_info.get('previous')
        if not previous_chapter:
            return {'error': 'No previous chapter', 'message': 'This is the first chapter'}
        
        # Get the full content of the previous chapter
        previous_chapter_id = previous_chapter.get('id')
        return self.get_chapter_content(bible_id, previous_chapter_id)