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
        journey_reasons = [
            "Clarity to overcome doubts",
            "Confidence to share my beliefs",
        ]
        for reason in journey_reasons:
            JourneyReasonOption.objects.update_or_create(
                option=reason,
                defaults={"is_active": True},
            )
        denominations = [
            "Catholic", "Protestant", "Baptist", "Nondenominational", "Methodist",
            "Pentecostal", "Lutheran", "Evangelical", "Adventist", "Orthodox", "Other",
        ]
        for denomination in denominations:
            DenominationOption.objects.update_or_create(
                name=denomination,
                defaults={"is_active": True},
            )
        faith_goal_data = [
            {
                "question": "When faith conversations come up, where do you want more confidence?",
                "options": [
                    "I'm not always sure how to respond in the moment.",
                    "I want to explain scripture more clearly and connect it to real life.",
                    "I want my faith to grow so I can encourage and inspire others.",
                ],
            },
            {
                "question": "How would you most like to grow in your faith right now?",
                "options": [
                    "I want to speak about my faith with clarity and confidence.",
                    "I want to understand scripture more deeply and explain it clearly.",
                    "I want my faith to grow so I can uplift and lead others.",
                ],
            },
            {
                "question": "What kind of support would help you most right now?",
                "options": [
                    "Guidance on how to respond with clarity and confidence.",
                    "Clear, easy-to-understand insights from scripture I can share.",
                    "Wisdom and reflections that strengthen my faith and inspire others.",
                ],
            },
        ]
        for index, item in enumerate(faith_goal_data):
            question_obj, _ = FaithGoalQuestion.objects.update_or_create(
                question=item["question"],
                defaults={"is_active": True},
            )
            for option_text in item["options"]:
                FaithGoalOption.objects.update_or_create(
                    faith_goal_question=question_obj,
                    option=option_text,
                    defaults={"is_active": True},
                )
        tone_preference_data = [
            {
                "title": "Clear and Hopeful",
                "name": "Clear and Hopeful",
                "description": "Simple, direct, and encouraging. Speaks to God's love and faithfulness in an easily understood way.",
                "quote": "God allows us to choose because He loves us deeply. Even in our struggles, His grace is always enough.",
            },
            {
                "title": "Dynamic and Powerful",
                "name": "Dynamic and Powerful",
                "description": "Emotive, bold, and filled with vivid imagery. Designed to inspire and energize.",
                "quote": "Sin may exist, but so does God's unstoppable power to redeem, restore, and turn every story into a victory.",
            },
            {
                "title": "Practical and Everyday",
                "name": "Practical and Everyday",
                "description": "Grounded and solution-oriented, focusing on how faith applies to daily life.",
                "quote": "Sometimes life feels messy, but God uses even our mistakes to shape us and teach us how to walk in His ways.",
            },
            {
                "title": "Encouraging and Purposeful",
                "name": "Encouraging and Purposeful",
                "description": "Focuses on meaning and growth through challenges, using affirming and positive language.",
                "quote": "It's not always easy to understand, but God allows challenges so we can grow stronger in faith and closer to Him.",
            },
            {
                "title": "Uplifting and Optimistic",
                "name": "Uplifting and Optimistic",
                "description": "Highlights hope and joy even in adversity, emphasizing God's ongoing provision.",
                "quote": "Even in a broken world, God's love shines through. His plan for good will always outweigh the pain we see now.",
            },
            {
                "title": "Scholarly and Rational",
                "name": "Scholarly and Rational",
                "description": "Appeals to logic and reason, using well-structured arguments and historical/theological insights.",
                "quote": "Sin entered through humanity's choices, but God's plan through Jesus shows us the depth of His justice and mercy.",
            },
            {
                "title": "Warm and Relatable",
                "name": "Warm and Relatable",
                "description": "Conversational, empathetic, and emotionally resonant. Speaks to the heart with compassion.",
                "quote": "That's a tough question—it's okay to wrestle with it. What matters most is knowing God is with you, no matter what.",
            },
            {
                "title": "Passionate and Empowering",
                "name": "Passionate and Empowering",
                "description": "Focused on spiritual growth and perseverance, emphasizing strength and action.",
                "quote": "Sin doesn't define us—God's purpose does. You have the power to walk boldly in the freedom He's given you.",
            },
        ]
        for tone in tone_preference_data:
            TonePreferenceOption.objects.update_or_create(
                title=tone["title"],           # lookup key
                defaults={                     # only these fields get updated
                    "name": tone["name"],      # icon is NOT here — stays untouched
                    "description": tone["description"],
                    "quote": tone["quote"],
                    "is_active": True,
                },
            )
        bible_familiarity_data = [
            {
                "label": "None",
                "text1": "Clear answers when you need them most",
                "text2": "Whether you're just starting or building confidence, this path helps you find the right words.",
                "title": "Conversation Ready",
                "name": "Conversation Ready",
                "caption": "Preachly provides clear, confident responses grounded in scripture, perfect for real-life conversations when you're not sure what to say.",
            },
            {
                "label": "A Little",
                "text1": "Go deeper in understanding and conversation",
                "text2": "You already have a foundation, we'll help you build on it.",
                "title": "In-Depth",
                "name": "In-Depth",
                "caption": "Preachly will expand answers with context, scripture connections, and thoughtful explanations to help you discuss faith with clarity and confidence.",
            },
            {
                "label": "A Lot",
                "text1": "Explore the deeper structure of the Christian worldview",
                "text2": "You're ready to connect ideas, ask bigger questions, and explore deeper meaning.",
                "title": "Full Framework",
                "name": "Full Framework",
                "caption": "Preachly provides layered insights connecting scripture, theology, philosophy, and real-world application. Helping you engage in thoughtful, meaningful conversations.",
            },
        ]
        for item in bible_familiarity_data:
            BibleFamiliarityOption.objects.update_or_create(
                label=item["label"],           # lookup key — stable
                defaults={
                    "text1": item["text1"],
                    "text2": item["text2"],
                    "title": item["title"],
                    "name": item["name"],
                    "caption": item["caption"],
                    "is_active": True,
                },
            )
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
            },
        ]
        for version in bible_versions:
            BibleVersionOption.objects.update_or_create(
                api_bible_id=version["api_bible_id"],  # unique field — perfect key
                defaults={
                    "title": version["title"],
                    "subtitle": version["subtitle"],
                    "is_active": True,
                },
            )
 
        return Response({
            "success": True,
            "message": "✅ Onboarding data updated successfully! No data was deleted.",
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

@api_view(['POST'])
def populate_weekly_checkin_questions(request):
    try:
        questions_data = [
            {
                'question': 'This week, how confident did you feel talking about your faith?',
                'order': 1,
                'options': [
                    ('Not confident at all', 1),
                    ('A little hesitant', 2),
                    ('Growing more confident', 3),
                    ('Mostly confident', 4),
                    ('Very confident', 5),
                ],
            },
            {
                'question': 'When faith conversations came up, how ready did you feel to respond?',
                'order': 2,
                'options': [
                    ('Not ready at all', 1),
                    ('Felt unsure', 2),
                    ('Starting to find my footing', 3),
                    ('Mostly ready', 4),
                    ('Fully ready', 5),
                ],
            },
            {
                'question': 'How clearly did scripture speak to you this week?',
                'order': 3,
                'options': [
                    ('Not clear at all', 1),
                    ('Still confusing', 2),
                    ('Starting to make sense', 3),
                    ('Mostly clear', 4),
                    ('Crystal clear', 5),
                ],
            },
            {
                'question': 'When you reflected on your relationship with God this week, what did you feel most?',
                'order': 4,
                'options': [
                    ('Restless', 1),
                    ('Searching', 2),
                    ('Moments of peace', 3),
                    ('Mostly at peace', 4),
                    ('Deep peace', 5),
                ],
            },
            {
                'question': 'How often did you make space to pray, reflect, or seek God this week?',
                'order': 5,
                'options': [
                    ('Not at all', 1),
                    ('Rarely', 2),
                    ('A few times', 3),
                    ('Often', 4),
                    ('Every day', 5),
                ],
            },
            {
                'question': "How aware were you of God's presence in your daily life this week?",
                'order': 6,
                'options': [
                    ('Felt distant', 1),
                    ('Noticed Him occasionally', 2),
                    ('Becoming more aware', 3),
                    ('Felt His presence often', 4),
                    ('Very aware of His presence', 5),
                ],
            },
            {
                'question': 'How confident do you feel about where God is leading your faith?',
                'order': 7,
                'options': [
                    ('Very uncertain', 1),
                    ('Taking small steps', 2),
                    ('Beginning to see direction', 3),
                    ('Mostly confident', 4),
                    ('Very confident', 5),
                ],
            },
            {
                'question': 'Looking back on this week, how much spiritual growth do you see?',
                'order': 8,
                'options': [
                    ('None yet', 1),
                    ('A little growth', 2),
                    ('Noticeable growth', 3),
                    ('Strong growth', 4),
                    ('Significant growth', 5),
                ],
            },
            {
                'question': 'How encouraged did you feel in your faith this week?',
                'order': 9,
                'options': [
                    ('Not encouraged at all', 1),
                    ('Needed more encouragement', 2),
                    ('Had some encouraging moments', 3),
                    ('Felt encouraged often', 4),
                    ('Deeply encouraged', 5),
                ],
            },
            {
                'question': 'How motivated are you to keep growing in your faith next week?',
                'order': 10,
                'options': [
                    ('Not motivated right now', 1),
                    ('A small spark', 2),
                    ('Starting to feel motivated', 3),
                    ('Mostly motivated', 4),
                    ('Strongly motivated', 5),
                ],
            },
        ]
 
        created_count = 0
        updated_count = 0
 
        for q_data in questions_data:
            question, created = WeeklyCheckinQuestion.objects.update_or_create(
                question_text=q_data['question'],   # lookup key
                defaults={
                    'question_order': q_data['order'],
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
 
            for option_text, option_order in q_data['options']:
                WeeklyCheckinOption.objects.update_or_create(
                    question=question,
                    option_order=option_order,       # lookup key — unique per question
                    defaults={'option_text': option_text},
                )
 
        return Response({
            'success': True,
            'message': f'Questions processed — {created_count} created, {updated_count} updated. No data deleted.',
        }, status=status.HTTP_200_OK)
 
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}',
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
        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f'daily_modal_checkin_{user.id}_{today}'
        if cache.get(cache_key):
            return Response({
                'success': True,
                'show_modal': False,
                'message': 'Modal already shown today'
            }, status=status.HTTP_200_OK)
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
