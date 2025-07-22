# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.homepage.services.home_page_bible_api import DailyVerseService
from .serializers import DailyVerseSerializer 
from apps.core.utils.mixins import BaseResponseMixin

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