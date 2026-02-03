from django.contrib import admin
from apps.checkin.models import (
    UserStreak,
    DailyCheckin,
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

from .models import BadgeTemplate, UserAppBadge

from django.contrib import admin
from django.utils.html import format_html
from .models import BadgeTemplate, UserAppBadge

@admin.register(BadgeTemplate)
class BadgeTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_type', 'order', 'days_required', 'image_tag')
    list_filter = ('badge_type',)
    search_fields = ('title', 'description')
    ordering = ('order',)
    list_editable = ('order', 'days_required')
    readonly_fields = ('image_preview',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:5px;"/>', obj.image.url)
        return "No Image"
    image_tag.short_description = "Preview"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="120" height="120" style="border-radius:10px;"/>', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image Preview"

@admin.register(UserAppBadge)
class UserAppBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_template', 'earned_at')
    list_filter = ('badge_template', 'earned_at')
    search_fields = ('user__email', 'badge_template__title')
    ordering = ('-earned_at',)
