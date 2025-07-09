from django.db import models
from django.conf import settings


class JourneyReasonOption(models.Model):
    option = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.option}"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "01. Journey Reason Options"


class JourneyReason(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    journey_reason = models.ForeignKey(
        JourneyReasonOption, on_delete=models.CASCADE, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.journey_reason.option}"  # FIX THIS

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "02. Journey Reasons"


class DenominationOption(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "03. Denomination Options"


class Denomination(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    denomination_option = models.ForeignKey(
        DenominationOption, on_delete=models.CASCADE, blank=True, null=True
    )
    name = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "04. Denominations"


class FaithGoalQuestion(models.Model):
    question = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question}"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "05. Faith Goal Questions"


class FaithGoalOption(models.Model):
    faith_goal_question = models.ForeignKey(
        FaithGoalQuestion, on_delete=models.CASCADE, blank=True, null=True
    )
    option = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.faith_goal_question:
            return self.faith_goal_question.question
        return "Option (no question)"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "06. Faith Goal Options"


class FaithGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    faith_goal_option = models.ForeignKey(
        FaithGoalOption, on_delete=models.CASCADE, blank=True, null=True
    )
    text = models.CharField(max_length=250, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.faith_goal_option and self.faith_goal_option.faith_goal_question:
            return self.faith_goal_option.faith_goal_question.question
        return "Faith Goal (incomplete)"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "07. Faith Goals"


class TonePreferenceOption(models.Model):
    option_title = models.CharField(max_length=100, blank=True, null=True)
    option_subtitle = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.option_title}"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "08. Tone Preference Options"


class TonePreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    tone_preference_option = models.ForeignKey(
        TonePreferenceOption, on_delete=models.CASCADE, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tone_preference_option.option_title

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "09. Tone Preferences"


class BibleFamiliarityOption(models.Model):
    option = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.option

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "10. Bible Familiarity Options"


class BibleFamiliarity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    bible_familiarity_option = models.ForeignKey(
        BibleFamiliarityOption, on_delete=models.CASCADE, blank=True, null=True
    )
    text = models.CharField(max_length=250, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bible_familiarity_option.option}"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "11. Bible Familiarity"


class BibleVersionOption(models.Model):
    title = models.CharField(max_length=250, blank=True, null=True)
    subtitle = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "12. Bible Version Options"


class BibleVersion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    bible_version_option = models.ForeignKey(
        BibleVersionOption, on_delete=models.CASCADE, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bible_version_option.title}"

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "13. Bible Versions"
