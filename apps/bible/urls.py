# Updated urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Bible content endpoints
    path('bible-versions/', views.BibleVersionListView.as_view(), name='bible-versions'),
    path('user-preferred-bible/', views.UserPreferredBibleView.as_view(), name='user-preferred-bible'),
    path('switch-bible-version/', views.BibleVersionSwitchView.as_view(), name='switch-bible-version'),
    
    path('<str:bible_id>/books/', views.BookListView.as_view(), name='books'),
    path('<str:bible_id>/books/<str:book_id>/chapters/', views.ChapterListView.as_view(), name='chapters'),
    path('<str:bible_id>/chapters/<str:chapter_id>/', views.ChapterContentView.as_view(), name='chapter-content'),
    path('<str:bible_id>/verses/<str:verse_id>/', views.VerseDetailView.as_view(), name='verse-detail'),
    path('<str:bible_id>/search/', views.SearchView.as_view(), name='search'),
    
    path('<str:bible_id>/chapters/<str:chapter_id>/next/', views.NextChapterView.as_view(), name='next-chapter'),
    path('<str:bible_id>/chapters/<str:chapter_id>/previous/', views.PreviousChapterView.as_view(), name='previous-chapter'),
    
    # User features endpoints
    path('reading-progress/', views.ReadingProgressView.as_view(), name='reading-progress'),
    path('bookmarks/', views.BookmarkListView.as_view(), name='bookmarks'),
    path('bookmarks/<uuid:pk>/', views.BookmarkDetailView.as_view(), name='bookmark-detail'),
    path('search-history/', views.SearchHistoryView.as_view(), name='search-history'),
]