from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ReadingProgress, Bookmark, SearchHistory
from .serializers import ReadingProgressSerializer, BookmarkSerializer, SearchHistorySerializer
from .services.bible_api_service import BibleAPIService
from apps.core.utils.mixins import BaseResponseMixin
import logging

logger = logging.getLogger(__name__)


class BibleVersionListView(BaseResponseMixin, APIView):
    """GET /api/bible-versions/ - List all Bible versions with user's preference marked"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        service = BibleAPIService()
        versions = service.get_bible_versions()
        user_preferred_id = self.get_user_preferred_bible_id(request.user)
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
        try:
            progress = ReadingProgress.objects.get(user=user)
            return progress.bible_version_id
        except ReadingProgress.DoesNotExist:
            pass
        return '06125adad2d5898a-01'  # NIV

class UserPreferredBibleView(BaseResponseMixin, APIView):
    """GET/PUT /api/user-preferred-bible/ - Get/Update user's preferred Bible version"""
    permission_classes = [IsAuthenticated]
    
    def get_default_bible_version(self):
        """
        Returns a dynamic default Bible version from available options
        """
        try:
            from apps.onboarding.models import BibleVersionOption
            default_version = BibleVersionOption.objects.first()
            if default_version:
                return {
                    'id': default_version.api_bible_id,
                    'title': default_version.title,
                    'subtitle': default_version.subtitle,
                    'details': {}
                }
        except (ImportError, AttributeError):
            pass
        return {
            'id': '9879dbb7cfe39e4d-01',  # WEB as a reasonable default
            'title': 'World English Bible',
            'subtitle': 'Modern English public domain translation',
            'details': {}
        }

    def get(self, request):
        try:
            from apps.onboarding.models import BibleVersion
            user_bible_version = BibleVersion.objects.get(user=request.user)
            bible_version_option = user_bible_version.bible_version_option
            service = BibleAPIService()
            api_bible_id = bible_version_option.api_bible_id
            bible_details = service.get_bible_details(api_bible_id)

            return self.success_response({
                'preferred_version': {
                    'id': api_bible_id,
                    'title': bible_version_option.title,
                    'subtitle': bible_version_option.subtitle,
                    'details': bible_details
                }
            })
        except (ImportError, AttributeError, BibleVersion.DoesNotExist):
            try:
                progress = ReadingProgress.objects.get(user=request.user)
                service = BibleAPIService()
                bible_details = service.get_bible_details(progress.bible_version_id)
                
                return self.success_response({
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
            logger.error(f"Error fetching preferred Bible version: {str(e)}")
        default_version = self.get_default_bible_version()
        return self.success_response({
            'preferred_version': default_version,
            'is_default_fallback': True  # Indicate this is a fallback
        })
    
    def put(self, request):
        """Update user's preferred Bible version"""
        bible_version_id = request.data.get('bible_version_id')
        
        if not bible_version_id:
            return self.bad_request_response('bible_version_id is required')
        
        try:
            from apps.onboarding.models import BibleVersion, BibleVersionOption
            bible_version_option = BibleVersionOption.objects.get(api_bible_id=bible_version_id)
            user_bible_version, created = BibleVersion.objects.update_or_create(
                user=request.user,
                defaults={'bible_version_option': bible_version_option}
            )
            ReadingProgress.objects.update_or_create(
                user=request.user,
                defaults={'bible_version_id': bible_version_id}
            )
            
            return self.success_response(
                data={
                    'bible_version_id': bible_version_id,
                    'title': bible_version_option.title,
                    'subtitle': bible_version_option.subtitle
                },
                message='Preferred Bible version updated successfully'
            )
            
        except BibleVersionOption.DoesNotExist:
            return self.not_found_response('Specified Bible version not found')
        except ImportError:
            ReadingProgress.objects.update_or_create(
                user=request.user,
                defaults={'bible_version_id': bible_version_id}
            )
            
            return self.success_response(
                data={'bible_version_id': bible_version_id},
                message='Bible version preference updated (fallback)'
            )
        except Exception as e:
            logger.error(f"Error updating Bible version: {str(e)}")
            return self.error_response(
                message='Failed to update Bible version',
                error_code='UPDATE_FAILED',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
class BookListView(BaseResponseMixin, APIView):
    """GET /api/bibles/{bible_id}/books/ - List books for a Bible version"""
    
    def get(self, request, bible_id):
        try:
            service = BibleAPIService()
            books = service.get_books(bible_id)
            
            if isinstance(books, dict) and 'error' in books:
                return self.error_response(
                    message=books.get('error', 'Failed to fetch books'),
                    error_code='BIBLE_API_ERROR',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            return self.success_response({
                'bible_id': bible_id,
                'books': books,
                'count': len(books) if isinstance(books, list) else 0
            })
            
        except Exception as e:
            logger.error(f"Error fetching books for Bible {bible_id}: {str(e)}")
            return self.error_response(
                message='Failed to retrieve books list',
                error_code='BOOKS_RETRIEVAL_ERROR',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChapterListView(APIView, BaseResponseMixin): # <--- Add BaseResponseMixin here
    """GET /api/bibles/{bible_id}/books/{book_id}/chapters/ - List chapters"""
    def get(self, request, bible_id, book_id):
        service = BibleAPIService()
        chapters_data = service.get_chapters(bible_id, book_id) # Renamed for clarity

        if isinstance(chapters_data, dict) and 'error' in chapters_data:
            status_code = chapters_data.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = chapters_data.get('error', 'An error occurred while fetching chapters.')
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            elif status_code == status.HTTP_400_BAD_REQUEST:
                return self.bad_request_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="EXTERNAL_API_ERROR" # Or a more specific code if the external API provides one
                )
        
        return self.success_response(
            data={
                'bible_id': bible_id,
                'book_id': book_id,
                'chapters': chapters_data # Use the fetched chapters data
            },
            message="Chapters retrieved successfully." # Add a success message
        )


class ChapterContentView(APIView, BaseResponseMixin): # <--- ADDED BaseResponseMixin here
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/ - Get chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        content = service.get_chapter_content(bible_id, chapter_id)
        
        if isinstance(content, dict) and 'error' in content:
            status_code = content.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = content.get('error', 'Failed to retrieve chapter content.')
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="CHAPTER_CONTENT_ERROR" # Custom error code for this specific issue
                )
        bible_details = service.get_bible_details(bible_id)
        if isinstance(bible_details, dict) and 'error' in bible_details:
            status_code = bible_details.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = bible_details.get('error', 'Failed to retrieve Bible details.')
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="BIBLE_DETAILS_ERROR"
                )
        nav_info = service.get_chapter_navigation(bible_id, chapter_id)
        if isinstance(nav_info, dict) and 'error' in nav_info:
            status_code = nav_info.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = nav_info.get('error', 'Failed to retrieve navigation info.')

            return self.error_response(
                message=message,
                status_code=status_code,
                error_code="NAVIGATION_INFO_ERROR"
            )
 
        return self.success_response(
            data={
                'bible_id': bible_id,
                'bible_info': bible_details,
                'chapter': content,
                'navigation': nav_info
            },
            message="Chapter content and details retrieved successfully."
        )
    


class SearchView(APIView, BaseResponseMixin):
    """GET /api/bibles/{bible_id}/search/?query=text - Search verses"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, bible_id):
        query = request.query_params.get('query')
        if not query:
            return self.bad_request_response(
                message="Query parameter 'query' is required.",
                error_code="QUERY_PARAM_REQUIRED"
            )
        
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
            if limit <= 0: # Add a check for non-positive limit
                return self.bad_request_response(
                    message="Limit must be a positive integer.",
                    error_code="INVALID_LIMIT"
                )
        except ValueError:
            return self.bad_request_response(
                message="Limit must be an integer.",
                error_code="INVALID_LIMIT_TYPE"
            )
        
        service = BibleAPIService()
        results = service.search_verses(bible_id, query, limit)
        
        if isinstance(results, dict) and 'error' in results:
            status_code = results.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = results.get('error', 'Failed to perform search.')
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="SEARCH_ERROR"
                )
        
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            bible_version_id=bible_id
        )
        
        return self.success_response(
            data={
                'bible_id': bible_id,
                'search_results': results
            },
            message="Search completed successfully."
        )


class ReadingProgressView(APIView):
    """GET/PUT /api/reading-progress/ - User's reading progress"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
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


class SearchHistoryView(APIView, BaseResponseMixin):
    """GET /api/search-history/ - User's search history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        history = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')[:10] # Added order_by for typical history views
        serializer = SearchHistorySerializer(history, many=True)
        return self.success_response(data=serializer.data, message="Search history retrieved successfully.")
    
    def delete(self, request):
        """Clear search history"""
        SearchHistory.objects.filter(user=request.user).delete()
        return self.deleted_response(message="Search history cleared successfully.")


class VerseDetailView(APIView, BaseResponseMixin):
    """GET /api/bibles/{bible_id}/verses/{verse_id}/ - Get specific verse"""
    def get(self, request, bible_id, verse_id):
        service = BibleAPIService()
        verse_data = service.get_verse_content(bible_id, verse_id)
        
        if isinstance(verse_data, dict) and 'error' in verse_data:
            status_code = verse_data.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = verse_data.get('error', 'Failed to retrieve verse content.')
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="VERSE_CONTENT_ERROR"
                )
        
        return self.success_response(
            data={
                'bible_id': bible_id,
                'verse': verse_data
            },
            message="Verse content retrieved successfully."
        )
    

class BibleVersionSwitchView(APIView):
    """POST /api/switch-bible-version/ - Temporarily switch Bible version for current session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Switch Bible version temporarily (doesn't change user preference)"""
        bible_version_id = request.data.get('bible_version_id')
        
        if not bible_version_id:
            return Response({'error': 'bible_version_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        service = BibleAPIService()
        bible_details = service.get_bible_details(bible_version_id)
        
        if not bible_details:
            return Response({'error': 'Invalid Bible version ID'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user,
            defaults={'bible_version_id': bible_version_id}
        )
        progress.bible_version_id = bible_version_id
        progress.save()
        
        return Response({
            'message': 'Bible version switched successfully',
            'current_bible_version': {
                'id': bible_version_id,
                'details': bible_details
            }
        })
    
class NextChapterView(APIView, BaseResponseMixin):
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/next/ - Get next chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        
        next_content = service.get_next_chapter_content(bible_id, chapter_id)
        
        if isinstance(next_content, dict) and 'error' in next_content:
            status_code = next_content.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = next_content.get('error', 'Failed to retrieve next chapter content.')
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="NEXT_CHAPTER_CONTENT_ERROR"
                )
        
        bible_details = service.get_bible_details(bible_id)
        if isinstance(bible_details, dict) and 'error' in bible_details:
            status_code = bible_details.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = bible_details.get('error', 'Failed to retrieve Bible details.')
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="BIBLE_DETAILS_ERROR"
                )
        
        next_chapter_id = next_content.get('id')
        nav_info = service.get_chapter_navigation(bible_id, next_chapter_id)
        if isinstance(nav_info, dict) and 'error' in nav_info:
            status_code = nav_info.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = nav_info.get('error', 'Failed to retrieve navigation info for next chapter.')
            return self.error_response(
                message=message,
                status_code=status_code,
                error_code="NAVIGATION_INFO_ERROR"
            )
        
        return self.success_response(
            data={
                'bible_id': bible_id,
                'bible_info': bible_details,
                'chapter': next_content,
                'navigation': nav_info
            },
            message="Next chapter content and details retrieved successfully."
        )


class PreviousChapterView(APIView, BaseResponseMixin):
    """GET /api/bibles/{bible_id}/chapters/{chapter_id}/previous/ - Get previous chapter content"""
    def get(self, request, bible_id, chapter_id):
        service = BibleAPIService()
        
        previous_content = service.get_previous_chapter_content(bible_id, chapter_id)
        
        if isinstance(previous_content, dict) and 'error' in previous_content:
            status_code = previous_content.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = previous_content.get('error', 'Failed to retrieve previous chapter content.')
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="PREVIOUS_CHAPTER_CONTENT_ERROR"
                )
        
        bible_details = service.get_bible_details(bible_id)
        if isinstance(bible_details, dict) and 'error' in bible_details:
            status_code = bible_details.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = bible_details.get('error', 'Failed to retrieve Bible details.')
            if status_code == status.HTTP_404_NOT_FOUND:
                return self.not_found_response(message=message)
            else:
                return self.error_response(
                    message=message,
                    status_code=status_code,
                    error_code="BIBLE_DETAILS_ERROR"
                )
        
        previous_chapter_id = previous_content.get('id')
        nav_info = service.get_chapter_navigation(bible_id, previous_chapter_id)
        if isinstance(nav_info, dict) and 'error' in nav_info:
            status_code = nav_info.get('statusCode', status.HTTP_400_BAD_REQUEST)
            message = nav_info.get('error', 'Failed to retrieve navigation info for previous chapter.')
            return self.error_response(
                message=message,
                status_code=status_code,
                error_code="NAVIGATION_INFO_ERROR"
            )
        
        return self.success_response(
            data={
                'bible_id': bible_id,
                'bible_info': bible_details,
                'chapter': previous_content,
                'navigation': nav_info
            },
            message="Previous chapter content and details retrieved successfully."
        )