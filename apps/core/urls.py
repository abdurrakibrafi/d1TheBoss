from django.urls import path, include
from .views import FakeDataAPIView


urlpatterns = [

    path('fake-data/', FakeDataAPIView.as_view(), name='fake-data'),

]