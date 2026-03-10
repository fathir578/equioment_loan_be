from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.activity_logs.views import ActivityLogViewSet

router = DefaultRouter()
router.register(r'', ActivityLogViewSet, basename='activitylog')

urlpatterns = [
    path('', include(router.urls)),
]
