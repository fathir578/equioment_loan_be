from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import RegisterView, MyTokenObtainPairView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', MyTokenObtainPairView.as_view(), name='auth_login'),
    path('refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
]
