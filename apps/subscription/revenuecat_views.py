import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from apps.subscription.models import UserSubscription, SubscriptionPlan
from apps.core.utils.mixins import BaseResponseMixin

mixin = BaseResponseMixin()


@api_view(['GET'])
def get_plans(request):
    """Get available subscription plans with all payment provider info"""
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True)

        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'plan_type': plan.plan_type,
                'price': str(plan.price) if plan.price else None,
                'currency': plan.currency,
                'interval': plan.interval,
                'trial_period_days': plan.trial_period_days,
                'revenuecat_entitlement_id': plan.revenuecat_entitlement_id,
                'revenuecat_product_id_android': plan.revenuecat_product_id_android,
                'revenuecat_product_id_ios': plan.revenuecat_product_id_ios,
            })

        return mixin.success_response(
            data={
                'plans': plans_data,
                'total_plans': len(plans_data)
            },
            message="Plans retrieved successfully"
        )

    except Exception as e:
        return mixin.handle_exception(e)


@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def link_revenuecat_user(request):
    """
    Link Django user to RevenueCat and sync subscription data
    Frontend sends complete RevenueCat customer info
    Supports both POST (create/link) and PUT (update) operations
    """
    try:
        revenuecat_user_id = request.data.get('revenuecat_user_id')
        has_active_subscription = request.data.get('has_active_subscription', False)
        subscription_status = request.data.get('status', 'free')
        active_entitlements = request.data.get('active_entitlements', [])
        entitlement_id = request.data.get('entitlement_id')
        product_id = request.data.get('product_id')
        expiration_date = request.data.get('expiration_date')
        will_renew = request.data.get('will_renew', False)
        period_type = request.data.get('period_type')
        active_subscriptions = request.data.get('active_subscriptions', [])
        first_seen = request.data.get('first_seen')
        original_app_version = request.data.get('original_app_version')
        original_transaction_id = request.data.get('original_transaction_id')
        if not revenuecat_user_id:
            return mixin.bad_request_response(message="revenuecat_user_id is required")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={
                'revenuecat_user_id': revenuecat_user_id,
                'status': subscription_status,
                'active_entitlements': active_entitlements,
                'revenuecat_original_transaction_id': original_transaction_id,
            }
        )
        if not created:
            user_subscription.revenuecat_user_id = revenuecat_user_id
        if original_transaction_id:
            user_subscription.revenuecat_original_transaction_id = original_transaction_id
        user_subscription.active_entitlements = active_entitlements
        if has_active_subscription:
            if period_type == 'trial':
                user_subscription.status = 'trialing'
            else:
                user_subscription.status = 'active'
        else:
            user_subscription.status = 'free'
        if expiration_date:
            try:
                from dateutil import parser
                user_subscription.current_period_end = parser.parse(expiration_date)
                user_subscription.current_period_start = timezone.now()
            except Exception as e:
                print(f"Error parsing expiration date: {e}")
        if product_id and has_active_subscription:
            subscription_plan = SubscriptionPlan.objects.filter(
                Q(revenuecat_product_id_android=product_id) |
                Q(revenuecat_product_id_ios=product_id)
            ).first()

            if subscription_plan:
                user_subscription.subscription_plan = subscription_plan
            else:
                if entitlement_id:
                    subscription_plan = SubscriptionPlan.objects.filter(
                        revenuecat_entitlement_id=entitlement_id
                    ).first()
                    if subscription_plan:
                        user_subscription.subscription_plan = subscription_plan
        if period_type == 'trial' and expiration_date:
            try:
                from dateutil import parser
                user_subscription.trial_start = timezone.now()
                user_subscription.trial_end = parser.parse(expiration_date)
            except Exception as e:
                print(f"Error parsing trial dates: {e}")
        if has_active_subscription:
            user_subscription.payment_status = 'paid'
            user_subscription.last_payment_date = timezone.now()
        else:
            user_subscription.payment_status = 'pending'
        user_subscription.save()
        response_data = {
            'user_id': request.user.id,
            'user_email': request.user.email,
            'username': request.user.username if hasattr(request.user, 'username') else None,
            'revenuecat_user_id': user_subscription.revenuecat_user_id,
            'original_transaction_id': user_subscription.revenuecat_original_transaction_id,
            'status': user_subscription.status,
            'linked': True,
            'created_new': created,
            'has_active_subscription': has_active_subscription,

            'subscription_details': {
                'plan_name': user_subscription.subscription_plan.name if user_subscription.subscription_plan else None,
                'plan_type': user_subscription.subscription_plan.plan_type if user_subscription.subscription_plan else None,
                'price': str(
                    user_subscription.subscription_plan.price) if user_subscription.subscription_plan else None,
                'interval': user_subscription.subscription_plan.interval if user_subscription.subscription_plan else None,
            },

            'entitlements': {
                'active_entitlements': user_subscription.active_entitlements,
                'entitlement_id': entitlement_id,
            },

            'dates': {
                'expires_at': user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None,
                'trial_start': user_subscription.trial_start.isoformat() if user_subscription.trial_start else None,
                'trial_end': user_subscription.trial_end.isoformat() if user_subscription.trial_end else None,
                'first_seen': first_seen,
            },

            'subscription_status': {
                'is_trial': user_subscription.status == 'trialing',
                'will_renew': will_renew,
                'period_type': period_type,
                'payment_status': user_subscription.payment_status,
            },
            'metadata': {
                'original_app_version': original_app_version,
                'active_subscriptions': active_subscriptions,
            }
        }

        message = "User linked and subscription synced successfully"
        if created:
            message = "New subscription created and linked successfully"

        return mixin.success_response(
            data=response_data,
            message=message
        )

    except Exception as e:
        return mixin.handle_exception(e)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    Get user's subscription status
    NO AUTO-SYNC - Just returns stored data
    """
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)

        return mixin.success_response(
            data={
                'has_subscription':  user_subscription.status in ['active', 'trialing'],
                'status': user_subscription.status,
                'plan_name': user_subscription.subscription_plan.name if user_subscription.subscription_plan else None,
                'plan_type': user_subscription.subscription_plan.plan_type if user_subscription.subscription_plan else None,
                'expires_at': user_subscription.current_period_end.isoformat() if user_subscription.current_period_end else None,
                'active_entitlements': user_subscription.active_entitlements,
                'revenuecat_user_id': user_subscription.revenuecat_user_id,
                'original_transaction_id': user_subscription.revenuecat_original_transaction_id,
                'is_trial': user_subscription.status == 'trialing',
                'trial_end': user_subscription.trial_end.isoformat() if user_subscription.trial_end else None,
                'payment_status': user_subscription.payment_status,
            },
            message="Subscription status retrieved successfully"
        )

    except UserSubscription.DoesNotExist:
        return mixin.success_response(
            data={
                'has_subscription': False,
                'status': 'free',
                'can_make_request': False,
                'revenuecat_user_id': None,
                'monthly_prompts_used': 0,
                'monthly_prompts_limit': 0,
            },
            message="No subscription found"
        )
    except Exception as e:
        return mixin.handle_exception(e)


@api_view(['POST'])
@staff_member_required
def setup_revenuecat_plans(request):
    """Create/Update RevenueCat subscription plans - Admin only"""
    try:
        plans_created = []
        monthly_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type="pro_monthly",
            defaults={
                "name": "Unlock Monthly Plan",
                "revenuecat_entitlement_id": "premium",
                "revenuecat_product_id_android": "monthly_plan",
                "revenuecat_product_id_ios": "monthly_plan",
                "price": 11.99,
                "currency": "USD",
                "interval": "month",
                "trial_period_days": 7,
                "is_active": True
            }
        )
        plans_created.append({"plan": "pro_monthly", "created": created})
        yearly_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type="pro_yearly",
            defaults={
                "name": "Unlock Yearly Plan",
                "revenuecat_entitlement_id": "premium",
                "revenuecat_product_id_android": "yearly_plan",
                "revenuecat_product_id_ios": "yearly_plan",
                "price": 79.99,
                "currency": "USD",
                "interval": "year",
                "trial_period_days": 7,
                "is_active": True
            }
        )
        plans_created.append({"plan": "pro_yearly", "created": created})

        return Response(
            {
                "message": "Preachly plans setup completed!",
                "plans": plans_created,
                "total_plans": SubscriptionPlan.objects.count()
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
@csrf_exempt
def revenuecat_webhook(request):
    """Handle RevenueCat webhook events"""
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
        event_type = data.get('type')
        event_data = data.get('event', {})

        print(f"RevenueCat Webhook: {event_type}")
        print(f"Event Data: {event_data}")

        if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'NON_RENEWING_PURCHASE']:
            _handle_subscription_activated(event_data)
        elif event_type in ['CANCELLATION', 'EXPIRATION']:
            _handle_subscription_cancelled(event_data)
        elif event_type == 'UNCANCELLATION':
            _handle_subscription_reactivated(event_data)

        return HttpResponse("OK", status=200)

    except Exception as e:
        print(f"RevenueCat webhook error: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=400)


def _handle_subscription_activated(event_data):
    """Handle subscription activation from webhook"""
    try:
        app_user_id = event_data.get('app_user_id')
        product_id = event_data.get('product_id')
        entitlement_ids = event_data.get('entitlement_ids', [])
        period_type = event_data.get('period_type', 'normal')
        expiration_at_ms = event_data.get('expiration_at_ms')

        if not app_user_id:
            return

        user_subscription = UserSubscription.objects.filter(
            revenuecat_user_id=app_user_id
        ).first()

        if user_subscription:
            if period_type == 'trial':
                user_subscription.status = 'trialing'
            else:
                user_subscription.status = 'active'
            user_subscription.active_entitlements = entitlement_ids
            if expiration_at_ms:
                user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                    expiration_at_ms / 1000, tz=timezone.utc
                )
            if product_id:
                plan = SubscriptionPlan.objects.filter(
                    Q(revenuecat_product_id_android=product_id) |
                    Q(revenuecat_product_id_ios=product_id)
                ).first()
                if plan:
                    user_subscription.subscription_plan = plan

            user_subscription.payment_status = 'paid'
            user_subscription.save()

            print(f"✅ Subscription activated for user: {user_subscription.user.email}")

    except Exception as e:
        print(f"Error handling subscription activation: {str(e)}")


def _handle_subscription_cancelled(event_data):
    """Handle subscription cancellation from webhook"""
    try:
        app_user_id = event_data.get('app_user_id')
        if not app_user_id:
            return

        user_subscription = UserSubscription.objects.filter(
            revenuecat_user_id=app_user_id
        ).first()

        if user_subscription:
            user_subscription.status = 'canceled'
            user_subscription.canceled_at = timezone.now()
            user_subscription.active_entitlements = []
            user_subscription.save()

            print(f"❌ Subscription cancelled for user: {user_subscription.user.email}")

    except Exception as e:
        print(f"Error handling subscription cancellation: {str(e)}")


def _handle_subscription_reactivated(event_data):
    """Handle subscription reactivation from webhook"""
    try:
        app_user_id = event_data.get('app_user_id')
        entitlement_ids = event_data.get('entitlement_ids', [])
        expiration_at_ms = event_data.get('expiration_at_ms')

        if not app_user_id:
            return

        user_subscription = UserSubscription.objects.filter(
            revenuecat_user_id=app_user_id
        ).first()

        if user_subscription:
            user_subscription.status = 'active'
            user_subscription.canceled_at = None
            user_subscription.active_entitlements = entitlement_ids

            if expiration_at_ms:
                user_subscription.current_period_end = timezone.datetime.fromtimestamp(
                    expiration_at_ms / 1000, tz=timezone.utc
                )

            user_subscription.save()

            print(f"✅ Subscription reactivated for user: {user_subscription.user.email}")

    except Exception as e:
        print(f"Error handling subscription reactivation: {str(e)}")