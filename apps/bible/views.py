# Updated views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ReadingProgress, Bookmark, SearchHistory
from .serializers import ReadingProgressSerializer, BookmarkSerializer, SearchHistorySerializer
from .services.bible_api_service import BibleAPIService
from apps.core.utils.mixins import BaseResponseMixin


class BibleVersionListView(BaseResponseMixin, APIView):
    """GET /api/bible-versions/ - List all Bible versions with user's preference marked"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        service = BibleAPIService()
        versions = service.get_bible_versions()
        
        # Get user's preferred Bible version
        user_preferred_id = self.get_user_preferred_bible_id(request.user)
        
        # Mark user's preferred version
        for version in versions:
            version['is_default'] = version['id'] == user_preferred_id
            version['is_user_preferred'] = version['id'] == user_preferred_id

        return self.success_response(
            {
            'versions': versions,
            'user_preferred_id': user_preferred_id
        }
        )
        
    
    def get_user_preferred_bible_id(self, user):
        """Get user's preferred Bible version ID"""
        try:
            from apps.onboarding.models import BibleVersion
            user_bible_version = BibleVersion.objects.filter(user=user).first()
            if user_bible_version and user_bible_version.bible_version_option:
                return user_bible_version.bible_version_option.api_bible_id
        except ImportError:
            pass
        
        # Fallback to reading progress bible version
        try:
            progress = ReadingProgress.objects.get(user=user)
            return progress.bible_version_id
        except ReadingProgress.DoesNotExist:
            pass
        
        # Final fallback
        return '06125adad2d5898a-01'  # NIV


class UserPreferredBibleView(APIView):
    """GET/PUT /api/user-preferred-bible/ - Get/Update user's preferred Bible version"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from apps.onboarding.models import BibleVersion
            user_bible_version = BibleVersion.objects.get(user=request.user)
            bible_version_option = user_bible_version.bible_version_option
            
            # Get Bible details from API.Bible
            service = BibleAPIService()
            api_bible_id = bible_version_option.api_bible_id
            bible_details = service.get_bible_details(api_bible_id)
            
            return Response({
                'preferred_version': {
                    'id': api_bible_id,
                    'title': bible_version_option.title,
                    'subtitle': bible_version_option.subtitle,
                    'details': bible_details
                }
            })
        except (ImportError, AttributeError):
            # Fallback to reading progress
            try:
                progress = ReadingProgress.objects.get(user=request.user)
                service = BibleAPIService()
                bible_details = service.get_bible_details(progress.bible_version_id)
                
                return Response({
                    'preferred_version': {
                        'id': progress.bible_version_id,
                        'title': 'User Selected Version',
                        'subtitle': '',
                        'details': bible_details
                    }
                })
            except ReadingProgress.DoesNotExist:
                pass
        except Exception as e:
            pass
        
        # Final fallback
        return Response({
            'preferred_version': {
                'id': '06125adad2d5898a-01',
                'title': 'New International Version',
                'subtitle': 'NIV',
                'details': {}
            }
        })
    
    def put(self, request):
        """Update user's preferred Bible version"""
        bible_version_id = request.data.get('bible_version_id')
        
        if not bible_version_id:
            return Response({'error': 'bible_version_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.onboarding.models import BibleVersion, BibleVersionOption
            
            # Get the Bible version option
            bible_version_option = BibleVersionOption.objects.get(api_bible_id=bible_version_id)
            
            # Update or create user's Bible version preference
            user_bible_version, created = BibleVersion.objects.get_or_create(
                user=request.user,
                defaults={'bible_version_option': bible_version_option}
            )
            
            if not created:
                user_bible_version.bible_version_option = bible_version_option
                user_bible_version.save()
            
            # Also update reading progress to use new version
            progress, created = ReadingProgress.objects.get_or_create(
                user=request.user,
                defaults={'bible_version_id': bible_version_id}
            )
            
            if not created:
                progress.bible_version_id = bible_version_id
                progress.save()
            
            return Response({
                'message': 'Preferred Bible version updated successfully',
                'bible_version_id': bible_version_id
            })
            
        except ImportError:
            # Fallback: just update reading progress
            progress, created = ReadingProgress.objects.get_or_create(
                user=request.user,
                defaults={'bible_version_id': bible_version_id}
            )
            
            if not created:
                progress.bible_version_id = bible_version_id
                progress.save()
            
            return Response({
                'message': 'Bible version preference updated',
                'bible_version_id': bible_version_id
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookListView(APIView):
    """GET /api/bibles/{bible_id}/books/ - List books for a Bible version"""
    def get(self, request, bible_id):
        service = BibleAPIService()
        books = service.get_books(bible_id)
        
        if isinstance(books, dict) and 'error' in books:
            return Response(books, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'bible_id': bible_id,
            'books': books
        })


class ChapterListView(APIView):
    """GET /api/bibles/{bible_id}/books/{book_id}/chapters/ - List chapters"""
    def get(self, request, bible_id, book_id):
        service = BibleAPIService()
        chapters = service.get_chapters(bible_id, book_id)
        
        if isinstance(chapters, dict) and 'error' in chapters:
            return Response(chapters, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'bible_id': bible_id,
            'book_id': book_id,
            'chapters': chapters
        })


class ChapterContentView(APIView):
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/ - Get chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        content = service.get_chapter_content(bible_id, chapter_id)
        
        if isinstance(content, dict) and 'error' in content:
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        # Add Bible version info to response
        bible_details = service.get_bible_details(bible_id)
        
        # Get navigation info
        nav_info = service.get_chapter_navigation(bible_id, chapter_id)
        
        return Response({
            'bible_id': bible_id,
            'bible_info': bible_details,
            'chapter': content,
            'navigation': nav_info  # Added navigation info
        })

class SearchView(APIView):
    """GET /api/bibles/{bible_id}/search/?query=text - Search verses"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, bible_id):
        query = request.query_params.get('query')
        if not query:
            return Response({'error': 'Query parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        service = BibleAPIService()
        results = service.search_verses(bible_id, query, limit)
        
        if isinstance(results, dict) and 'error' in results:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        
        # Save search history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            bible_version_id=bible_id
        )
        
        return Response({
            'bible_id': bible_id,
            'search_results': results
        })


class ReadingProgressView(APIView):
    """GET/PUT /api/reading-progress/ - User's reading progress"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get user's preferred Bible version
        preferred_bible_id = self.get_user_preferred_bible_id(request.user)
        
        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user,
            defaults={'bible_version_id': preferred_bible_id}
        )
        
        serializer = ReadingProgressSerializer(progress)
        return Response(serializer.data)
    
    def put(self, request):
        """Update reading progress"""
        try:
            progress = ReadingProgress.objects.get(user=request.user)
        except ReadingProgress.DoesNotExist:
            preferred_bible_id = self.get_user_preferred_bible_id(request.user)
            progress = ReadingProgress.objects.create(
                user=request.user,
                bible_version_id=preferred_bible_id
            )
        
        serializer = ReadingProgressSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_user_preferred_bible_id(self, user):
        """Get user's preferred Bible version ID"""
        try:
            from apps.onboarding.models import BibleVersion
            user_bible_version = BibleVersion.objects.filter(user=user).first()
            if user_bible_version and user_bible_version.bible_version_option:
                return user_bible_version.bible_version_option.api_bible_id
        except ImportError:
            pass
        
        return '06125adad2d5898a-01'  # Default to NIV


class BookmarkListView(APIView):
    """GET/POST /api/bookmarks/ - User bookmarks"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user)
        serializer = BookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BookmarkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookmarkDetailView(APIView):
    """GET/PUT/DELETE /api/bookmarks/{id}/ - Bookmark detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
        serializer = BookmarkSerializer(bookmark)
        return Response(serializer.data)
    
    def put(self, request, pk):
        bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
        serializer = BookmarkSerializer(bookmark, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchHistoryView(APIView):
    """GET /api/search-history/ - User's search history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        history = SearchHistory.objects.filter(user=request.user)[:10]
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    def delete(self, request):
        """Clear search history"""
        SearchHistory.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerseDetailView(APIView):
    """GET /api/bibles/{bible_id}/verses/{verse_id}/ - Get specific verse"""
    def get(self, request, bible_id, verse_id):
        service = BibleAPIService()
        verse = service.get_verse_content(bible_id, verse_id)
        
        if isinstance(verse, dict) and 'error' in verse:
            return Response(verse, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'bible_id': bible_id,
            'verse': verse
        })


class BibleVersionSwitchView(APIView):
    """POST /api/switch-bible-version/ - Temporarily switch Bible version for current session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Switch Bible version temporarily (doesn't change user preference)"""
        bible_version_id = request.data.get('bible_version_id')
        
        if not bible_version_id:
            return Response({'error': 'bible_version_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Validate that the Bible version exists
        service = BibleAPIService()
        bible_details = service.get_bible_details(bible_version_id)
        
        if not bible_details:
            return Response({'error': 'Invalid Bible version ID'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Update reading progress to use this version temporarily
        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user,
            defaults={'bible_version_id': bible_version_id}
        )
        
        # Store the current Bible version without changing user preference
        progress.bible_version_id = bible_version_id
        progress.save()
        
        return Response({
            'message': 'Bible version switched successfully',
            'current_bible_version': {
                'id': bible_version_id,
                'details': bible_details
            }
        })
    

class NextChapterView(APIView):
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/next/ - Get next chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        
        # Get next chapter content
        next_content = service.get_next_chapter_content(bible_id, chapter_id)
        
        if isinstance(next_content, dict) and 'error' in next_content:
            return Response(next_content, status=status.HTTP_400_BAD_REQUEST)
        
        # Add Bible version info to response
        bible_details = service.get_bible_details(bible_id)
        
        # Get navigation info for the next chapter
        next_chapter_id = next_content.get('id')
        nav_info = service.get_chapter_navigation(bible_id, next_chapter_id)
        
        return Response({
            'bible_id': bible_id,
            'bible_info': bible_details,
            'chapter': next_content,
            'navigation': nav_info
        })

class PreviousChapterView(APIView):
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/previous/ - Get previous chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        
        # Get previous chapter content
        previous_content = service.get_previous_chapter_content(bible_id, chapter_id)
        
        if isinstance(previous_content, dict) and 'error' in previous_content:
            return Response(previous_content, status=status.HTTP_400_BAD_REQUEST)
        
        # Add Bible version info to response
        bible_details = service.get_bible_details(bible_id)
        
        # Get navigation info for the previous chapter
        previous_chapter_id = previous_content.get('id')
        nav_info = service.get_chapter_navigation(bible_id, previous_chapter_id)
        
        return Response({
            'bible_id': bible_id,
            'bible_info': bible_details,
            'chapter': previous_content,
            'navigation': nav_info
        })