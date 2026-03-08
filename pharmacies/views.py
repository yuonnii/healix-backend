import math
import unicodedata

from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from healix.permissions import IsPharmacy
from .models import Pharmacy, Medicine, PharmacyInventory
from .serializers import (
    PharmacySerializer, MedicineSerializer,
    PharmacyInventorySerializer,)

def normalize(text):
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()

def ok(data=None, message='Success', status_code=status.HTTP_200_OK):
    return Response({'success': True, 'message': message, 'data': data}, status=status_code)


def _nearby_filter(qs, lat_field, lng_field, lat, lng, radius_km):
    """Apply bounding-box filter for nearby results."""
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * abs(math.cos(math.radians(lat))))
    return qs.filter(**{
        f'{lat_field}__range': (lat - lat_delta, lat + lat_delta),
        f'{lng_field}__range': (lng - lng_delta, lng + lng_delta),
    })


@extend_schema(tags=['Pharmacies'])
class PharmacyListView(generics.ListAPIView):
    """
    Search pharmacies. Supports ?lat=&lng=&radius_km= for nearby.
    Also ?search= for name/address full-text.
    """
    serializer_class   = PharmacySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name', 'address']

    def get_queryset(self):
        qs = Pharmacy.objects.filter(is_verified=True, is_active=True)
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        if lat and lng:
            try:
                qs = _nearby_filter(
                    qs, 'latitude', 'longitude',
                    float(lat), float(lng),
                    float(self.request.query_params.get('radius_km', 10)),
                )
            except (ValueError, TypeError):
                pass
        return qs


@extend_schema(tags=['Pharmacies'])
class PharmacyDetailView(generics.RetrieveAPIView):
    """Get pharmacy detail including current inventory."""
    serializer_class   = PharmacySerializer
    permission_classes = [permissions.AllowAny]
    queryset           = Pharmacy.objects.filter(is_verified=True)

    def retrieve(self, request, *args, **kwargs):
        pharmacy  = self.get_object()
        inventory = PharmacyInventory.objects.filter(
            pharmacy=pharmacy, is_available=True
        ).select_related('medicine')
        return ok(data={
            'pharmacy':  PharmacySerializer(pharmacy).data,
            'inventory': PharmacyInventorySerializer(inventory, many=True).data,
        })


@extend_schema(tags=['Pharmacies'])
class MedicineListView(generics.ListAPIView):
    """Search medicines by name, generic name, or barcode."""
    serializer_class   = MedicineSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        queryset = Medicine.objects.all()
        search = self.request.query_params.get('search', '')
        if search:
            normalized = normalize(search)
            all_meds = list(queryset)
            ids = [
                m.id for m in all_meds
                if normalized in normalize(m.name or "")
                or normalized in normalize(m.generic_name or "")
                or normalized in normalize(m.brand_name or "")
            ]
            queryset = queryset.filter(id__in=ids)
        return queryset
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name', 'generic_name', 'brand_name', 'barcode', 'category']


@extend_schema(tags=['Pharmacies'])
class MedicineAvailabilityView(APIView):
    """
    Check which pharmacies near you have a specific medicine in stock.
    Optional: ?lat=&lng=&radius_km=
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, medicine_id):
        medicine = get_object_or_404(Medicine, pk=medicine_id)

        inv_qs = PharmacyInventory.objects.filter(
            medicine=medicine,
            is_available=True,
            stock_quantity__gt=0,
            pharmacy__is_verified=True,
            pharmacy__is_active=True,
        ).select_related('pharmacy')

        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        if lat and lng:
            try:
                inv_qs = _nearby_filter(
                    inv_qs, 'pharmacy__latitude', 'pharmacy__longitude',
                    float(lat), float(lng),
                    float(request.query_params.get('radius_km', 10)),
                )
            except (ValueError, TypeError):
                pass

        results = [
            {
                'pharmacy_id':      item.pharmacy.id,
                'pharmacy_name':    item.pharmacy.name,
                'pharmacy_address': item.pharmacy.address,
                'pharmacy_phone':   item.pharmacy.phone_number,
                'latitude':         float(item.pharmacy.latitude)  if item.pharmacy.latitude  else None,
                'longitude':        float(item.pharmacy.longitude) if item.pharmacy.longitude else None,
                'is_open_now':      item.pharmacy.is_open_now,
                'price':            float(item.price),
                'stock_quantity':   item.stock_quantity,
            }
            for item in inv_qs
        ]

        return ok(data={
            'medicine':          MedicineSerializer(medicine).data,
            'available_at':      results,
            'total_pharmacies':  len(results),
        })


@extend_schema(tags=['Pharmacies'])
class PharmacyInventoryListCreateView(generics.ListCreateAPIView):
    """Pharmacy: view or add medicines to inventory."""
    serializer_class   = PharmacyInventorySerializer
    permission_classes = [IsPharmacy]

    def get_queryset(self):
        return PharmacyInventory.objects.filter(
            pharmacy=self.request.user.pharmacy_profile
        ).select_related('medicine')

    def perform_create(self, serializer):
        serializer.save(pharmacy=self.request.user.pharmacy_profile)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return ok(data=self.get_serializer(qs, many=True).data)


@extend_schema(tags=['Pharmacies'])
class PharmacyInventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Pharmacy: update stock/price or mark medicine unavailable."""
    serializer_class   = PharmacyInventorySerializer
    permission_classes = [IsPharmacy]

    def get_queryset(self):
        return PharmacyInventory.objects.filter(pharmacy=self.request.user.pharmacy_profile)

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(data=serializer.data, message='Inventory updated.')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_available = False
        instance.save(update_fields=['is_available'])
        return ok(message='Medicine marked as unavailable.')
