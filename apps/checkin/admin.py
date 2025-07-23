from django.contrib import admin
from apps.checkin.models import (
    UserStreak,
    DailyCheckin,
    UserGoal,
    WeeklyCheckinQuestion,
    WeeklyCheckinOption,
    UserWeeklyCheckin,
    UserWeeklyCheckinResponse,
    UserBadge,
)


@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_checkin_date', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DailyCheckin)
class DailyCheckinAdmin(admin.ModelAdmin):
    list_display = ('user', 'checkin_date', 'streak_day', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'target_count', 'current_count', 'date', 'completed', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


@admin.register(WeeklyCheckinQuestion)
class WeeklyCheckinQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'question_order', 'is_active', 'created_at')
    list_editable = ('question_order', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(WeeklyCheckinOption)
class WeeklyCheckinOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_text', 'option_order')
    list_editable = ('option_order',)
    search_fields = ('question__question_text',)


@admin.register(UserWeeklyCheckin)
class UserWeeklyCheckinAdmin(admin.ModelAdmin):
    list_display = ('user', 'week_number', 'is_available', 'is_completed', 'completed_at', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


@admin.register(UserWeeklyCheckinResponse)
class UserWeeklyCheckinResponseAdmin(admin.ModelAdmin):
    list_display = ('weekly_checkin', 'question', 'selected_option', 'created_at')
    search_fields = ('weekly_checkin__user__email', 'question__question_text')
    readonly_fields = ('created_at',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'weeks_completed', 'badge_name', 'earned_date')
    search_fields = ('user__email',)
    readonly_fields = ('earned_date',)
