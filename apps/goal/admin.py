from django.contrib import admin
from apps.goal.models import UserGoal, ChapterRead, ConversationInteraction, ShareActivity

@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'current_count', 'target_count', 'completed', 'week_start')
    list_filter = ('goal_type', 'completed', 'week_start')
    search_fields = ('user__username',)
    ordering = ('-week_start',)

@admin.register(ChapterRead)
class ChapterReadAdmin(admin.ModelAdmin):
    list_display = ('user', 'bible_id', 'chapter_id', 'read_at')
    search_fields = ('user__username', 'bible_id', 'chapter_id')
    list_filter = ('bible_id',)
    ordering = ('-read_at',)

@admin.register(ConversationInteraction)
class ConversationInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'interaction_type', 'content_type', 'content_id', 'created_at')
    list_filter = ('interaction_type', 'content_type')
    search_fields = ('user__username', 'content_id')
    ordering = ('-created_at',)

@admin.register(ShareActivity)
class ShareActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'content_id', 'share_platform', 'shared_at')
    list_filter = ('share_platform', 'content_type')
    search_fields = ('user__username', 'content_id')
    ordering = ('-shared_at',)
