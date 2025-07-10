from django.shortcuts import render

# Create your views here.
# views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from .models import *
from .serializers import *


# Bible Version Views
class BibleVersionCacheListView(APIView):
    """GET /api/bible-versions/ - List all available Bible versions"""
    
    def get(self, request):
        versions = BibleVersionCache.objects.filter(is_active=True)
        serializer = BibleVersionCacheListSerializer(versions, many=True)
        return Response(serializer.data)


class BibleVersionCacheDetailView(APIView):
    """GET /api/bible-versions/{id}/ - Get specific Bible version details"""
    
    def get(self, request, pk):
        version = get_object_or_404(BibleVersionCache, pk=pk)
        serializer = BibleVersionCacheSerializer(version)
        return Response(serializer.data)


# Book Views
class BookListView(APIView):
    """GET /api/bible-versions/{bible_id}/books/ - List books for a Bible version"""
    
    def get(self, request, bible_id):
        bible_version = get_object_or_404(BibleVersionCache, pk=bible_id)
        books = Book.objects.filter(bible_version=bible_version)
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)


class BookDetailView(APIView):
    """GET /api/books/{id}/ - Get book details with chapters"""
    
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookWithChaptersSerializer(book)
        return Response(serializer.data)


# Chapter Views
class ChapterListView(APIView):
    """GET /api/books/{book_id}/chapters/ - List chapters for a book"""
    
    def get(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id)
        chapters = Chapter.objects.filter(book=book)
        serializer = ChapterListSerializer(chapters, many=True)
        return Response(serializer.data)


class ChapterDetailView(APIView):
    """GET /api/chapters/{id}/ - Get chapter with all verses"""
    
    def get(self, request, pk):
        chapter = get_object_or_404(Chapter, pk=pk)
        serializer = ChapterWithVersesSerializer(chapter)
        return Response(serializer.data)


# Verse Views
class VerseDetailView(APIView):
    """GET /api/verses/{id}/ - Get specific verse"""
    
    def get(self, request, pk):
        verse = get_object_or_404(Verse, pk=pk)
        serializer = VerseSerializer(verse)
        return Response(serializer.data)


# Reading Progress Views
class ReadingProgressView(APIView):
    """GET/PUT /api/reading-progress/{bible_id}/ - Reading progress management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, bible_id):
        bible_version = get_object_or_404(BibleVersionCache, pk=bible_id)
        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user, 
            bible_version=bible_version
        )
        serializer = ReadingProgressSerializer(progress)
        return Response(serializer.data)
    
    def put(self, request, bible_id):
        bible_version = get_object_or_404(BibleVersionCache, pk=bible_id)
        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user, 
            bible_version=bible_version
        )
        serializer = UpdateReadingProgressSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ReadingProgressSerializer(progress).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Bookmark Views
class BookmarkListView(APIView):
    """GET/POST /api/bookmarks/ - User bookmarks"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user)
        serializer = BookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CreateBookmarkSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            bookmark = Bookmark.objects.get(id=serializer.instance.id)
            return Response(BookmarkSerializer(bookmark).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookmarkDetailView(APIView):
    """GET/PUT/DELETE /api/bookmarks/{id}/ - Bookmark management"""
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


# Audio Views
class PlaybackStateView(APIView):
    """GET/PUT /api/playback-state/ - Audio playback state"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        playback_state, created = PlaybackState.objects.get_or_create(user=request.user)
        serializer = PlaybackStateSerializer(playback_state)
        return Response(serializer.data)
    
    def put(self, request):
        playback_state, created = PlaybackState.objects.get_or_create(user=request.user)
        serializer = PlaybackStateSerializer(playback_state, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AudioSessionView(APIView):
    """GET/POST /api/audio-sessions/ - Audio session tracking"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        sessions = AudioSession.objects.filter(user=request.user)[:10]  # Last 10 sessions
        serializer = AudioSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AudioSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AudioSessionDetailView(APIView):
    """PUT /api/audio-sessions/{id}/ - Update audio session"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        session = get_object_or_404(AudioSession, pk=pk, user=request.user)
        serializer = AudioSessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Search Views
class SearchView(APIView):
    """POST /api/search/ - Search Bible verses"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        query = request.data.get('query', '')
        bible_id = request.data.get('bible_id')
        
        if not query or not bible_id:
            return Response({'error': 'Query and bible_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        bible_version = get_object_or_404(BibleVersionCache, pk=bible_id)
        
        # Search in verses
        verses = Verse.objects.filter(
            chapter__book__bible_version=bible_version,
            content__icontains=query
        )[:50]  # Limit results
        
        # Save search history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            bible_version=bible_version,
            result_count=verses.count()
        )
        
        serializer = VerseSerializer(verses, many=True)
        return Response({
            'query': query,
            'result_count': verses.count(),
            'results': serializer.data
        })


class SearchHistoryView(APIView):
    """GET /api/search-history/ - User search history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        history = SearchHistory.objects.filter(user=request.user)[:20]
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data)


# Reading Plan Views
class ReadingPlanListView(APIView):
    """GET /api/reading-plans/ - List available reading plans"""
    
    def get(self, request):
        plans = ReadingPlan.objects.filter(is_active=True)
        serializer = ReadingPlanSerializer(plans, many=True)
        return Response(serializer.data)


class UserReadingPlanView(APIView):
    """GET/POST /api/user-reading-plans/ - User's reading plans"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_plans = UserReadingPlan.objects.filter(user=request.user)
        serializer = UserReadingPlanSerializer(user_plans, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserReadingPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Dashboard View
class DashboardView(APIView):
    """GET /api/dashboard/ - User dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get user's reading progress
        progress = ReadingProgress.objects.filter(user=request.user).first()
        
        # Get recent bookmarks
        bookmarks = Bookmark.objects.filter(user=request.user)[:5]
        
        # Get reading plans
        reading_plans = UserReadingPlan.objects.filter(user=request.user, completed=False)
        
        # Get recent audio sessions
        audio_sessions = AudioSession.objects.filter(user=request.user)[:5]
        
        dashboard_data = {
            'reading_progress': ReadingProgressSerializer(progress).data if progress else None,
            'recent_bookmarks': BookmarkSerializer(bookmarks, many=True).data,
            'active_reading_plans': UserReadingPlanSerializer(reading_plans, many=True).data,
            'recent_audio_sessions': AudioSessionSerializer(audio_sessions, many=True).data,
        }
        
        return Response(dashboard_data)