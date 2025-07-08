class LegalDocument(models.Model):
    DOCUMENT_TYPES = [
        ('terms', 'Terms and Conditions'),
        ('privacy', 'Privacy Policy'),
    ]
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    version = models.CharField(max_length=10, default='1.0')
    is_active = models.BooleanField(default=True)
    effective_date = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_document_type_display()} - v{self.version}"
    
    class Meta:
        verbose_name = "Legal Document"
        verbose_name_plural = "Legal Documents"
        ordering = ['-created_at']


class LegalDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = LegalDocument
        fields = [
            'id', 'document_type', 'document_type_display', 
            'title', 'content', 'version', 'effective_date'
        ]
        read_only_fields = ['id']



    class TermsAndConditionsView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = LegalDocumentSerializer
    
    def get(self, request):
        """Get current Terms and Conditions"""
        try:
            terms = LegalDocument.objects.filter(
                document_type='terms',
                is_active=True
            ).first()
            
            if not terms:
                return self.bad_request_response(
                    message="Terms and Conditions not found",
                    error_code="TERMS_NOT_FOUND"
                )
            
            serializer = self.get_serializer(terms)
            
            return self.success_response(
                data=serializer.data,
                message="Terms and Conditions retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e)


class PrivacyPolicyView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = LegalDocumentSerializer
    
    def get(self, request):
        """Get current Privacy Policy"""
        try:
            privacy = LegalDocument.objects.filter(
                document_type='privacy',
                is_active=True
            ).first()
            
            if not privacy:
                return self.bad_request_response(
                    message="Privacy Policy not found",
                    error_code="PRIVACY_NOT_FOUND"
                )
            
            serializer = self.get_serializer(privacy)
            
            return self.success_response(
                data=serializer.data,
                message="Privacy Policy retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e)


# Alternative: Combined view if you prefer
class LegalDocumentView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = LegalDocumentSerializer
    
    def get(self, request, document_type):
        """Get legal document by type"""
        try:
            if document_type not in ['terms', 'privacy']:
                return self.bad_request_response(
                    message="Invalid document type",
                    error_code="INVALID_DOCUMENT_TYPE"
                )
            
            document = LegalDocument.objects.filter(
                document_type=document_type,
                is_active=True
            ).first()
            
            if not document:
                return self.bad_request_response(
                    message=f"{document_type.title()} document not found",
                    error_code="DOCUMENT_NOT_FOUND"
                )
            
            serializer = self.get_serializer(document)
            
            return self.success_response(
                data=serializer.data,
                message=f"{document.get_document_type_display()} retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e)
        

    # Option 1: Separate endpoints
path("legal/terms/", TermsAndConditionsView.as_view(), name="terms-conditions"),
path("legal/privacy/", PrivacyPolicyView.as_view(), name="privacy-policy"),

# Option 2: Combined endpoint
path("legal/<str:document_type>/", LegalDocumentView.as_view(), name="legal-document"),


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'title', 'version', 'is_active', 'effective_date']
    list_filter = ['document_type', 'is_active', 'effective_date']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']