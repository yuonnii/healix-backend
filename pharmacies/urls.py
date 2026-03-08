from django.urls import path
from . import views

app_name = 'pharmacies'

urlpatterns = [
    # Public
    path('pharmacies/',                         views.PharmacyListView.as_view(),            name='list'),
    path('pharmacies/<int:pk>/',                views.PharmacyDetailView.as_view(),          name='detail'),
    path('medicines/',                          views.MedicineListView.as_view(),            name='medicine-list'),
    path('medicines/<int:medicine_id>/availability/', views.MedicineAvailabilityView.as_view(), name='medicine-availability'),

    # Pharmacy (authenticated)
    path('pharmacies/me/inventory/',            views.PharmacyInventoryListCreateView.as_view(), name='my-inventory'),
    path('pharmacies/me/inventory/<int:pk>/',   views.PharmacyInventoryDetailView.as_view(),     name='inventory-detail'),
]
