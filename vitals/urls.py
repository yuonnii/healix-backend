from django.urls import path
from . import views

app_name = 'vitals'

urlpatterns = [
    # ── Device ────────────────────────────────────────────────────────────────
    # The ESP32 POSTs here every 5 seconds
    path('vitals/push/',                            views.DevicePushView.as_view(),            name='push'),

    # ── Doctor ────────────────────────────────────────────────────────────────
    # All readings for a patient (with optional ?alerts_only=true)
    path('vitals/patient/<int:patient_id>/',        views.PatientVitalsView.as_view(),         name='patient-vitals'),
    # Only the single latest reading (for live display in the appointment panel)
    path('vitals/patient/<int:patient_id>/latest/', views.LatestVitalsView.as_view(),          name='patient-latest'),
    # All readings taken during one appointment + session stats
    path('vitals/appointment/<int:appointment_id>/',views.AppointmentVitalsView.as_view(),     name='appointment-vitals'),

    # ── Patient ───────────────────────────────────────────────────────────────
    # Patient views their own readings
    path('vitals/me/',                              views.MyVitalsView.as_view(),              name='my-vitals'),

    # ── Admin: device token management ───────────────────────────────────────
    path('vitals/devices/',                         views.DeviceTokenListCreateView.as_view(), name='devices'),
    path('vitals/devices/<int:pk>/',                views.DeviceTokenDetailView.as_view(),     name='device-detail'),
]
