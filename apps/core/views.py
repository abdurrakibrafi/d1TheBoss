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
from rest_framework.decorators import api_view
from rest_framework import status
from apps.onboarding.models import (
    JourneyReasonOption, DenominationOption, FaithGoalQuestion, 
    FaithGoalOption, TonePreferenceOption, BibleFamiliarityOption, 
    BibleVersionOption
)


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



@api_view(['POST'])
def populate_onboarding_data(request):
    try:
        # Journey Reasons
        journey_reasons = [
            "Clarity to overcome doubts",
            "Confidence to share my beliefs"
        ]
        
        for reason in journey_reasons:
            JourneyReasonOption.objects.get_or_create(
                option=reason,
                defaults={'is_active': True}
            )

        # Denominations
        denominations = [
            "Catholic", "Protestant", "Baptist", "Nondenominational",
            "Methodist", "Pentecostal", "Lutheran", "Evangelical",
            "Adventist", "Orthodox", "Other"
        ]
        
        for denomination in denominations:
            DenominationOption.objects.get_or_create(
                name=denomination,
                defaults={'is_active': True}
            )

        # Faith Goal Questions and Options
        faith_goal_data = [
            {
                "question": "What's holding you back from confidently living and sharing your faith?",
                "options": [
                    "I feel unsure how to respond to questions or doubts about my faith.",
                    "I struggle to find the right words to share scripture effectively.",
                    "I feel I need a deeper connection to God's word before I can inspire others."
                ]
            },
            {
                "question": "How do you hope to grow in your walk with God?",
                "options": [
                    "I want to learn how to speak about my faith with confidence and clarity.",
                    "I want to strengthen my understanding of scripture and apply it to my life.",
                    "I want to inspire and encourage others through my faith journey."
                ]
            },
            {
                "question": "What would help you feel more equipped to achieve your faith goals?",
                "options": [
                    "Practical tools to respond to objections and questions about faith.",
                    "Daily scripture insights that I can share with others or reflect on.",
                    "Clear and inspired guidance rooted in scripture."
                ]
            }
        ]

        for item in faith_goal_data:
            question_obj, created = FaithGoalQuestion.objects.get_or_create(
                question=item["question"],
                defaults={'is_active': True}
            )
            
            for option in item["options"]:
                FaithGoalOption.objects.get_or_create(
                    faith_goal_question=question_obj,
                    option=option,
                    defaults={'is_active': True}
                )

        # Tone Preferences
        tone_preferences = [
            "Clear and Hopeful",
            "Dynamic and Powerful",
            "Practical and Everyday",
            "Encouraging and Purposeful",
            "Uplifting and Optimistic",
            "Scholarly and Rational",
            "Warm and Relatable",
            "Passionate and Empowering"
        ]
        
        for tone in tone_preferences:
            TonePreferenceOption.objects.get_or_create(
                option_title=tone,
                defaults={'is_active': True}
            )

        # Bible Familiarity
        bible_familiarity = ["None", "A Little", "A Lot"]
        
        for familiarity in bible_familiarity:
            BibleFamiliarityOption.objects.get_or_create(
                option=familiarity,
                defaults={'is_active': True}
            )

        # Bible Versions
        bible_versions = [
            "KJV (King James Version)",
            "WEB (World English Bible)",
            "ASV (American Standard Version)",
            "ESV (English Standard Version)",
            "NLT (New Living Translation)"
        ]
        
        for version in bible_versions:
            BibleVersionOption.objects.get_or_create(
                title=version,
                defaults={'is_active': True}
            )

        return Response({
            "success": True,
            "message": "All onboarding data populated successfully!",
            "status_code": 200
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error populating data: {str(e)}",
            "status_code": 500
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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