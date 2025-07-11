from django.contrib import admin
from .models import (
    ReadingProgress,
    Bookmark,
    SearchHistory,
    ReadingPlan,
    UserNote,
)


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'bible_version_id',
        'current_book_id',
        'current_chapter_id',
        'current_verse_number',
        'is_audio_mode',
        'last_read_date',
        'consecutive_days',
        'updated_at',
    )
    search_fields = ('user__username', 'bible_version_id', 'current_book_id', 'current_chapter_id')
    list_filter = ('is_audio_mode', 'last_read_date')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'bible_version_id',
        'book_id',
        'chapter_id',
        'verse_id',
        'color',
        'created_at',
    )
    search_fields = ('user__username', 'verse_id', 'note', 'tags')
    list_filter = ('color', 'created_at')
    readonly_fields = ('id',)


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'query',
        'bible_version_id',
        'result_count',
        'created_at',
    )
    search_fields = ('user__username', 'query', 'bible_version_id')
    list_filter = ('created_at',)


@admin.register(ReadingPlan)
class ReadingPlanAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'name',
        'plan_type',
        'bible_version_id',
        'start_date',
        'end_date',
        'is_active',
        'completion_percentage',
        'created_at',
    )
    search_fields = ('user__username', 'name', 'bible_version_id')
    list_filter = ('plan_type', 'is_active', 'created_at')


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'title',
        'note_type',
        'bible_version_id',
        'book_id',
        'chapter_id',
        'verse_id',
        'updated_at',
    )
    search_fields = ('user__username', 'title', 'content', 'bible_version_id')
    list_filter = ('note_type', 'updated_at')
    readonly_fields = ('id',)

