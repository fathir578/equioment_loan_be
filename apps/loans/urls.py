from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.loans.views import LoanViewSet, ExportLoansCSVView

router = DefaultRouter()
router.register(r'', LoanViewSet, basename='loan')

urlpatterns = [
    path('export/csv/', ExportLoansCSVView.as_view(), name='export-loans-csv'),
    path('', include(router.urls)),
]
