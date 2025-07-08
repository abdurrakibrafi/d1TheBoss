from django.urls import path, include
from .views import FakeDataAPIView, APIGuideView, PrivacyPolicyView, TermsAndConditionsView, PrivacyPolicyView


urlpatterns = [

    path("legal/terms/", TermsAndConditionsView.as_view(), name="terms-conditions"),
    path("legal/privacy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
    
    path("guide/", APIGuideView.as_view(), name="api-guide;"),

    path('fake-data/', FakeDataAPIView.as_view(), name='fake-data'),

]