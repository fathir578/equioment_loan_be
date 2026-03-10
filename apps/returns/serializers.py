from rest_framework import serializers
from apps.returns.models import Return, ReturnItem

class ReturnItemSerializer(serializers.ModelSerializer):
    tool_name = serializers.ReadOnlyField(source='loan_item.tool.name')

    class Meta:
        model = ReturnItem
        fields = '__all__'

class ReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)
    processed_by_username = serializers.ReadOnlyField(source='processed_by.username')

    class Meta:
        model = Return
        fields = '__all__'
        read_only_fields = ('processed_by', 'created_at')
