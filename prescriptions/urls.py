from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Patient
    path('prescriptions/my/',             views.PatientPrescriptionListView.as_view(), name='my-list'),
    path('prescriptions/<int:pk>/',       views.PrescriptionDetailView.as_view(),      name='detail'),
    path('prescriptions/scan/',           views.ScanPrescriptionView.as_view(),        name='scan'),
    path('prescriptions/scan/history/',   views.PatientScanHistoryView.as_view(),      name='scan-history'),

    # Doctor
    path('prescriptions/create/',         views.DoctorCreatePrescriptionView.as_view(), name='create'),
]
