from django.urls import path, include
from .views import FakeDataAPIView, APIGuideView


urlpatterns = [

    path("guide/", APIGuideView.as_view(), name="api-guide;"),

    path('fake-data/', FakeDataAPIView.as_view(), name='fake-data'),

]