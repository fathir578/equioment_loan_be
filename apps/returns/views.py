from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import connection
import json
from apps.returns.models import Return
from apps.returns.serializers import ReturnSerializer
from core.permissions import IsAdminOrPetugas
from core.utils import success_response, created_response

class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAdminOrPetugas]
    filterset_fields = ['loan', 'processed_by']

    def create(self, request, *args, **kwargs):
        # Gunakan Stored Procedure sp_process_return
        loan_id = request.data.get('loan_id')
        processed_by = request.user.id
        return_date = request.data.get('return_date')
        fine_per_day = request.data.get('fine_per_day', 5000)
        items = request.data.get('items', []) # [{"loan_item_id":1, "qty_returned":1, "condition":"baik"}]
        notes = request.data.get('notes', '')

        with connection.cursor() as cursor:
            # sp_process_return(p_loan_id, p_processed_by, p_return_date, p_fine_per_day, p_items_json, p_notes, OUT p_return_id, OUT p_late_days, OUT p_total_fine, OUT p_message)
            cursor.execute("SET @p_return_id = 0")
            cursor.execute("SET @p_late_days = 0")
            cursor.execute("SET @p_total_fine = 0.00")
            cursor.execute("SET @p_message = ''")
            cursor.execute(
                "CALL sp_process_return(%s, %s, %s, %s, %s, %s, @p_return_id, @p_late_days, @p_total_fine, @p_message)",
                [loan_id, processed_by, return_date, fine_per_day, json.dumps(items), notes]
            )
            cursor.execute("SELECT @p_return_id, @p_late_days, @p_total_fine, @p_message")
            return_id, late_days, total_fine, message = cursor.fetchone()

        if return_id == 0:
            return Response({'success': False, 'message': message}, status=status.HTTP_400_BAD_REQUEST)

        ret_obj = Return.objects.get(id=return_id)
        return created_response(ReturnSerializer(ret_obj).data, message=message)
