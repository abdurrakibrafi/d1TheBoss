from django.urls import path
from . import views
from apps.subscription import tests
from apps.subscription.services import webhooks  

# urls.py
urlpatterns = [
    # Setup (call once to create plans)
    path('setup/create-plans/', views.setup_subscription_plans, name='setup-plans'),
    path('setup/check-plans/', views.check_existing_plans, name='check-plans'),
    
    # Regular subscription APIs
    path('status/', views.subscription_status, name='subscription-status'),
    path('plans/', views.list_subscription_plans, name='subscription-plans'),
    path('create/', views.create_subscription, name='create-subscription'),
    path('cancel/', views.cancel_subscription, name='cancel-subscription'),
    path('switch/', views.switch_subscription, name='switch-subscription'),

    # Payment methods
    path('payment/setup-intent/', views.create_setup_intent, name='create-setup-intent'),
    path('payment/add-method/', views.add_payment_method, name='add-payment-method'),
    
    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe-webhook'),

    # Add to urls.py (ONLY for testing)
    path('test/create-payment-method/', tests.create_test_payment_method, name='test-payment-method'),
    path('test/create-multiple-payment-methods/', tests.create_multiple_test_payment_methods, name='test-multiple-payment-methods'),
]