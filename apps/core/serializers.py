from rest_framework import serializers
from apps.core.models import LegalDocument


class LegalDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = LegalDocument
        fields = [
            'id', 'document_type', 'document_type_display', 
            'title', 'content', 'created_at', 'updated_at'
        ]