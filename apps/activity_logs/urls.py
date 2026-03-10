from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.activity_logs.views import ActivityLogViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r'', ActivityLogViewSet, basename='activitylog')

urlpatterns = [
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
