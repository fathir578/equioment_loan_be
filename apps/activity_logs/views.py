from rest_framework import viewsets, mixins
from apps.activity_logs.models import ActivityLog
from apps.activity_logs.serializers import ActivityLogSerializer
from core.permissions import IsAdmin

class ActivityLogViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['user', 'action']
    search_fields = ['description', 'action']
