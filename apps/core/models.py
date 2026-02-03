from django.db import models


class LegalDocument(models.Model):
    DOCUMENT_TYPES = [
        ("terms", "Terms and Conditions"),
        ("privacy", "Privacy Policy"),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Legal Document"
        verbose_name_plural = "Legal Documents"
