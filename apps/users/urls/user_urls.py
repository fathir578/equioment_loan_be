from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # Custom URLs for petugas CRUD (with permissions)
    path('petugas/<int:pk>/', UserViewSet.as_view({
        'put': 'update_petugas',
        'delete': 'delete_petugas',
        'get': 'retrieve_petugas'
    }, permission_classes=[IsAuthenticated, IsAdmin]), name='user-petugas-detail'),
]
