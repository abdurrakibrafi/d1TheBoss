from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'content', 'is_user', 'bookmark', 'model_used',
        'tokens_consumed', 'response_time', 'ai_metadata',
        'created_at', 'updated_at'
    )
    show_change_link = True


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_active', 'message_count', 'tokens_used', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('id', 'user__email', 'title')
    readonly_fields = ('created_at', 'updated_at', 'message_count', 'tokens_used')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'is_user', 'bookmark', 'model_used', 'tokens_consumed', 'response_time', 'created_at')
    list_filter = ('is_user', 'bookmark', 'created_at')
    search_fields = ('session__id', 'content')
    readonly_fields = ('created_at', 'updated_at')

