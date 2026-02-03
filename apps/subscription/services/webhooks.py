# apps/subscription/services/webhooks.py - Updated with proper cancellation handling
import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils import timezone
from zoneinfo import ZoneInfo  # Python 3.9+ timezone handling
from apps.subscription.models import UserSubscription
import logging
from apps.notification.services.notification_service import NotificationService

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
        
        # Store previous status to detect changes
        previous_status = user_subscription.status
        
        # Update status from Stripe
        user_subscription.status = subscription['status']
        
        # Handle period dates with proper checks
        if subscription.get('current_period_start'):
            user_subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription['current_period_start'], tz=ZoneInfo("UTC")
            )
        
        if subscription.get('current_period_end'):
            user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription['current_period_end'], tz=ZoneInfo("UTC")
            )
        
        # Handle trial dates
        if subscription.get('trial_start'):
            user_subscription.trial_start = timezone.datetime.fromtimestamp(
                subscription['trial_start'], tz=ZoneInfo("UTC")
            )
        
        if subscription.get('trial_end'):
            user_subscription.trial_end = timezone.datetime.fromtimestamp(
                subscription['trial_end'], tz=ZoneInfo("UTC")
            )
        
        # Handle cancellation timestamp
        if subscription.get('canceled_at'):
            user_subscription.canceled_at = timezone.datetime.fromtimestamp(
                subscription['canceled_at'], tz=ZoneInfo("UTC")
            )
        
        user_subscription.save()

        # 🔔 SUBSCRIPTION WAS CANCELED (but still active until period end)
        if (subscription['status'] == 'canceled' and 
            previous_status != 'canceled' and
            user_subscription.current_period_end):
            
            NotificationService.send_notification(
                user_id=user_subscription.user.id,
                title="Subscription Cancelled 🚫",
                message=f"Your subscription will remain active until {user_subscription.current_period_end.strftime('%B %d, %Y')}",
                notification_types=['push', 'in_app', 'email'],
                data={
                    'type': 'subscription_cancelled',
                    'access_until': user_subscription.current_period_end.isoformat(),
                    'canceled_at': user_subscription.canceled_at.isoformat() if user_subscription.canceled_at else None
                }
            )

        # 🔔 CHECK IF TRIAL IS ENDING SOON (2 days before)
        elif (user_subscription.status == 'trialing' and 
            user_subscription.trial_end and 
            user_subscription.days_until_trial_end() <= 2):
            
            NotificationService.send_notification(
                user_id=user_subscription.user.id,
                title="Trial Ending Soon! ⏰",
                message=f"Your free trial ends in {user_subscription.days_until_trial_end()} days. Add a payment method to continue.",
                notification_types=['push', 'in_app', 'email'],
                data={
                    'type': 'trial_ending',
                    'days_left': user_subscription.days_until_trial_end()
                }
            )
        
        # 🔔 TRIAL ENDED - NOW ACTIVE
        elif (subscription['status'] == 'active' and 
              previous_status == 'trialing'):
            
            NotificationService.send_notification(
                user_id=user_subscription.user.id,
                title="Payment Successful! ✅",
                message="Your subscription is now active. Welcome to Explorer Pro!",
                notification_types=['push', 'in_app'],
                data={
                    'type': 'subscription_activated',
                    'plan_name': user_subscription.subscription_plan.name if user_subscription.subscription_plan else 'Pro Plan'
                }
            )

        # 🔔 SUBSCRIPTION BECAME PAST DUE
        elif (subscription['status'] == 'past_due' and 
              previous_status != 'past_due'):
            
            NotificationService.send_notification(
                user_id=user_subscription.user.id,
                title="Payment Issue ⚠️",
                message="Your payment failed. Please update your payment method to continue your subscription.",
                notification_types=['push', 'in_app', 'email'],
                data={
                    'type': 'subscription_past_due',
                    'action_required': 'update_payment_method'
                }
            )
        
        logger.info(f"Updated subscription {subscription['id']} - Status: {previous_status} → {subscription['status']}")
        
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription['id']} not found in database")
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")

def handle_subscription_deleted(subscription):
    """
    This webhook is called when subscription is ACTUALLY deleted/ended
    This is when access should truly end
    """
    try:
        user_subscription = UserSubscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        
        # Update status to canceled
        user_subscription.status = 'canceled'
        
        # Set canceled_at if not already set
        if not user_subscription.canceled_at:
            user_subscription.canceled_at = timezone.now()
        
        user_subscription.save()
        
        # 🔔 SUBSCRIPTION ACCESS HAS ACTUALLY ENDED
        NotificationService.send_notification(
            user_id=user_subscription.user.id,
            title="Subscription Ended 📋",
            message="Your subscription access has ended. You can resubscribe anytime to continue using Explorer Pro!",
            notification_types=['push', 'in_app', 'email'],
            data={
                'type': 'subscription_ended',
                'ended_at': timezone.now().isoformat(),
                'resubscribe_available': True
            }
        )
        
        logger.info(f"Subscription {subscription['id']} completely deleted - access ended")
        
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription['id']} not found in database")
    except Exception as e:
        logger.error(f"Error handling subscription deletion: {str(e)}")

def handle_payment_succeeded(invoice):
    try:
        subscription_id = invoice.get('subscription')
        if subscription_id:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            user_sub.mark_payment_success()

            # Don't send notification for first payment (trial end) as it's handled in subscription_updated
            # Only send for renewal payments
            if user_sub.last_payment_date:  # This means it's not the first payment
                NotificationService.send_notification(
                    user_id=user_sub.user.id,
                    title="Payment Successful! 💳",
                    message=f"Your {user_sub.subscription_plan.name if user_sub.subscription_plan else 'subscription'} has been renewed.",
                    notification_types=['push', 'in_app'],
                    data={
                        'type': 'payment_success',
                        'amount': str(user_sub.subscription_plan.price) if user_sub.subscription_plan else 'N/A',
                        'next_billing': user_sub.current_period_end.isoformat() if user_sub.current_period_end else None
                    }
                )
            
            logger.info(f"Payment succeeded for subscription {subscription_id}")
        else:
            logger.info("Invoice payment succeeded but no subscription ID found")
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found for successful payment")
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")

def handle_payment_failed(invoice):
    try:
        subscription_id = invoice.get('subscription')
        if subscription_id:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
            
            NotificationService.send_notification(
                user_id=user_sub.user.id,
                title="Payment Failed ❌",
                message="Your payment couldn't be processed. Please update your payment method to avoid service interruption.",
                notification_types=['push', 'in_app', 'email'],
                data={
                    'type': 'payment_failed',
                    'action_required': 'update_payment_method',
                    'retry_date': user_sub.current_period_end.isoformat() if user_sub.current_period_end else None
                }
            )
            logger.info(f"Payment failed for subscription {subscription_id}")
        else:
            logger.info("Invoice payment failed but no subscription ID found")
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found for failed payment")
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")