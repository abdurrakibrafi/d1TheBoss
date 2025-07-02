from django.contrib import admin
from apps.onboarding.models import (
    JourneyReasonOption, JourneyReason,
    DenominationOption, Denomination,
    FaithGoalQuestion, FaithGoalOption, FaithGoal,
    TonePreferenceOption, TonePreference,
    BibleFamiliarityOption, BibleFamiliarity,
    BibleVersionOption, BibleVersion
)

# 01. Journey Reason Options
@admin.register(JourneyReasonOption)
class JourneyReasonOptionAdmin(admin.ModelAdmin):
    list_display = ['option', 'is_active', 'created_at']
    search_fields = ['option']
    list_filter = ['is_active']

@admin.register(JourneyReason)
class JourneyReasonAdmin(admin.ModelAdmin):
    list_display = ['user', 'journey_reason', 'created_at']
    search_fields = ['user__email', 'journey_reason__option']
    list_filter = ['journey_reason']


# 03. Denomination Options
@admin.register(DenominationOption)
class DenominationOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['is_active']

@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ['user', 'denomination_option', 'name', 'created_at']
    search_fields = ['user__email', 'name']
    list_filter = ['denomination_option']


# 05. Faith Goal Questions & Options
@admin.register(FaithGoalQuestion)
class FaithGoalQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'is_active', 'created_at']
    search_fields = ['question']
    list_filter = ['is_active']

@admin.register(FaithGoalOption)
class FaithGoalOptionAdmin(admin.ModelAdmin):
    list_display = ['faith_goal_question', 'option', 'is_active']
    search_fields = ['option', 'faith_goal_question__question']
    list_filter = ['is_active', 'faith_goal_question']

@admin.register(FaithGoal)
class FaithGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'faith_goal_option', 'text', 'created_at']
    search_fields = ['user__email', 'text']
    list_filter = ['faith_goal_option']


# 08. Tone Preference Options
@admin.register(TonePreferenceOption)
class TonePreferenceOptionAdmin(admin.ModelAdmin):
    list_display = ['option_title', 'option_subtitle', 'is_active']
    search_fields = ['option_title', 'option_subtitle']
    list_filter = ['is_active']

@admin.register(TonePreference)
class TonePreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'tone_preference_option']
    search_fields = ['user__email', 'tone_preference_option__option_title']
    list_filter = ['tone_preference_option']


# 10. Bible Familiarity
@admin.register(BibleFamiliarityOption)
class BibleFamiliarityOptionAdmin(admin.ModelAdmin):
    list_display = ['option', 'is_active']
    search_fields = ['option']
    list_filter = ['is_active']

@admin.register(BibleFamiliarity)
class BibleFamiliarityAdmin(admin.ModelAdmin):
    list_display = ['user', 'bible_familiarity_option', 'text']
    search_fields = ['user__email', 'text']
    list_filter = ['bible_familiarity_option']


# 12. Bible Versions
@admin.register(BibleVersionOption)
class BibleVersionOptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'is_active']
    search_fields = ['title', 'subtitle']
    list_filter = ['is_active']

@admin.register(BibleVersion)
class BibleVersionAdmin(admin.ModelAdmin):
    list_display = ['user', 'bible_version_option']
    search_fields = ['user__email', 'bible_version__title']
    list_filter = ['bible_version_option']

