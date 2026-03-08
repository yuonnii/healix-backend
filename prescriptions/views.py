import math

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from healix.permissions import IsPatient, IsDoctor
from .models import Prescription, ScannedPrescription
from .serializers import (
    PrescriptionSerializer,
    CreatePrescriptionSerializer,
    ScannedPrescriptionSerializer,
    ScanUploadSerializer,
)


def ok(data=None, message='Success', status_code=status.HTTP_200_OK):
    return Response({'success': True, 'message': message, 'data': data}, status=status_code)


@extend_schema(tags=['Prescriptions'])
class PatientPrescriptionListView(generics.ListAPIView):
    """Patient: list all own prescriptions."""
    serializer_class   = PrescriptionSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return Prescription.objects.filter(
            patient=self.request.user.patient_profile
        ).select_related('doctor__user', 'appointment').prefetch_related('items__medicine')


@extend_schema(tags=['Prescriptions'])
class PrescriptionDetailView(generics.RetrieveAPIView):
    """Get a prescription. Accessible to the patient it was issued to, or the issuing doctor."""
    serializer_class   = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        prescription = get_object_or_404(
            Prescription.objects.prefetch_related('items__medicine'),
            pk=self.kwargs['pk']
        )
        user = self.request.user
        if user.role == 'patient' and prescription.patient.user != user:
            raise PermissionDenied('Not your prescription.')
        if user.role == 'doctor' and (prescription.doctor is None or prescription.doctor.user != user):
            raise PermissionDenied('Not your prescription.')
        return prescription

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)


@extend_schema(tags=['Prescriptions'])
class DoctorCreatePrescriptionView(generics.CreateAPIView):
    """Doctor: issue a prescription after a completed consultation."""
    serializer_class   = CreatePrescriptionSerializer
    permission_classes = [IsDoctor]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save()
        return Response({
            'success': True,
            'message': 'Prescription issued successfully.',
            'data':    PrescriptionSerializer(prescription, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Prescriptions'])
class ScanPrescriptionView(APIView):
    """
    Patient: upload a prescription image.
    Returns identified medicines and which nearby pharmacies have them in stock.
    Pass ?lat=&lng=&radius_km= to filter pharmacies by proximity.
    """
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = ScanUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the scan record
        scan = ScannedPrescription.objects.create(
            patient=request.user.patient_profile,
            image=serializer.validated_data['image'],
            identified_medicines=_identify_medicines_from_image(serializer.validated_data['image']),
            processed=True,
        )

        # Enrich each identified medicine with pharmacy availability
        enriched = []
        for med_info in scan.identified_medicines:
            enriched.append({
                **med_info,
                'available_at_pharmacies': _find_nearby_pharmacies(med_info['name'], request),
            })

        scan.identified_medicines = enriched
        scan.save(update_fields=['identified_medicines'])

        return Response({
            'success': True,
            'message': 'Prescription scanned successfully.',
            'data': {
                'scan_id':            scan.id,
                'total_medicines':    len(enriched),
                'identified_medicines': enriched,
            },
        }, status=status.HTTP_201_CREATED)


def _identify_medicines_from_image(image_file):
    """
    Stub for OCR + medicine NLP pipeline.
    In production: integrate Google Vision API or Tesseract + a medicines NER model.
    Returns a list of dicts with name/dosage/frequency/duration/confidence.
    """
    return [
        {
            'name':       'Amoxicillin',
            'dosage':     '500mg',
            'frequency':  'Three times daily',
            'duration':   '7 days',
            'confidence': 0.95,
        },
        {
            'name':       'Ibuprofen',
            'dosage':     '400mg',
            'frequency':  'Twice daily with food',
            'duration':   '5 days',
            'confidence': 0.90,
        },
    ]


def _find_nearby_pharmacies(medicine_name, request):
    """Find pharmacies that have a medicine in stock, optionally filtered by proximity."""
    from pharmacies.models import Medicine, PharmacyInventory

    medicines = Medicine.objects.filter(name__icontains=medicine_name)
    if not medicines.exists():
        return []

    inv_qs = PharmacyInventory.objects.filter(
        medicine__in=medicines,
        is_available=True,
        stock_quantity__gt=0,
        pharmacy__is_verified=True,
        pharmacy__is_active=True,
    ).select_related('pharmacy', 'medicine')

    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    if lat and lng:
        try:
            lat, lng = float(lat), float(lng)
            radius   = float(request.query_params.get('radius_km', 10))
            lat_delta = radius / 111.0
            lng_delta = radius / (111.0 * abs(math.cos(math.radians(lat))))
            inv_qs = inv_qs.filter(
                pharmacy__latitude__range=(lat - lat_delta, lat + lat_delta),
                pharmacy__longitude__range=(lng - lng_delta, lng + lng_delta),
            )
        except (ValueError, TypeError):
            pass

    return [
        {
            'pharmacy_id':      item.pharmacy.id,
            'pharmacy_name':    item.pharmacy.name,
            'pharmacy_address': item.pharmacy.address,
            'is_open_now':      item.pharmacy.is_open_now,
            'price':            float(item.price),
            'stock_quantity':   item.stock_quantity,
        }
        for item in inv_qs[:5]
    ]


@extend_schema(tags=['Prescriptions'])
class PatientScanHistoryView(generics.ListAPIView):
    """Patient: list past prescription scans."""
    serializer_class   = ScannedPrescriptionSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return ScannedPrescription.objects.filter(patient=self.request.user.patient_profile)
