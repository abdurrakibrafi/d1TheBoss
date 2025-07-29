# models.py
from django.db import models
from apps.accounts.models import User
from django.utils import timezone
import stripe

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('explorer_monthly', 'Explorer Pro Monthly'),
        ('explorer_yearly', 'Explorer Pro Yearly'),
    ]
    
    name = models.CharField(max_length=100, blank=True, null=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    interval = models.CharField(max_length=10, blank=True, null=True) # 'month' or 'year'
    trial_period_days = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)
    apple_product_id = models.CharField(max_length=100, blank=True, null=True)  # Add this


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
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    payment_status = models.CharField(max_length=20, default='pending')
    last_payment_date = models.DateTimeField(null=True, blank=True)

    

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_active(self):
        return self.status in ['trialing', 'active']
    
    def is_trial_active(self):
        if self.trial_end and self.status == 'trialing':
            return timezone.now() < self.trial_end
        return False
    
    def days_until_trial_end(self):
        if self.trial_end and self.is_trial_active():
            return (self.trial_end - timezone.now()).days
        return 0
    
    def mark_payment_success(self):
        self.payment_status = 'paid'
        self.last_payment_date = timezone.now()
        self.save()

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, )
    stripe_payment_method_id = models.CharField(max_length=100, blank=True, )
    card_last4 = models.CharField(max_length=4, blank=True, )
    card_brand = models.CharField(max_length=20, blank=True, )
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.card_brand} **** {self.card_last4}"