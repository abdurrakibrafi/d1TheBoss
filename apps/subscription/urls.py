from django.urls import path, include
from apps.subscription import revenuecat_views

urlpatterns = [
    path('revenuecat/plans/', revenuecat_views.get_plans, name='rc-get-plans'),
    path('revenuecat/link-user/', revenuecat_views.link_revenuecat_user, name='rc-link-user'),
    path('revenuecat/status/', revenuecat_views.subscription_status, name='rc-status'),
    path('revenuecat/setup/plans/', revenuecat_views.setup_revenuecat_plans, name='rc-setup-plans'),
    path('webhooks/revenuecat/', revenuecat_views.revenuecat_webhook, name='revenuecat-webhook'),
]


