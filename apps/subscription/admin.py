from django.contrib import admin
from django.utils import timezone
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'currency', 'interval', 'created_at')
    list_filter = ('plan_type', 'interval', 'currency')
    search_fields = ('name', 'revenuecat_entitlement_id', 'revenuecat_product_id_android', 'revenuecat_product_id_ios')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'price', 'currency', 'interval', 'trial_period_days')
        }),
        ('RevenueCat Configuration', {
            'fields': ('revenuecat_entitlement_id', 'revenuecat_product_id_android', 'revenuecat_product_id_ios'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'subscription_name', 'status', 'current_period_end', 'created_at')
    list_filter = ('status', 'payment_status', 'subscription_plan__plan_type')
    search_fields = ('user__email', 'revenuecat_user_id', 'revenuecat_original_transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'subscription_plan', 'revenuecat_user_id')
        }),
        ('Subscription Status', {
            'fields': ('status', 'payment_status')
        }),
        ('RevenueCat Data', {
            'fields': ('active_entitlements', 'revenuecat_original_transaction_id'),
            'classes': ('collapse',)
        }),
        ('Subscription Period', {
            'fields': ('current_period_start', 'current_period_end', 'trial_start', 'trial_end', 'canceled_at')
        }),
        ('Payment Information', {
            'fields': ('last_payment_date',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email if obj.user else "No User"
    user_email.short_description = 'User Email'
    
    def subscription_name(self, obj):
        return obj.subscription_plan.name if obj.subscription_plan else "No Plan"
    subscription_name.short_description = 'Subscription Plan'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'subscription_plan')
        return queryset
class SubscriptionDashboard(admin.AdminSite):
    site_header = "Subscription Management Dashboard"
    site_title = "Subscription Admin"
    index_title = "Subscription Management"
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)