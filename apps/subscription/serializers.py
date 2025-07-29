# serializers.py
from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, PaymentMethod

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name', 
            'plan_type',
            'price',
            'currency',
            'interval',
            'trial_period_days',
            'is_active'
        ]

class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    is_trial_active = serializers.SerializerMethodField()
    days_until_trial_end = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'subscription_plan',
            'status',
            'current_period_start',
            'current_period_end',
            'trial_start',
            'trial_end',
            'canceled_at',
            'is_active',
            'is_trial_active',
            'days_until_trial_end',
            'created_at',
            'updated_at'
        ]
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_is_trial_active(self, obj):
        return obj.is_trial_active()
    
    def get_days_until_trial_end(self, obj):
        return obj.days_until_trial_end()

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'card_last4',
            'card_brand', 
            'is_default',
            'created_at'
        ]
        
class SubscriptionStatusSerializer(serializers.Serializer):
    """For users without subscription"""
    has_subscription = serializers.BooleanField(default=False)
    show_subscription_page = serializers.BooleanField(default=True)
    user_id = serializers.IntegerField()
    message = serializers.CharField(default="No active subscription found")