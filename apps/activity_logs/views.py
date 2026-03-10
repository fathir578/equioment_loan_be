from rest_framework import viewsets, mixins, permissions
from rest_framework.views import APIView
from django.db.models import Count, Sum
from django.contrib.auth import get_user_model
from apps.activity_logs.models import ActivityLog
from apps.activity_logs.serializers import ActivityLogSerializer
from apps.tools.models import Tool
from apps.categories.models import Category
from apps.loans.models import Loan, LoanItem
from apps.returns.models import Return
from core.permissions import IsAdmin
from core.utils import success_response

User = get_user_model()

class ActivityLogViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['user', 'action']
    search_fields = ['description', 'action']

class DashboardStatsView(APIView):
    """
    Dashboard Statistik untuk Admin.
    Menampilkan ringkasan data penting dalam satu endpoint.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        stats = {
            'counts': {
                'users':      User.objects.count(),
                'tools':      Tool.objects.count(),
                'categories': Category.objects.count(),
                'loans':      Loan.objects.count(),
            },
            'loans_status': {
                'pending':  Loan.objects.filter(status='pending').count(),
                'approved': Loan.objects.filter(status='approved').count(),
                'returned': Loan.objects.filter(status='returned').count(),
            },
            'financial': {
                'total_fines': Return.objects.aggregate(total=Sum('total_fine'))['total'] or 0,
            },
            'top_tools': Tool.objects.annotate(
                total_borrowed=Count('loan_items')
            ).order_by('-total_borrowed')[:5].values('id', 'name', 'total_borrowed')
        }
        return success_response(stats, message="Statistik dashboard berhasil diambil.")
