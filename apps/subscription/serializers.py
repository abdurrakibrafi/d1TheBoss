from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    
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
            'revenuecat_entitlement_id',
            'revenuecat_product_id_android',
            'revenuecat_product_id_ios',
            'is_active'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Full subscription details serializer"""
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
            'active_entitlements',
            'revenuecat_user_id',
            'revenuecat_original_transaction_id',
            'payment_status',
            'last_payment_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_active(self, obj):
        """Check if subscription is currently active"""
        return obj.is_active()
    
    def get_is_trial_active(self, obj):
        """Check if trial is currently active"""
        return obj.is_trial_active()
    
    def get_days_until_trial_end(self, obj):
        """Get remaining days in trial"""
        return obj.days_until_trial_end()


class SubscriptionStatusSerializer(serializers.Serializer):
    """Lightweight serializer for quick status checks"""
    has_subscription = serializers.BooleanField()
    status = serializers.CharField()
    plan_name = serializers.CharField(allow_null=True)
    plan_type = serializers.CharField(allow_null=True)
    is_trial = serializers.BooleanField()
    expires_at = serializers.DateTimeField(allow_null=True)
    active_entitlements = serializers.ListField(child=serializers.CharField())
    

class SimplePlanSerializer(serializers.ModelSerializer):
    """Minimal plan info for public listing"""
    
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
        ]