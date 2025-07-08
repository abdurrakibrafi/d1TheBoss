from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.core.utils.mixins import BaseResponseMixin
from apps.core.utils.fake_user_data import FakeDataGenerator
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import generics
from apps.core.serializers import LegalDocumentSerializer
from apps.core.models import LegalDocument


class TermsAndConditionsView(BaseResponseMixin, generics.RetrieveAPIView):
    serializer_class = LegalDocumentSerializer

    def get(self, request, *args, **kwargs):
        """Get current Terms and Conditions"""

        try:
            terms = LegalDocument.objects.filter(
                document_type='terms',
                is_active=True
            ).first()

            if not terms:
                return self.bad_request_response(
                    message="Terms and Conditions not found",
                )

            serializer = self.get_serializer(terms)

            return self.success_response(
                data=serializer.data,
                message="Terms and Conditions retrieved successfully"
            )

        except Exception as e:  
            return self.handle_exception(e)
        

class PrivacyPolicyView(BaseResponseMixin, generics.RetrieveAPIView):
    serializer_class = LegalDocumentSerializer

    def get(self, request, *args, **kwargs):
        """Get current Privacy Policy"""    

        try:
            privacy = LegalDocument.objects.filter(
                document_type='privacy',
                is_active=True
            ).first()

            if not privacy:
                return self.bad_request_response(
                    message="Privacy Policy not found",
                )

            serializer = self.get_serializer(privacy)

            return self.success_response(
                data=serializer.data,
                message="Privacy Policy retrieved successfully"
            )

        except Exception as e:
            return self.handle_exception(e)










































class APIGuideView(TemplateView):
    template_name = "guide/api-guide.html"

class FakeDataAPIView(BaseResponseMixin, APIView):
    """
    API to generate fake data for development and testing
    """
    permission_classes = [permissions.AllowAny]  # Anyone can access
    
    def post(self, request):
        action = request.data.get('action')
        
        if not action:
            return self.error_response(
                message="Action is required. Available actions: create_users, create_admin, create_test_users, clear_users, get_summary",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if action == 'create_users':
                count = int(request.data.get('count', 10))
                if count > 50:  # Limit to prevent abuse
                    return self.error_response(
                        message="Maximum 50 users can be created at once",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                users = FakeDataGenerator.create_fake_users(count)
                return self.success_response(
                    data=users,
                    message=f"{len(users)} fake users created successfully",
                    status_code=status.HTTP_201_CREATED
                )
            
            elif action == 'create_admin':
                admin_data = FakeDataGenerator.create_admin_user()
                return self.success_response(
                    data=admin_data,
                    message="Admin user creation processed",
                    status_code=status.HTTP_201_CREATED
                )
            
            elif action == 'create_test_users':
                test_users = FakeDataGenerator.create_test_users()
                return self.success_response(
                    data=test_users,
                    message=f"{len(test_users)} test users created successfully",
                    status_code=status.HTTP_201_CREATED
                )
            
            elif action == 'clear_users':
                result = FakeDataGenerator.clear_all_users()
                return self.success_response(
                    data=result,
                    message="Users cleared successfully",
                    status_code=status.HTTP_200_OK
                )
            
            elif action == 'get_summary':
                summary = FakeDataGenerator.get_users_summary()
                return self.success_response(
                    data=summary,
                    message="Users summary retrieved successfully",
                    status_code=status.HTTP_200_OK
                )
            
            else:
                return self.error_response(
                    message="Invalid action. Available actions: create_users, create_admin, create_test_users, clear_users, get_summary",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return self.error_response(
                message=f"Error processing request: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )