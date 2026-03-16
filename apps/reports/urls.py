from django.urls import path
from apps.reports.views import LaporanJurusanView

urlpatterns = [
    path('<str:dept_kode>/', LaporanJurusanView.as_view(), name='laporan-jurusan'),
]
