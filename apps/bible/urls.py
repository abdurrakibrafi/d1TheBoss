from django.urls import path
from . import views

urlpatterns = [
    # Bible Version URLs
    path('bible-versions/', views.BibleVersionCacheListView.as_view(), name='bible-versions'),
    path('bible-versions/<int:pk>/', views.BibleVersionCacheDetailView.as_view(), name='bible-version-detail'),
    
    # Book URLs
    path('bible-versions/<int:bible_id>/books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    
    # Chapter URLs
    path('books/<int:book_id>/chapters/', views.ChapterListView.as_view(), name='chapter-list'),
    path('chapters/<int:pk>/', views.ChapterDetailView.as_view(), name='chapter-detail'),
    
    # Verse URLs
    path('verses/<int:pk>/', views.VerseDetailView.as_view(), name='verse-detail'),
        
    # Reading Progress URLs
    path('reading-progress/<int:bible_id>/', views.ReadingProgressView.as_view(), name='reading-progress'),
    
    # Bookmark URLs
    path('bookmarks/', views.BookmarkListView.as_view(), name='bookmark-list'),
    path('bookmarks/<uuid:pk>/', views.BookmarkDetailView.as_view(), name='bookmark-detail'),
    
    # Audio URLs
    path('playback-state/', views.PlaybackStateView.as_view(), name='playback-state'),
    path('audio-sessions/', views.AudioSessionView.as_view(), name='audio-sessions'),
    path('audio-sessions/<uuid:pk>/', views.AudioSessionDetailView.as_view(), name='audio-session-detail'),
    
    # Search URLs
    path('search/', views.SearchView.as_view(), name='search'),
    path('search-history/', views.SearchHistoryView.as_view(), name='search-history'),
    
    # Reading Plan URLs
    path('reading-plans/', views.ReadingPlanListView.as_view(), name='reading-plans'),
    path('user-reading-plans/', views.UserReadingPlanView.as_view(), name='user-reading-plans'),
    
    # Dashboard URL
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]