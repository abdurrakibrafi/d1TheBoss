import requests
import json
import re

class BibleAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.scripture.api.bible/v1"
        self.headers = {
            'api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Your three Bible versions
        self.bible_versions = {
            'NIV': '06125adad2d5898a-01',
            'RSVCE': '23a9e6c7f72c7a17-01', 
            'CSB': '31f05e40af9925ef-01'
            
        }
    
    def get_bible_info(self, bible_id):
        """Get information about a specific Bible version"""
        url = f"{self.base_url}/bibles/{bible_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def get_books(self, bible_id):
        """Get all books for a Bible version"""
        url = f"{self.base_url}/bibles/{bible_id}/books"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def get_chapters(self, bible_id, book_id):
        """Get all chapters for a specific book"""
        url = f"{self.base_url}/bibles/{bible_id}/books/{book_id}/chapters"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def get_chapter_content(self, bible_id, chapter_id):
        """Get the full content of a chapter with verses"""
        url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def get_verse_list(self, bible_id, chapter_id):
        """Get verse IDs for a chapter"""
        url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter_id}/verses"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def search_bible(self, bible_id, query, limit=10):
        """Search for verses containing specific keywords"""
        url = f"{self.base_url}/bibles/{bible_id}/search"
        params = {
            'query': query,
            'limit': limit
        }
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def parse_chapter_verses(self, chapter_content):
        """Parse chapter content into individual verses"""
        # Remove HTML tags but keep verse numbers
        content = chapter_content
        
        # Find all verse numbers and their content
        verse_pattern = r'(\d+)([^0-9]+?)(?=\d+|$)'
        verses = re.findall(verse_pattern, content)
        
        parsed_verses = []
        for match in verses:
            verse_num = match[0]
            verse_text = match[1].strip()
            # Clean up remaining HTML tags
            verse_text = re.sub(r'<[^>]+>', '', verse_text)
            parsed_verses.append({
                'number': verse_num,
                'text': verse_text
            })
        
        return parsed_verses

def main():
    # Replace with your actual API key
    API_KEY = "5bfde174ec2ff06892d3af5a4a35f9d8"
    
    bible_api = BibleAPI(API_KEY)
    
    print("=== Bible API Working Demo ===\n")
    
    # Step 1: Show available Bible versions
    print("Available Bible Versions:")
    for name, bible_id in bible_api.bible_versions.items():
        print(f"- {name}: {bible_id}")
    
    # Step 2: Select a version
    selected_version = "NIV"
    selected_bible_id = bible_api.bible_versions[selected_version]
    print(f"\nSelected Version: {selected_version}")
    
    # Step 3: Get Bible info
    print(f"\nGetting Bible info for {selected_version}...")
    bible_info = bible_api.get_bible_info(selected_bible_id)
    if bible_info:
        data = bible_info['data']
        print(f"Name: {data['name']}")
        print(f"Description: {data['description']}")
        print(f"Language: {data['language']['name']}")
    
    # Step 4: Get all books
    print(f"\nGetting books for {selected_version}...")
    books_data = bible_api.get_books(selected_bible_id)
    if books_data:
        books = books_data['data']
        print(f"Total books: {len(books)}")
        print("\nFirst 10 books:")
        for i, book in enumerate(books[:10]):
            print(f"{i+1:2d}. {book['name']} (ID: {book['id']})")
    
    # Step 5: Get chapters for Genesis
    if books_data:
        genesis = books[0]
        print(f"\nGetting chapters for {genesis['name']}...")
        chapters_data = bible_api.get_chapters(selected_bible_id, genesis['id'])
        if chapters_data:
            chapters = chapters_data['data']
            # Filter out intro chapter
            numbered_chapters = [ch for ch in chapters if ch['number'] != 'intro']
            print(f"Total chapters in {genesis['name']}: {len(numbered_chapters)}")
            print("First 5 chapters:")
            for chapter in numbered_chapters[:5]:
                print(f"- Chapter {chapter['number']} (ID: {chapter['id']})")
    
    # Step 6: Get content for Genesis Chapter 1
    if chapters_data:
        genesis_1 = None
        for chapter in chapters:
            if chapter['number'] == '1':
                genesis_1 = chapter
                break
        
        if genesis_1:
            print(f"\nGetting content for {genesis['name']} Chapter 1...")
            chapter_content = bible_api.get_chapter_content(selected_bible_id, genesis_1['id'])
            if chapter_content:
                data = chapter_content['data']
                print(f"Chapter: {data['reference']}")
                print(f"Total verses: {data['verseCount']}")
                
                # Get verse list for reference
                verse_list = bible_api.get_verse_list(selected_bible_id, genesis_1['id'])
                if verse_list:
                    verses = verse_list['data']
                    print(f"Verse count from API: {len(verses)}")
                
                # Parse verses from chapter content
                parsed_verses = bible_api.parse_chapter_verses(data['content'])
                print(f"\nFirst 3 verses:")
                for verse in parsed_verses[:3]:
                    print(f"Verse {verse['number']}: {verse['text']}")
                
                # Show raw content preview
                clean_content = re.sub(r'<[^>]+>', '', data['content'])
                print(f"\nRaw content preview: {clean_content[:200]}...")
    
    # Step 7: Test search functionality
    print(f"\nTesting search functionality...")
    search_results = bible_api.search_bible(selected_bible_id, "love", limit=3)
    if search_results:
        verses = search_results['data']['verses']
        print(f"Found {len(verses)} verses containing 'love':")
        for verse in verses:
            clean_text = re.sub(r'<[^>]+>', '', verse['text'])
            print(f"- {verse['reference']}: {clean_text[:80]}...")
    
    # Step 8: Test with different Bible versions
    print(f"\nTesting other Bible versions...")
    for version_name, version_id in bible_api.bible_versions.items():
        if version_name != selected_version:
            print(f"\n{version_name}:")
            bible_info = bible_api.get_bible_info(version_id)
            if bible_info:
                data = bible_info['data']
                print(f"  Name: {data['name']}")
                print(f"  Language: {data['language']['name']}")
                
                # Test search in this version
                search_results = bible_api.search_bible(version_id, "love", limit=1)
                if search_results and search_results['data']['verses']:
                    verse = search_results['data']['verses'][0]
                    clean_text = re.sub(r'<[^>]+>', '', verse['text'])
                    print(f"  Sample verse: {verse['reference']}: {clean_text[:60]}...")

if __name__ == "__main__":
    main()