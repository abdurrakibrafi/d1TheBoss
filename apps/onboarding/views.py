from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.core.utils.mixins import BaseResponseMixin
from apps.onboarding.serializers import (
    DenominationOptionSerializer,
    DenominationSerializer,
    FaithGoalOptionSerializer,
    FaithGoalSerializer,
    JourneyReasonOptionSerializer,
    JourneyReasonSerializer,
    TonePreferenceOptionSerializer,
    TonePreferenceSerializer,
    BibleFamiliarityOptionSerializer,
    BibleFamiliaritySerializer,
    BibleVersionOptionSerializer,
    BibleVersionSerializer,
    OnboardingOptionsSerializer, 
    UserOnboardingProgressSerializer,
    UserOnboardingSummarySerializer,

)
from apps.onboarding.models import (
    DenominationOption,
    Denomination,
    FaithGoalOption,
    FaithGoalQuestion,
    FaithGoal,
    JourneyReasonOption,
    JourneyReason,
    TonePreferenceOption,
    TonePreference,
    BibleFamiliarityOption,
    BibleFamiliarity,
    BibleVersionOption,
    BibleVersion
)

class OnboardingOptionsView(BaseResponseMixin, generics.GenericAPIView):
    """Get all onboarding options in one call"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            data = {
                'journey_reasons': JourneyReasonOption.objects.filter(is_active=True),
                'denominations': DenominationOption.objects.filter(is_active=True),  # Remove is_parent=True
                'faith_goal_questions': FaithGoalQuestion.objects.filter(is_active=True),
                'tone_preferences': TonePreferenceOption.objects.filter(is_active=True),
                'bible_familiarity': BibleFamiliarityOption.objects.filter(is_active=True),
                'bible_versions': BibleVersionOption.objects.filter(is_active=True),
            }
            serializer = OnboardingOptionsSerializer(data)
            return self.success_response(
                data=serializer.data,
                message="Onboarding options retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
        

# USER SELECTION VIEWS (GET/POST)

class JourneyReasonView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JourneyReasonSerializer
    
    def get(self, request):
        try:
            journey = JourneyReason.objects.filter(user=request.user).first()
            if journey:
                serializer = self.serializer_class(journey)
                return self.success_response(
                    data=serializer.data,
                    message="Journey reason retrieved successfully"
                )
            return self.success_response(
                data=None,
                message="No journey reason found for user"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            # Delete existing first (one choice only)
            JourneyReason.objects.filter(user=request.user).delete()
            
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Journey reason saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class DenominationView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DenominationSerializer
    
    def get(self, request):
        try:
            denomination = Denomination.objects.filter(user=request.user).first()
            if denomination:
                serializer = self.serializer_class(denomination)
                return self.success_response(
                    data=serializer.data,
                    message="Denomination retrieved successfully"
                )
            return self.success_response(
                data=None,
                message="No denomination found for user"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            Denomination.objects.filter(user=request.user).delete()
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Denomination saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class FaithGoalView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FaithGoalSerializer
    
    def get(self, request):
        try:
            goals = FaithGoal.objects.filter(user=request.user)
            serializer = self.serializer_class(goals, many=True)
            return self.success_response(
                data=serializer.data,
                message="Faith goals retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Faith goal saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class TonePreferenceView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TonePreferenceSerializer
    
    def get(self, request):
        try:
            tone = TonePreference.objects.filter(user=request.user).first()
            if tone:
                serializer = self.serializer_class(tone)
                return self.success_response(
                    data=serializer.data,
                    message="Tone preference retrieved successfully"
                )
            return self.success_response(
                data=None,
                message="No tone preference found for user"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            TonePreference.objects.filter(user=request.user).delete()
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Tone preference saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class BibleFamiliarityView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BibleFamiliaritySerializer
    
    def get(self, request):
        try:
            familiarity = BibleFamiliarity.objects.filter(user=request.user).first()
            if familiarity:
                serializer = self.serializer_class(familiarity)
                return self.success_response(
                    data=serializer.data,
                    message="Bible familiarity retrieved successfully"
                )
            return self.success_response(
                data=None,
                message="No bible familiarity found for user"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            BibleFamiliarity.objects.filter(user=request.user).delete()
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Bible familiarity saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class BibleVersionView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BibleVersionSerializer
    
    def get(self, request):
        try:
            version = BibleVersion.objects.filter(user=request.user).first()
            if version:
                serializer = self.serializer_class(version)
                return self.success_response(
                    data=serializer.data,
                    message="Bible version retrieved successfully"
                )
            return self.success_response(
                data=None,
                message="No bible version found for user"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def post(self, request):
        try:
            BibleVersion.objects.filter(user=request.user).delete()
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return self.created_response(
                    data=serializer.data,
                    message="Bible version saved successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)


class OnboardingProgressView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            serializer = UserOnboardingProgressSerializer(request.user.profile)
            return self.success_response(
                data=serializer.data,
                message="Onboarding progress retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def patch(self, request):
        try:
            serializer = UserOnboardingProgressSerializer(
                request.user.profile, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return self.updated_response(
                    data=serializer.data,
                    message="Onboarding progress updated successfully"
                )
            return self.bad_request_response(
                message="Invalid data provided",
                errors=serializer.errors
            )
        except Exception as exc:
            return self.handle_exception(exc)

class OnboardingSummaryView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            serializer = UserOnboardingSummarySerializer(request.user)
            return self.success_response(
                data=serializer.data,
                message="Onboarding summary retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

class OnboardingStatusView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            
            # Calculate progress percentage based on current step
            progress_percentage = (profile.onboarding_step / 7) * 100 if profile.onboarding_step else 0
            
            return self.success_response(
                data={
                    "onboarding_completed": profile.onboarding_completed,
                    "current_step": profile.onboarding_step,
                    "completed_at": profile.onboarding_completed_at,
                    "progress_percentage": progress_percentage
                }
            )
        except Exception as exc:
            return self.handle_exception(exc)

class CompleteOnboardingView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            profile = request.user.profile
            profile.onboarding_completed = True
            profile.onboarding_completed_at = timezone.now()
            profile.onboarding_step = 7
            profile.save()
            
            return self.success_response(
                message="Onboarding completed successfully",
                data={
                    "onboarding_completed": True,
                    "completed_at": profile.onboarding_completed_at,
                    "progress_percentage": 100
                }
            )
        except Exception as exc:
            return self.handle_exception(exc)

