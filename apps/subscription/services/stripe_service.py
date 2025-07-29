# services/stripe_service.py
import stripe
from django.conf import settings
from apps.subscription.models import UserSubscription, SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    
    @staticmethod
    def create_customer(user):
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={'user_id': user.id}
            )
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create customer: {str(e)}")
    
    @staticmethod
    def create_setup_intent(customer_id):
        """Create setup intent for saving payment method"""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                usage='off_session'
            )
            return setup_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create setup intent: {str(e)}")
    
    @staticmethod
    def create_subscription(customer_id, price_id, payment_method_id=None):
        """Create subscription with trial"""
        try:
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'trial_period_days': 7,
                'expand': ['latest_invoice.payment_intent'],
            }
            
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            subscription = stripe.Subscription.create(**subscription_data)
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription_id, at_period_end=True):
        """Cancel subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=at_period_end
            )
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    @staticmethod
    def get_payment_methods(customer_id):
        """Get customer's payment methods"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            return payment_methods
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to get payment methods: {str(e)}")
        
    @staticmethod
    def update_subscription(subscription_id, new_price_id, proration_date=None):
        """Update subscription to a new price/plan"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Create subscription update parameters
            params = {
                'items': [{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                'proration_behavior': 'always_invoice',
            }
            
            if proration_date:
                params['proration_date'] = proration_date
            
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                **params
            )
            
            return updated_subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to update subscription: {str(e)}")