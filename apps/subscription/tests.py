from django.test import TestCase

# Create your tests here.
# Add this to your views.py for TESTING ONLY
# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import stripe
from django.utils import timezone
from django.conf import settings
from apps.subscription.services.stripe_service import StripeService
from apps.subscription.models import UserSubscription, SubscriptionPlan, PaymentMethod
from apps.subscription.serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer, PaymentMethodSerializer

    
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_test_payment_method(request):
#     """Attach existing test payment method"""
#     try:
#         stripe.api_key = settings.STRIPE_SECRET_KEY
        
#         user_subscription = UserSubscription.objects.get(user=request.user)
        
#         # Use pre-made test payment method
#         test_pm_id = 'pm_card_visa'  # Stripe's test payment method
        
#         # Attach to customer
#         stripe.PaymentMethod.attach(
#             test_pm_id,
#             customer=user_subscription.stripe_customer_id
#         )
        
#         return Response({
#             'payment_method_id': test_pm_id,
#             'card_info': 'visa **** 4242'
#         })
        
#     except Exception as e:
#         return Response({'error': str(e)}, status=400)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_test_payment_method(request):
    """Create and attach a real test payment method for backend testing"""
    if not settings.DEBUG:
        return Response({'error': 'Only available in debug mode'}, status=400)
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        # Create a REAL test payment method (this is what frontend would do)
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={
                'number': '4242424242424242',  # Stripe test card
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
            },
        )
        
        # Attach to customer
        payment_method.attach(customer=user_subscription.stripe_customer_id)
        
        # Save to your database (same as your add_payment_method logic)
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        
        PaymentMethod.objects.create(
            user=request.user,
            stripe_payment_method_id=payment_method.id,
            card_last4=payment_method.card.last4,
            card_brand=payment_method.card.brand,
            is_default=True
        )
        
        return Response({
            'success': True,
            'payment_method_id': payment_method.id,  # This will be a REAL ID like pm_1abc123
            'card_info': f"{payment_method.card.brand} **** {payment_method.card.last4}"
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST']) 
@permission_classes([IsAuthenticated])
def create_multiple_test_payment_methods(request):
    """Create multiple test payment methods to choose from"""
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        # Try different test payment methods
        test_methods = ['pm_card_visa', 'pm_card_mastercard', 'pm_card_amex']
        
        for pm_id in test_methods:
            try:
                stripe.PaymentMethod.attach(pm_id, customer=user_subscription.stripe_customer_id)
                return Response({
                    'payment_method_id': pm_id,
                    'card_info': f'Test card {pm_id}'
                })
            except:
                continue
                
        return Response({'error': 'All test methods failed'}, status=400)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)