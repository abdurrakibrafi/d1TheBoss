# views.py - Updated with your existing BaseResponseMixin
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
from zoneinfo import ZoneInfo

# Import your existing mixin
from apps.core.utils.mixins import BaseResponseMixin  # Adjust import path as needed

class SubscriptionMixin(BaseResponseMixin):
    """Simple mixin for subscription-specific functionality"""
    
    def get_subscription_plan(self, plan_identifier):
        """Get subscription plan by ID or plan_type"""
        try:
            # Try to get by ID first (if it's a number)
            if str(plan_identifier).isdigit():
                return SubscriptionPlan.objects.get(id=int(plan_identifier), is_active=True)
            else:
                # Try to get by plan_type
                return SubscriptionPlan.objects.get(plan_type=plan_identifier, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return None

# Create mixin instance to use in function-based views
mixin = SubscriptionMixin()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """Get user's current subscription status"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return mixin.success_response(
            data=serializer.data,
            message="Subscription status retrieved successfully"
        )
    except UserSubscription.DoesNotExist:
        return mixin.success_response(
            data={
                'has_subscription': False,
                'show_subscription_page': True
            },
            message="No active subscription found"
        )
    except Exception as e:
        return mixin.handle_exception(e)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_setup_intent(request):
    """Create setup intent for adding payment method"""
    try:
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=request.user
        )
        
        if not user_subscription.stripe_customer_id:
            customer = StripeService.create_customer(request.user)
            user_subscription.stripe_customer_id = customer.id
            user_subscription.save()
        
        setup_intent = StripeService.create_setup_intent(
            user_subscription.stripe_customer_id
        )
        
        return mixin.success_response(
            data={
                'client_secret': setup_intent.client_secret,
                'setup_intent_id': setup_intent.id
            },
            message="Setup intent created successfully"
        )
    except Exception as e:
        return mixin.handle_exception(e)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_method(request):
    """Save payment method after setup intent confirmation"""
    payment_method_id = request.data.get('payment_method_id')
    
    if not payment_method_id:
        return mixin.bad_request_response(
            message="Payment method ID is required",
            errors={'payment_method_id': ['This field is required']}
        )
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        # Get payment method details from Stripe
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        
        # Check if payment method already exists
        existing_pm = PaymentMethod.objects.filter(
            user=request.user,
            stripe_payment_method_id=payment_method_id
        ).first()
        
        if existing_pm:
            return mixin.success_response(
                data={
                    'payment_method_id': payment_method_id,
                    'card_info': f"{payment_method.card.brand} **** {payment_method.card.last4}"
                },
                message="Payment method already exists"
            )
        
        # Set all other payment methods to not default
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        
        # Save to database
        pm = PaymentMethod.objects.create(
            user=request.user,
            stripe_payment_method_id=payment_method_id,
            card_last4=payment_method.card.last4,
            card_brand=payment_method.card.brand,
            is_default=True
        )
        
        return mixin.success_response(
            data={
                'payment_method_id': payment_method_id,
                'card_info': f"{payment_method.card.brand} **** {payment_method.card.last4}"
            },
            message="Payment method added successfully"
        )
        
    except UserSubscription.DoesNotExist:
        return mixin.bad_request_response(
            message="Please create setup intent first"
        )
    except stripe.error.InvalidRequestError as e:
        return mixin.bad_request_response(
            message=f"Invalid payment method: {str(e)}"
        )
    except Exception as e:
        return mixin.handle_exception(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    """Create a new subscription - accepts plan_id OR plan_type"""
    # Support both plan_id and plan_type for flexibility
    plan_identifier = request.data.get('plan_id') or request.data.get('plan_type')
    payment_method_id = request.data.get('payment_method_id')
    
    if not plan_identifier:
        return mixin.bad_request_response(
            message="Plan identifier is required",
            errors={'plan': ['Either plan_id or plan_type is required']}
        )
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Get the subscription plan using our helper method
        plan = mixin.get_subscription_plan(plan_identifier)
        if not plan:
            return mixin.not_found_response(
                message=f"Subscription plan '{plan_identifier}' not found or inactive"
            )
        
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        if user_subscription.stripe_subscription_id:
            return mixin.bad_request_response(
                message="User already has an active subscription"
            )
        
        # Re-attach the payment method if it fails
        if payment_method_id:
            try:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=user_subscription.stripe_customer_id
                )
            except:
                pass  # Already attached or other issue
                
        # Create subscription
        subscription = StripeService.create_subscription(
            user_subscription.stripe_customer_id,
            plan.stripe_price_id,
            payment_method_id
        )

        # Debug: Print subscription object (remove in production)
        print(f"DEBUG: Subscription object: {subscription}")
        print(f"DEBUG: Subscription status: {subscription.status}")
        
        # Update user subscription
        user_subscription.stripe_subscription_id = subscription.id
        user_subscription.subscription_plan = plan
        user_subscription.status = subscription.status
        
        # Handle period dates - for trialing subscriptions, use billing_cycle_anchor
         # Handle period dates - for trialing subscriptions, use billing_cycle_anchor
        if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
            user_subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription.current_period_start, tz=ZoneInfo("UTC")
            )
        elif hasattr(subscription, 'billing_cycle_anchor') and subscription.billing_cycle_anchor:
            # For trialing subscriptions, the billing cycle anchor is when billing will start
            user_subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription.start_date, tz=ZoneInfo("UTC")
            )
            
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription.current_period_end, tz=ZoneInfo("UTC")
            )
        elif hasattr(subscription, 'billing_cycle_anchor') and subscription.billing_cycle_anchor:
            # For trialing subscriptions, use billing_cycle_anchor as the end of trial/start of billing
            user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription.billing_cycle_anchor, tz=ZoneInfo("UTC")
            )
            
        # Handle trial dates
        if hasattr(subscription, 'trial_start') and subscription.trial_start:
            user_subscription.trial_start = timezone.datetime.fromtimestamp(
                subscription.trial_start, tz=ZoneInfo("UTC")
            )
        if hasattr(subscription, 'trial_end') and subscription.trial_end:
            user_subscription.trial_end = timezone.datetime.fromtimestamp(
                subscription.trial_end, tz=ZoneInfo("UTC")
            )
            
            
        user_subscription.save()
        
        return mixin.created_response(
            data={
                'subscription_id': subscription.id,
                'status': subscription.status,
                'plan_name': plan.name,
                'plan_price': str(plan.price),
                'trial_end': user_subscription.trial_end.isoformat() if user_subscription.trial_end else None,
                'current_period_end': user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None
            },
            message="Subscription created successfully"
        )
        
    except UserSubscription.DoesNotExist:
        return mixin.bad_request_response(
            message="Please create setup intent first"
        )
    except KeyError as e:
        # Log the specific missing key for debugging
        print(f"API Exception: KeyError: {str(e)}")
        return mixin.handle_exception(Exception(f"Missing subscription field: {str(e)}"))
    except Exception as e:
        print(f"API Exception: {type(e).__name__}: {str(e)}")
        return mixin.handle_exception(e)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancel subscription at period end"""
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        if not user_subscription.stripe_subscription_id:
            return mixin.not_found_response(
                message="No active subscription found"
            )
        
        subscription = StripeService.cancel_subscription(
            user_subscription.stripe_subscription_id
        )
        
        user_subscription.canceled_at = timezone.now()
        user_subscription.save()
        
        return mixin.success_response(
            message="Subscription canceled successfully"
        )
    except UserSubscription.DoesNotExist:
        return mixin.not_found_response(
            message="No subscription found"
        )
    except Exception as e:
        return mixin.handle_exception(e)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_subscription_plans(request):
    """List available subscription plans"""
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return mixin.success_response(
            data=serializer.data,
            message="Subscription plans retrieved successfully"
        )
    except Exception as e:
        return mixin.handle_exception(e)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_subscription_plans(request):
    """One-time API to create subscription plans in Stripe and database"""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    plans_data = [
        {
            'name': 'Explorer Pro Monthly',
            'plan_type': 'explorer_monthly',
            'price': 9.99,
            'interval': 'month',
            'description': 'Monthly subscription with 7-day free trial'
        },
        {
            'name': 'Explorer Pro Yearly', 
            'plan_type': 'explorer_yearly',
            'price': 99.99,
            'interval': 'year',
            'description': 'Yearly subscription with 7-day free trial (Save 25%)'
        }
    ]
    
    created_plans = []
    errors = []
    
    try:
        for plan_data in plans_data:
            try:
                # Check if plan already exists
                existing_plan = SubscriptionPlan.objects.filter(
                    plan_type=plan_data['plan_type']
                ).first()
                
                if existing_plan:
                    created_plans.append({
                        'id': existing_plan.id,  # Include ID in response
                        'name': plan_data['name'],
                        'status': 'already_exists',
                        'stripe_price_id': existing_plan.stripe_price_id,
                        'price': str(existing_plan.price)
                    })
                    continue
                
                # Create product in Stripe
                product = stripe.Product.create(
                    name=plan_data['name'],
                    description=plan_data['description']
                )
                
                # Create price in Stripe
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan_data['price'] * 100),  # Convert to cents
                    currency='usd',
                    recurring={'interval': plan_data['interval']},
                )
                
                # Create in database
                plan = SubscriptionPlan.objects.create(
                    name=plan_data['name'],
                    plan_type=plan_data['plan_type'],
                    stripe_price_id=price.id,
                    price=plan_data['price'],
                    currency='usd',
                    interval=plan_data['interval'],
                    trial_period_days=7,
                    is_active=True,
                )
                
                created_plans.append({
                    'id': plan.id,  # Include ID in response
                    'name': plan.name,
                    'status': 'created',
                    'stripe_price_id': plan.stripe_price_id,
                    'price': str(plan.price),
                    'interval': plan.interval
                })
                
            except Exception as plan_error:
                errors.append({
                    'plan': plan_data['name'],
                    'error': str(plan_error)
                })
        
        return mixin.success_response(
            data={
                'plans': created_plans,
                'errors': errors if errors else None,
                'total_plans': len(created_plans)
            },
            message="Subscription plans setup completed"
        )
        
    except Exception as e:
        return mixin.handle_exception(e)

@api_view(['GET'])
def check_existing_plans(request):
    """Check what subscription plans already exist"""
    try:
        db_plans = SubscriptionPlan.objects.all()
        
        plans_info = []
        for plan in db_plans:
            plans_info.append({
                'id': plan.id,
                'name': plan.name,
                'plan_type': plan.plan_type,
                'price': str(plan.price),
                'interval': plan.interval,
                'stripe_price_id': plan.stripe_price_id,
                'is_active': plan.is_active,
                'created_at': plan.created_at if hasattr(plan, 'created_at') else None
            })
        
        return mixin.success_response(
            data={
                'total_plans': len(plans_info),
                'plans': plans_info,
                'has_plans': len(plans_info) > 0
            },
            message="Plans retrieved successfully"
        )
    except Exception as e:
        return mixin.handle_exception(e)
    

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_subscription(request):
    """Switch user's subscription to a different plan - accepts plan_id OR plan_type"""
    plan_identifier = request.data.get('plan_id') or request.data.get('plan_type')
    
    if not plan_identifier:
        return mixin.bad_request_response(
            message="Plan identifier is required",
            errors={'plan': ['Either plan_id or plan_type is required']}
        )
    
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)
        
        if not user_subscription.stripe_subscription_id:
            return mixin.not_found_response(
                message="No active subscription found"
            )
        
        # Get the new plan
        new_plan = mixin.get_subscription_plan(plan_identifier)
        if not new_plan:
            return mixin.not_found_response(
                message=f"Subscription plan '{plan_identifier}' not found or inactive"
            )
        
        # Don't allow switching to the same plan
        if user_subscription.subscription_plan == new_plan:
            return mixin.bad_request_response(
                message="Already subscribed to this plan"
            )
        
        # Update the subscription in Stripe
        updated_subscription = StripeService.update_subscription(
            user_subscription.stripe_subscription_id,
            new_plan.stripe_price_id
        )
        
        # Update our database with the new plan
        user_subscription.subscription_plan = new_plan
        user_subscription.status = updated_subscription.status
        
        # Handle period dates with proper checks (same as create function)
        if hasattr(updated_subscription, 'current_period_start') and updated_subscription.current_period_start:
            user_subscription.current_period_start = timezone.datetime.fromtimestamp(
                updated_subscription.current_period_start, tz=ZoneInfo("UTC")
            )
        elif hasattr(updated_subscription, 'billing_cycle_anchor') and updated_subscription.billing_cycle_anchor:
            # For trialing subscriptions, the billing cycle anchor is when billing will start
            user_subscription.current_period_start = timezone.datetime.fromtimestamp(
                updated_subscription.start_date, tz=ZoneInfo("UTC")
            )
            
        if hasattr(updated_subscription, 'current_period_end') and updated_subscription.current_period_end:
            user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                updated_subscription.current_period_end, tz=ZoneInfo("UTC")
            )
        elif hasattr(updated_subscription, 'billing_cycle_anchor') and updated_subscription.billing_cycle_anchor:
            # For trialing subscriptions, use billing_cycle_anchor as the end of trial/start of billing
            user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                updated_subscription.billing_cycle_anchor, tz=ZoneInfo("UTC")
            )
            
        # Handle trial dates (important for switches during trial period)
        if hasattr(updated_subscription, 'trial_start') and updated_subscription.trial_start:
            user_subscription.trial_start = timezone.datetime.fromtimestamp(
                updated_subscription.trial_start, tz=ZoneInfo("UTC")
            )
        if hasattr(updated_subscription, 'trial_end') and updated_subscription.trial_end:
            user_subscription.trial_end = timezone.datetime.fromtimestamp(
                updated_subscription.trial_end, tz=ZoneInfo("UTC")
            )
        
        user_subscription.save()
                
        return mixin.success_response(
            data={
                'new_plan': new_plan.name,
                'new_price': str(new_plan.price),
                'status': updated_subscription.status,
                'trial_end': user_subscription.trial_end.isoformat() if user_subscription.trial_end else None,
                'next_billing_date': user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None
            },
            message=f"Subscription switched to {new_plan.name}"
        )
        
    except UserSubscription.DoesNotExist:
        return mixin.not_found_response(
            message="No subscription found"
        )
    except KeyError as e:
        # Log the specific missing key for debugging
        print(f"Switch API Exception: KeyError: {str(e)}")
        return mixin.handle_exception(Exception(f"Missing subscription field: {str(e)}"))
    except Exception as e:
        print(f"Switch API Exception: {type(e).__name__}: {str(e)}")
        return mixin.handle_exception(e)