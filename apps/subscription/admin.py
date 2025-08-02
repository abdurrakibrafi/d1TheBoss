from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, PaymentMethod

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'currency', 'interval', 'trial_period_days', 'is_active')
    list_filter = ('interval', 'currency', 'is_active')
    search_fields = ('name', 'plan_type', 'stripe_price_id')
    readonly_fields = ('id',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'status', 'current_period_start', 'current_period_end', 'trial_end')
    list_filter = ('status', 'subscription_plan')
    search_fields = ('user__email', 'stripe_subscription_id', 'stripe_customer_id')
    autocomplete_fields = ['user', 'subscription_plan']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_brand', 'card_last4', 'is_default', 'created_at')
    list_filter = ('card_brand', 'is_default')
    search_fields = ('user__email', 'card_last4', 'stripe_payment_method_id')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at',)
