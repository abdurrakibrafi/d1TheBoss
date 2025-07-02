from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Denomination(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

        from django.db import models

class Denomination(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subdenominations',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Denomination'
        verbose_name_plural = 'Denominations'

    def __str__(self):
        return self.name



class FaithGoal(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class JourneyReason(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TonePreference(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class BibleFamiliarity(models.Model):
    level = models.CharField(max_length=50)  # None, A Little, A Lot
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)  # For ordering None=0, A Little=1, A Lot=2
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.level

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Bible Familiarities"


class BibleVersion(models.Model):
    name = models.CharField(max_length=200)  # Full name
    abbreviation = models.CharField(max_length=20)  # RSVCE, NIV, CSB
    copyright_info = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Onboarding choices
    denomination = models.ForeignKey(Denomination, on_delete=models.SET_NULL, null=True, blank=True)
    faith_goal = models.ForeignKey(FaithGoal, on_delete=models.SET_NULL, null=True, blank=True)
    journey_reason = models.ForeignKey(JourneyReason, on_delete=models.SET_NULL, null=True, blank=True)
    tone_preference = models.ForeignKey(TonePreference, on_delete=models.SET_NULL, null=True, blank=True)
    bible_familiarity = models.ForeignKey(BibleFamiliarity, on_delete=models.SET_NULL, null=True, blank=True)
    bible_version = models.ForeignKey(BibleVersion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Onboarding status
    onboarding_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Profile"

    @property
    def onboarding_progress_percentage(self):
        """Calculate onboarding completion percentage"""
        total_fields = 6
        completed_fields = sum([
            1 if self.denomination else 0,
            1 if self.faith_goal else 0,
            1 if self.journey_reason else 0,
            1 if self.tone_preference else 0,
            1 if self.bible_familiarity else 0,
            1 if self.bible_version else 0,
        ])
        return int((completed_fields / total_fields) * 100)

    @property
    def current_onboarding_step(self):
        """Get current onboarding step (1-7)"""
        if not self.denomination:
            return 1
        elif not self.faith_goal:
            return 2
        elif not self.journey_reason:
            return 3
        elif not self.tone_preference:
            return 4
        elif not self.bible_familiarity:
            return 5
        elif not self.bible_version:
            return 6
        else:
            return 7  # Completed

    def is_onboarding_complete(self):
        """Check if all onboarding fields are filled"""
        return all([
            self.denomination,
            self.faith_goal,
            self.journey_reason, 
            self.tone_preference,
            self.bible_familiarity,
            self.bible_version
        ])

    class Meta:
        ordering = ['-created_at']


class OnboardingProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_progress')
    current_step = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Step {self.current_step}"

    class Meta:
        verbose_name_plural = "Onboarding Progress"