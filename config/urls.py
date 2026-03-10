from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Endpoints
    path('api/v1/auth/',        include('apps.users.urls.auth_urls')),
    path('api/v1/users/',       include('apps.users.urls.user_urls')),
    path('api/v1/categories/',  include('apps.categories.urls')),
    path('api/v1/tools/',       include('apps.tools.urls')),
    path('api/v1/loans/',       include('apps.loans.urls')),
    path('api/v1/returns/',     include('apps.returns.urls')),
    path('api/v1/logs/',        include('apps.activity_logs.urls')),

    # Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
