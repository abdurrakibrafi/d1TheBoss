from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.serializers import ValidationError

class BaseResponseMixin:
    def success_response(self, data=None, message="Success", status_code=status.HTTP_200_OK, **kwargs):
        response_data = {
            "success": True, 
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
        if data is not None:
            response_data["data"] = data
        
        response_data.update(kwargs)
        return Response(response_data, status=status_code)
    
    def error_response(self, message="Error", status_code=status.HTTP_400_BAD_REQUEST, errors=None, **kwargs):
        response_data = {
            "success": False,
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
        
        if errors:
            response_data["errors"] = errors
            
        response_data.update(kwargs)
        return Response(response_data, status=status_code)

    def handle_exception(self, exc):
        """Override to provide consistent error responses"""
        if isinstance(exc, ValidationError):
            return self.error_response(
                message="Validation failed",        
                errors=exc.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)