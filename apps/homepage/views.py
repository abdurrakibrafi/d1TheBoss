from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.homepage.services.home_page_bible_api import DailyVerseService
from .serializers import DailyVerseSerializer 
from apps.core.utils.mixins import BaseResponseMixin
from django.utils import timezone

class DailyVerseView(BaseResponseMixin, APIView):
    """
    Get daily verse for authenticated user
    - Same verse for 24 hours
    - New verse after expiration
    - Personalized based on user preferences
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            service = DailyVerseService(request.user)
            daily_verse = service.get_daily_verse()
            serializer = DailyVerseSerializer(daily_verse)
            
            message = "Current daily verse retrieved" if not daily_verse.is_expired() else "New daily verse generated"
            
            return self.success_response({
                'message': message,
                'data': serializer.data
            })
            
        except Exception as e:
            return self.error_response({
                'message': f'Error retrieving daily verse: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshDailyVerseView(BaseResponseMixin, APIView):
    """
    Force refresh daily verse (for testing purposes)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            service = DailyVerseService(request.user)
            daily_verse = service.force_refresh_verse()
            serializer = DailyVerseSerializer(daily_verse)
            
            return self.success_response({
                'message': 'Daily verse refreshed successfully',
                'data': serializer.data
            })
            
        except Exception as e:
            return self.error_response({
                'message': f'Error refreshing daily verse: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


from datetime import timezone as dt_timezone
from .models import JourneyVerse
from .serializers import JourneyVerseSerializer

class JourneyDailyVerseView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            join_date = request.user.date_joined.date()
            today = timezone.now().date()
            days_passed = (today - join_date).days
            
            target_day = (days_passed % 90) + 1 
            
            verse = JourneyVerse.objects.filter(day_number=target_day).first()
            
            if not verse:

                verse = JourneyVerse.objects.filter(day_number=1).first()

            if verse:
                serializer = JourneyVerseSerializer(verse)
                return self.success_response(data=serializer.data)
            else:
                return self.error_response(message="No verses found in database.")

        except Exception as e:
            return self.handle_exception(e)