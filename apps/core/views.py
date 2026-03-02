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
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from apps.onboarding.models import (
    JourneyReasonOption,
    DenominationOption,
    FaithGoalQuestion,
    FaithGoalOption,
    TonePreferenceOption,
    BibleFamiliarityOption,
    BibleVersionOption,
)
from django.core.cache import cache
from datetime import datetime
from rest_framework.permissions import IsAuthenticated


class TermsAndConditionsView(BaseResponseMixin, generics.RetrieveAPIView):
    serializer_class = LegalDocumentSerializer

    def get(self, request, *args, **kwargs):
        """Get current Terms and Conditions"""

        try:
            terms = LegalDocument.objects.filter(
                document_type="terms", is_active=True
            ).first()

            if not terms:
                return self.bad_request_response(
                    message="Terms and Conditions not found",
                )

            serializer = self.get_serializer(terms)

            return self.success_response(
                data=serializer.data,
                message="Terms and Conditions retrieved successfully",
            )

        except Exception as e:
            return self.handle_exception(e)


class PrivacyPolicyView(BaseResponseMixin, generics.RetrieveAPIView):
    serializer_class = LegalDocumentSerializer

    def get(self, request, *args, **kwargs):
        """Get current Privacy Policy"""

        try:
            privacy = LegalDocument.objects.filter(
                document_type="privacy", is_active=True
            ).first()

            if not privacy:
                return self.bad_request_response(
                    message="Privacy Policy not found",
                )

            serializer = self.get_serializer(privacy)

            return self.success_response(
                data=serializer.data, message="Privacy Policy retrieved successfully"
            )

        except Exception as e:
            return self.handle_exception(e)


@api_view(["POST"])
def populate_onboarding_data(request):
    try:
        # 🧹 DELETE all old data
        JourneyReasonOption.objects.all().delete()
        DenominationOption.objects.all().delete()
        FaithGoalOption.objects.all().delete()
        FaithGoalQuestion.objects.all().delete()
        TonePreferenceOption.objects.all().delete()
        BibleFamiliarityOption.objects.all().delete()
        BibleVersionOption.objects.all().delete()

        # 🚀 INSERT fresh data

        # Journey Reasons
        journey_reasons = [
            "Clarity to overcome doubts",
            "Confidence to share my beliefs",
        ]
        for reason in journey_reasons:
            JourneyReasonOption.objects.create(
                option=reason, is_active=True
            )

        # Denominations
        denominations = [
            "Catholic", "Protestant", "Baptist", "Nondenominational", "Methodist",
            "Pentecostal", "Lutheran", "Evangelical", "Adventist", "Orthodox", "Other",
        ]
        for denomination in denominations:
            DenominationOption.objects.create(
                name=denomination, is_active=True
            )

        # Faith Goal Questions and Options
        faith_goal_data = [
            {
                "question": "What's holding you back from confidently living and sharing your faith?",
                "options": [
                    "I feel unsure how to respond to questions or doubts about my faith.",
                    "I struggle to find the right words to share scripture effectively.",
                    "I feel I need a deeper connection to God's word before I can inspire others.",
                ],
            },
            {
                "question": "How do you hope to grow in your walk with God?",
                "options": [
                    "I want to learn how to speak about my faith with confidence and clarity.",
                    "I want to strengthen my understanding of scripture and apply it to my life.",
                    "I want to inspire and encourage others through my faith journey.",
                ],
            },
            {
                "question": "What would help you feel more equipped to achieve your faith goals?",
                "options": [
                    "Practical tools to respond to objections and questions about faith.",
                    "Daily scripture insights that I can share with others or reflect on.",
                    "Clear and inspired guidance rooted in scripture.",
                ],
            },
        ]
        for item in faith_goal_data:
            question_obj = FaithGoalQuestion.objects.create(
                question=item["question"], is_active=True
            )
            for option in item["options"]:
                FaithGoalOption.objects.create(
                    faith_goal_question=question_obj,
                    option=option,
                    is_active=True,
                )

        # Tone Preferences
        tone_preference_data = [
            {
                "title": "Clear and Hopeful",
                "name": "Clear and Hopeful",
                "description": "Simple, direct, and encouraging. Speaks to God’s love and faithfulness in an easily understood way.",
                "quote": "God allows us to choose because He loves us deeply. Even in our struggles, His grace is always enough.",
            },
            {
                "title": "Dynamic and Powerful",
                "name": "Dynamic and Powerful",
                "description": "Emotive, bold, and filled with vivid imagery. Designed to inspire and energize",
                "quote": "Sin may exist, but so does God’s unstoppable power to redeem, restore, and turn every story into a victory.",
            },
            {
                "title": "Practical and Everyday",
                "name": "Practical and Everyday",
                "description": "Grounded and solution-oriented, focusing on how faith applies to daily life",
                "quote": "Sometimes life feels messy, but God uses even our mistakes to shape us and teach us how to walk in His ways.",
            },
            {
                "title": "Encouraging and Purposeful",
                "name": "Encouraging and Purposeful",
                "description": "Focuses on meaning and growth through challenges, using affirming and positive language",
                "quote": "It’s not always easy to understand, but God allows challenges so we can grow stronger in faith and closer to Him.",
            },
            {
                "title": "Uplifting and Optimistic",
                "name": "Uplifting and Optimistic",
                "description": "Highlights hope and joy even in adversity, emphasizing God’s ongoing provision",
                "quote": "Even in a broken world, God’s love shines through. His plan for good will always outweigh the pain we see now.",
            },
            {
                "title": "Scholarly and Rational",
                "name": "Scholarly and Rational",
                "description": "Appeals to logic and reason, using well-structured arguments and historical/theological insights.",
                "quote": "Sin entered through humanity’s choices, but God’s plan through Jesus shows us the depth of His justice and mercy.",
            },
            {
                "title": "Warm and Relatable",
                "name": "Warm and Relatable",
                "description": "Conversational, empathetic, and emotionally resonant. Speaks to the heart with compassion.",
                "quote": "That’s a tough question—it’s okay to wrestle with it. What matters most is knowing God is with you, no matter what.",
            },
            {
                "title": "Passionate and Empowering",
                "name": "Passionate and Empowering",
                "description": "Focused on spiritual growth and perseverance, emphasizing strength and action",
                "quote": "Sin doesn’t define us—God’s purpose does. You have the power to walk boldly in the freedom He’s given you.",
            },
        ]
        for tone in tone_preference_data:
            TonePreferenceOption.objects.create(
                title=tone["title"],
                name=tone["name"],
                description=tone["description"],
                quote=tone["quote"],
                is_active=True
            )

        # Bible Familiarity
        bible_familiarity_data = [
            {
                "label": "None",
                "text1": "New to the Word? No problem!",
                "text2": "",
                "title": "Simplified Responses",
                "name": "Simplified Responses",
                "caption": "Preachly will break things down in an easy-to-understand way, offering clear, simple explanations to help you build a strong foundation.",
            },
            {
                "label": "A Little",
                "text1": "A great foundation! Let's go deeper",
                "text2": "You have some knowledge, and we'll build on it!",
                "title": "In-Depth Responses",
                "name": "In-Depth Responses",
                "caption": "Preachly's answers will include context connections, and deeper insights to enrich your understanding",
            },
            {
                "label": "A Lot",
                "text1": "Ready for the deep dive?",
                "text2": "",
                "title": "Multi-Argumentation Responses",
                "name": "Multi-Argumentation Responses",
                "caption": "Preachly will provide multi-layered explanations, exploring different perspectives, theological arguments, and scriptural connections to help you sharpen your understanding",
            },
        ]
        for item in bible_familiarity_data:
            BibleFamiliarityOption.objects.create(
                label=item["label"],
                text1=item["text1"],
                text2=item["text2"],
                title=item["title"],
                name=item["name"],
                caption=item["caption"],
                is_active=True
            )

        # Bible Versions
        bible_versions = [
            {
                "api_bible_id": "de4e12af7f28f599-01",
                "title": "King James (Authorized) Version (KJV)",
                "subtitle": "Classic 1611 English Protestant translation",
            },
            {
                "api_bible_id": "9879dbb7cfe39e4d-01",
                "title": "World English Bible (WEB)",
                "subtitle": "Modern English public domain translation",
            },
            {
                "api_bible_id": "06125adad2d5898a-01",
                "title": "The Holy Bible, American Standard Version (ASV)",
                "subtitle": "1901 American English revision",
            }
        ]
        for version in bible_versions:
            BibleVersionOption.objects.create(
                api_bible_id=version["api_bible_id"],
                title=version["title"],
                subtitle=version["subtitle"],
                is_active=True
            )

        return Response({
            "success": True,
            "message": "✅ All onboarding data wiped & repopulated successfully!",
            "status_code": 200,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"❌ Error: {str(e)}",
            "status_code": 500,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class APIGuideView(TemplateView):
    template_name = "guide/api-guide.html"


class FakeDataAPIView(BaseResponseMixin, APIView):
    """
    API to generate fake data for development and testing
    """

    permission_classes = [permissions.AllowAny]  # Anyone can access

    def post(self, request):
        action = request.data.get("action")

        if not action:
            return self.error_response(
                message="Action is required. Available actions: create_users, create_admin, create_test_users, clear_users, get_summary",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if action == "create_users":
                count = int(request.data.get("count", 10))
                if count > 50:  # Limit to prevent abuse
                    return self.error_response(
                        message="Maximum 50 users can be created at once",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                users = FakeDataGenerator.create_fake_users(count)
                return self.success_response(
                    data=users,
                    message=f"{len(users)} fake users created successfully",
                    status_code=status.HTTP_201_CREATED,
                )

            elif action == "create_admin":
                admin_data = FakeDataGenerator.create_admin_user()
                return self.success_response(
                    data=admin_data,
                    message="Admin user creation processed",
                    status_code=status.HTTP_201_CREATED,
                )

            elif action == "create_test_users":
                test_users = FakeDataGenerator.create_test_users()
                return self.success_response(
                    data=test_users,
                    message=f"{len(test_users)} test users created successfully",
                    status_code=status.HTTP_201_CREATED,
                )

            elif action == "clear_users":
                result = FakeDataGenerator.clear_all_users()
                return self.success_response(
                    data=result,
                    message="Users cleared successfully",
                    status_code=status.HTTP_200_OK,
                )

            elif action == "get_summary":
                summary = FakeDataGenerator.get_users_summary()
                return self.success_response(
                    data=summary,
                    message="Users summary retrieved successfully",
                    status_code=status.HTTP_200_OK,
                )

            else:
                return self.error_response(
                    message="Invalid action. Available actions: create_users, create_admin, create_test_users, clear_users, get_summary",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return self.error_response(
                message=f"Error processing request: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



# serializers.py weekly check-in questions and options
from rest_framework import serializers
from apps.checkin.models import WeeklyCheckinQuestion, WeeklyCheckinOption

class WeeklyCheckinOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyCheckinOption
        fields = ['id', 'option_text', 'option_order']

class WeeklyCheckinQuestionSerializer(serializers.ModelSerializer):
    options = WeeklyCheckinOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = WeeklyCheckinQuestion
        fields = ['id', 'question_text', 'question_order', 'is_active', 'created_at', 'options']


# Views for Weekly Check-in population and retrieval

@api_view(['POST'])
def populate_weekly_checkin_questions(request):
    """
    API endpoint to populate all weekly check-in questions and their options
    Call this API via POST request to automatically create all questions
    """
    try:
        # Clear existing data (optional - remove if you don't want to clear)
        WeeklyCheckinQuestion.objects.all().delete()
        
        questions_data = [
            {
                'question': 'This week, how confident did you feel sharing your faith with others?',
                'options': ['Not at all', 'Hesitant', 'Growing in boldness', 'Mostly confident', 'Completely confident']
            },
            {
                'question': 'When conversations about faith came up, how prepared did you feel to respond?',
                'options': ['Not prepared at all', 'Caught off guard', 'Finding my footing', 'Mostly prepared', 'Fully prepared']
            },
            {
                'question': 'How clearly did scripture speak to you this week?',
                'options': ['Not clear at all', 'A bit cloudy', 'Starting to make sense', 'Mostly clear', 'Crystal clear']
            },
            {
                'question': 'When reflecting on your relationship with God, how much peace did you feel?',
                'options': ['Restless', 'Wrestling with it', 'Finding moments of peace', 'Mostly at peace', 'Completely at peace']
            },
            {
                'question': 'How often did you create space to pray, reflect, or listen for God\'s voice?',
                'options': ['Not at all', 'Rarely, but I want to more', 'Somewhat consistent', 'Often', 'Every day']
            },
            {
                'question': 'How present did God feel in your daily life this week?',
                'options': ['Distant', 'There in moments', 'Becoming more aware', 'Mostly present', 'Very near']
            },
            {
                'question': 'How confident do you feel about the direction of your faith journey?',
                'options': ['Uncertain', 'Taking small steps', 'Finding my rhythm', 'Mostly confident', 'Very confident']
            },
            {
                'question': 'Looking back on this week, how much growth do you see in your faith?',
                'options': ['None at all', 'A little, but I want more', 'Some noticeable growth', 'A lot of growth', 'Tremendous growth']
            },
            {
                'question': 'How often did you feel uplifted and encouraged in your walk with God this week?',
                'options': ['Not at all', 'Needed more encouragement', 'Had some encouraging moments', 'Often', 'Constantly']
            },
            {
                'question': 'How motivated are you to continue deepening your faith in the coming week?',
                'options': ['Not at all', 'A little spark of motivation', 'Starting to feel inspired', 'Mostly motivated', 'Fully motivated']
            }
        ]

        created_questions = []
        
        for index, question_data in enumerate(questions_data, 1):
            # Create question
            question = WeeklyCheckinQuestion.objects.create(
                question_text=question_data['question'],
                question_order=index,
                is_active=True
            )
            
            # Create options for this question
            for option_index, option_text in enumerate(question_data['options'], 1):
                WeeklyCheckinOption.objects.create(
                    question=question,
                    option_text=option_text,
                    option_order=option_index
                )
            
            created_questions.append(question)
        
        # Serialize the created questions with their options
        serializer = WeeklyCheckinQuestionSerializer(created_questions, many=True)
        
        return Response({
            'success': True,
            'message': f'Successfully created {len(created_questions)} questions with their options',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error creating questions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_weekly_checkin_questions(request):
    """
    API endpoint to retrieve all weekly check-in questions with their options
    """
    try:
        questions = WeeklyCheckinQuestion.objects.filter(is_active=True).prefetch_related('options')
        serializer = WeeklyCheckinQuestionSerializer(questions, many=True)
        
        return Response({
            'success': True,
            'count': len(questions),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving questions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_modal_checkin(request):
    """
    API endpoint to check if daily modal should be shown to user.
    Returns true only once per day per user.
    On subsequent requests the same day, returns false.
    Resets the next day.
    """
    try:
        user = request.user
        
        # Create cache key with user ID and today's date
        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f'daily_modal_checkin_{user.id}_{today}'
        
        # Check if user already accessed modal today
        if cache.get(cache_key):
            # Already showed modal today
            return Response({
                'success': True,
                'show_modal': False,
                'message': 'Modal already shown today'
            }, status=status.HTTP_200_OK)
        
        # First time accessing today - set cache and return true
        # Cache expires in 24 hours
        cache.set(cache_key, True, 86400)
        
        return Response({
            'success': True,
            'show_modal': True,
            'message': 'Show modal to user'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'show_modal': False,
            'message': f'Error checking daily modal: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
