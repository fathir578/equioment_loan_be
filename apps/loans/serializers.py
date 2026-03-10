from rest_framework import serializers
from apps.loans.models import Loan, LoanItem
from apps.tools.serializers import ToolSerializer

class LoanItemSerializer(serializers.ModelSerializer):
    tool_detail = ToolSerializer(source='tool', read_only=True)

    class Meta:
        model = LoanItem
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    items = LoanItemSerializer(many=True, read_only=True)
    user_username = serializers.ReadOnlyField(source='user.username')
    approver_username = serializers.ReadOnlyField(source='approved_by.username')

    class Meta:
        model = Loan
        fields = '__all__'
        read_only_fields = ('user', 'approved_by', 'status', 'created_at', 'updated_at')
