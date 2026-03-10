# ============================================================
#  core/pagination.py — Standar pagination untuk semua endpoint
# ============================================================

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math


class StandardPagination(PageNumberPagination):
    """
    Pagination standar yang dipakai semua endpoint list.

    Query params yang bisa dipakai client:
        ?page=2          → halaman ke-2
        ?page_size=20    → 20 item per halaman (max 100)

    Contoh response:
    {
        "count": 230,
        "total_pages": 23,
        "current_page": 3,
        "per_page": 10,
        "has_next": true,
        "has_prev": true,
        "results": [...]
    }
    """
    page_size              = 10
    page_size_query_param  = 'page_size'
    max_page_size          = 100
    page_query_param       = 'page'

    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count / self.get_page_size(self.request))

        return Response({
            'count':        self.page.paginator.count,
            'total_pages':  total_pages,
            'current_page': self.page.number,
            'per_page':     self.get_page_size(self.request),
            'has_next':     self.get_next_link() is not None,
            'has_prev':     self.get_previous_link() is not None,
            'results':      data,
        })

    def get_paginated_response_schema(self, schema):
        """Untuk auto-docs Swagger."""
        return {
            'type': 'object',
            'properties': {
                'count':        {'type': 'integer'},
                'total_pages':  {'type': 'integer'},
                'current_page': {'type': 'integer'},
                'per_page':     {'type': 'integer'},
                'has_next':     {'type': 'boolean'},
                'has_prev':     {'type': 'boolean'},
                'results':      schema,
            }
        }
