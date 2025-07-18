from django.urls import path
from apps.chat.views import (
    CreateChatSessionView, ChatSessionListView, ChatSessionDetailView,
    ChatSessionUpdateView, ChatSessionDeleteView, BookmarkMessageView,
    BookmarkedMessagesView, RegenerateResponseView, SearchChatHistoryView,
    FavoriteChatSessionView, NeedMoreClarityView, ChatStatisticsView,
    ExportChatHistoryView
)

urlpatterns = [
    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='chat-session-list'),
    path('sessions/create/', CreateChatSessionView.as_view(), name='chat-session-create'),
    path('sessions/<uuid:pk>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
    path('sessions/<uuid:pk>/update/', ChatSessionUpdateView.as_view(), name='chat-session-update'),
    path('sessions/<uuid:pk>/delete/', ChatSessionDeleteView.as_view(), name='chat-session-delete'),
    path('sessions/<uuid:pk>/favorite/', FavoriteChatSessionView.as_view(), name='chat-session-favorite'),
    
    # Message management
    path('messages/<int:message_id>/bookmark/', BookmarkMessageView.as_view(), name='bookmark-message'),
    path('messages/<int:message_id>/regenerate/', RegenerateResponseView.as_view(), name='regenerate-response'),
    path('messages/<int:message_id>/clarity/', NeedMoreClarityView.as_view(), name='need-more-clarity'),
    path('messages/bookmarked/', BookmarkedMessagesView.as_view(), name='bookmarked-messages'),
    
    # Search and utilities
    path('search/', SearchChatHistoryView.as_view(), name='search-chat-history'),
    path('statistics/', ChatStatisticsView.as_view(), name='chat-statistics'),
    path('export/', ExportChatHistoryView.as_view(), name='export-chat-history'),
]
