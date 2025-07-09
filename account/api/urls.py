from django.urls import path
from .views import UserInfoAPIView

urlpatterns = [
    path('me/', UserInfoAPIView.as_view(), name='user-info'),
]
