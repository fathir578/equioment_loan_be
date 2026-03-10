from rest_framework import serializers
from apps.tools.models import Tool
from apps.categories.serializers import CategorySerializer

class ToolSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Tool
        fields = '__all__'
        read_only_fields = ('qr_code', 'created_at', 'updated_at')
