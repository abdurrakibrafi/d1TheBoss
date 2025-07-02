from django.db import models

class JourneyReasonOption(models.Model):
    option = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.option}"
    
    class Meta:
        verbose_name_plural = ". Journey Reason Options"

class JourneyReason(models.Model):
    journey_reason = models.ForeignKey(JourneyReasonOption, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "2. Journey Reasons"

class Denomination(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        related_name="subdenominations",
        on_delete=models.CASCADE
    )
    is_parent = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "3. Denominations"

class FaithGoalQuestion(models.Model):
    question = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question}"
    
    class Meta:
        verbose_name_plural = "4. Faith Goal Questions"

    
class FaithGoalOption(models.Model):
    faith_goal_question = models.ForeignKey(FaithGoalQuestion, on_delete=models.CASCADE, blank=True, null=True)
    option = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.faith_goal_question.question} - {self.option}"
    
    class Meta:
        verbose_name_plural = "5. Faith Goal Options"

class FaithGoal(models.Model):
    faith_goal_option = models.ForeignKey(FaithGoalOption, on_delete=models.CASCADE, blank=True, null=True)
    text = models.CharField(max_length=250, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "6. Faith Goals"

class TonePreferenceOption(models.Model):
    option_title = models.CharField(max_length=100, blank=True, null=True)
    option_subtitle = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f"{self.option_title}"
    
    class Meta:
        verbose_name_plural = "7. Tone Preference Options"

class TonePreference(models.Model):
    tone_preference_option = models.ForeignKey(TonePreferenceOption, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tone_preference_option.option_title
    
    class Meta:
        verbose_name_plural = "8. Tone Preferences"
    
class BibleFamiliarityOption(models.Model):
    option = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.option
    
    class Meta:
        verbose_name_plural = "9. Bible Familiarity Options"


class BibleFamiliarity(models.Model):
    bible_familiarity = models.ForeignKey(BibleFamiliarityOption, on_delete=models.CASCADE, blank=True, null=True)
    text = models.CharField(max_length=250, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bible_familiarity.option}"
    
    class Meta:
        verbose_name_plural = "10. Bible Familiarity"
    
class BibleVersionOption(models.Model):
    title = models.CharField(max_length=250, blank=True, null=True)
    subtitle = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.CharField(max_length=250, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "11. Bible Version Options"


class BibleVersion(models.Model):
    bible_version = models.ForeignKey(BibleVersionOption, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bible_version.title}"
    
    class Meta:
        verbose_name_plural = "12. Bible Versions"



    

    

