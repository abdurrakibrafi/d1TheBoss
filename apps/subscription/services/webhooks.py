# apps/subscription/services/webhooks.py
import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils import timezone
from apps.subscription.models import UserSubscription
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        handle_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        handle_payment_failed(event['data']['object'])
    else:
        logger.info(f'Unhandled event type: {event["type"]}')

    return HttpResponse(status=200)

def handle_subscription_updated(subscription):
    try:
        user_subscription = UserSubscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        
        user_subscription.status = subscription['status']
        user_subscription.current_period_start = timezone.datetime.fromtimestamp(
            subscription['current_period_start']
        )
        user_subscription.current_period_end = timezone.datetime.fromtimestamp(
            subscription['current_period_end']
        )
        
        if subscription.get('canceled_at'):
            user_subscription.canceled_at = timezone.datetime.fromtimestamp(
                subscription['canceled_at']
            )
        
        user_subscription.save()
        logger.info(f"Updated subscription {subscription['id']}")
        
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription['id']} not found in database")

def handle_subscription_deleted(subscription):
    try:
        user_subscription = UserSubscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        user_subscription.status = 'canceled'
        user_subscription.canceled_at = timezone.now()
        user_subscription.save()
        logger.info(f"Deleted subscription {subscription['id']}")
        
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription['id']} not found in database")

def handle_payment_succeeded(invoice):
    try:
        subscription_id = invoice['subscription']
        if subscription_id:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            user_sub.mark_payment_success()
            logger.info(f"Payment succeeded for subscription {subscription_id}")
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found for successful payment")
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")

def handle_payment_failed(invoice):
    try:
        subscription_id = invoice['subscription']
        if subscription_id:
            logger.info(f"Payment failed for subscription {subscription_id}")
            # Add any specific logic for failed payments here
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")