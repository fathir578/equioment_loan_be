from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.loans.views import LoanViewSet

router = DefaultRouter()
router.register(r'', LoanViewSet, basename='loan')

urlpatterns = [
    path('', include(router.urls)),
]
