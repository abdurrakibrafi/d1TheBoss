from django.db import models
from apps.accounts.models import User
from django.utils import timezone


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)

    # RevenueCat fields
    revenuecat_entitlement_id = models.CharField(max_length=100, blank=True, null=True) 
    revenuecat_product_id_android = models.CharField(max_length=100, blank=True, null=True)
    revenuecat_product_id_ios = models.CharField(max_length=100, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    interval = models.CharField(max_length=10, blank=True, null=True)
    trial_period_days = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.interval}"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('pending', 'Pending'),
        ('free', 'Free'), 
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, blank=True, null=True)

    revenuecat_user_id = models.CharField(max_length=255, null=True, blank=True)
    active_entitlements = models.JSONField(default=list, blank=True)
    revenuecat_original_transaction_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='free')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    payment_status = models.CharField(max_length=20, default='pending')
    last_payment_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.name} ({self.status})"

 