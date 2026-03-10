from rest_framework import serializers
from apps.activity_logs.models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ActivityLog
        fields = '__all__'
