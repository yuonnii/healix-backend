from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Auto-generated API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App routes — all under /api/v1/
    path('api/v1/', include('accounts.urls', namespace='accounts')),
    path('api/v1/', include('doctors.urls', namespace='doctors')),
    path('api/v1/', include('appointments.urls', namespace='appointments')),
    path('api/v1/', include('pharmacies.urls', namespace='pharmacies')),
    path('api/v1/', include('prescriptions.urls', namespace='prescriptions')),
    path('api/v1/', include('vitals.urls', namespace='vitals')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
