from rest_framework import request, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection
from django.http import HttpResponse
import json
import csv
from apps.loans.models import Loan
from apps.loans.serializers import LoanSerializer
from core.permissions import IsOwnerOrAdmin, IsAdminOrPetugas
from core.utils import success_response, created_response

class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filterset_fields = ['user']  # Remove 'status' from filterset_fields - we handle it manually
    search_fields = ['notes', 'user__username']

    def get_queryset(self):
        user = self.request.user
        queryset = Loan.objects.all().select_related('user', 'user__department')

        # Handle status filter - support comma-separated values
        status_param = self.request.query_params.get('status', None)
        if status_param:
            status_list = [s.strip() for s in status_param.split(',')]
            queryset = queryset.filter(status__in=status_list)

        # Filter berdasarkan role user
        if user.role == 'peminjam':
            # Siswa hanya bisa lihat peminjaman sendiri
            queryset = queryset.filter(user=user)
        elif user.role == 'petugas':
            # Petugas hanya bisa lihat peminjaman dari departmentnya
            if hasattr(user, 'department') and user.department:
                queryset = queryset.filter(user__department=user.department)
            else:
                # Petugas tanpa department tidak bisa lihat data
                queryset = queryset.none()
        # Admin → no filter, bisa lihat semua

        return queryset

    def create(self, request, *args, **kwargs):
        # Gunakan Stored Procedure sp_create_loan
        requested_user_id = request.data.get('user_id')
        user_id = int(requested_user_id) if requested_user_id else request.user.id
        loan_date = request.data.get('loan_date')
        due_date = request.data.get('due_date')
        notes = request.data.get('notes', '')
        items = request.data.get('items', []) # Expect list of {"tool_id": 1, "qty": 1}

        with connection.cursor() as cursor:
            # MySQL OUT params are tricky with fetchone.
            # sp_create_loan(p_user_id, p_loan_date, p_due_date, p_notes, p_items_json, OUT p_loan_id, OUT p_message)
            cursor.execute("SET @p_loan_id = 0")
            cursor.execute("SET @p_message = ''")
            cursor.execute(
                "CALL sp_create_loan(%s, %s, %s, %s, %s, @p_loan_id, @p_message)",
                [user_id, loan_date, due_date, notes, json.dumps(items)]
            )
            cursor.execute("SELECT @p_loan_id, @p_message")
            loan_id, message = cursor.fetchone()

        if loan_id == 0:
            return Response({'success': False, 'message': message}, status=status.HTTP_400_BAD_REQUEST)

        loan = Loan.objects.get(id=loan_id)
        return created_response(LoanSerializer(loan).data, message=message)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrPetugas])
    def approve(self, request, pk=None):
        try:
            loan = self.get_object()
            if loan.status != 'pending':
                return Response({'success': False, 'message': 'Hanya peminjaman berstatus pending yang bisa disetujui.'}, status=status.HTTP_400_BAD_REQUEST)

            loan.status = 'approved'
            loan.approved_by = request.user
            loan.save() # This triggers DB triggers (e.g., stock update)
            return success_response(LoanSerializer(loan).data, message="Peminjaman disetujui.")
        except Exception as e:
            # Catch DB trigger errors (SIGNAL SQLSTATE)
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrPetugas])
    def reject(self, request, pk=None):
        try:
            loan = self.get_object()
            if loan.status != 'pending':
                return Response({'success': False, 'message': 'Hanya peminjaman berstatus pending yang bisa ditolak.'}, status=status.HTTP_400_BAD_REQUEST)

            loan.status = 'rejected'
            loan.approved_by = request.user
            loan.save()
            return success_response(LoanSerializer(loan).data, message="Peminjaman ditolak.")
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ExportLoansCSVView(APIView):
    """
    Export daftar peminjaman ke format CSV.
    Hanya untuk Admin/Petugas.
    """
    permission_classes = [IsAdminOrPetugas]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="laporan_peminjaman.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Peminjam', 'Tanggal Pinjam', 'Jatuh Tempo', 'Status', 'Alat'])

        loans = Loan.objects.all().select_related('user').prefetch_related('items__tool')
        for loan in loans:
            tools_str = ", ".join([f"{item.tool.name} (x{item.quantity})" for item in loan.items.all()])
            writer.writerow([
                loan.id,
                loan.user.username,
                loan.loan_date,
                loan.due_date,
                loan.status,
                tools_str
            ])

        return response
