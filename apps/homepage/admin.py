from django.contrib import admin
from apps.homepage.models import DailyVerse


@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 
        'verse_reference', 
        'bible_version', 
        'date_assigned', 
        'expires_at', 
        'is_expired', 
        'created_at'
    )
    list_filter = ('bible_version', 'date_assigned', 'expires_at')
    search_fields = ('verse_reference', 'verse_text', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user', 'bible_version')

    def user_email(self, obj):
        return obj.user.email if obj.user else "Unknown User"
    user_email.short_description = 'User Email'

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired?'
