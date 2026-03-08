from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from healix.permissions import IsDoctor, IsPatient
from appointments.models import Appointment
from .models import VitalReading, DeviceToken
from .permissions import IsIoTDevice
from .serializers import (
    VitalReadingInSerializer,
    VitalReadingOutSerializer,
    LatestVitalsSerializer,
    DeviceTokenSerializer,
)


# ─── Device endpoint ──────────────────────────────────────────────────────────

class DevicePushView(APIView):
    """
    POST /api/v1/vitals/push/

    Called by the ESP32 device every 5 seconds.
    Authentication: X-Device-Key: <token>   (no JWT needed)

    The device optionally passes an appointment_id query param so the reading
    gets linked to the active appointment:
        POST /api/v1/vitals/push/?appointment_id=7
    """
    permission_classes = [IsIoTDevice]
    authentication_classes = []   # no JWT — device uses X-Device-Key instead

    @extend_schema(
        tags=['Vitals'],
        summary='Push a vital reading from the IoT device',
        description=(
            'Called by the ESP32 device. Authenticate with `X-Device-Key: <token>` header.\n\n'
            'Optionally pass `?appointment_id=<id>` to link the reading to an active appointment.'
        ),
        parameters=[
            OpenApiParameter(
                name='appointment_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Link this reading to an appointment.',
            )
        ],
        request=VitalReadingInSerializer,
        responses={201: VitalReadingOutSerializer},
    )
    def post(self, request):
        serializer = VitalReadingInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'status_code': 400,
                 'message': 'Invalid data from device.', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data    = serializer.validated_data
        patient = request.device_token.patient

        # Optionally link to an appointment
        appointment = None
        appt_id = request.query_params.get('appointment_id')
        if appt_id:
            try:
                appointment = Appointment.objects.get(
                    pk=appt_id,
                    patient=patient,
                    status__in=['confirmed', 'in_progress'],
                )
            except Appointment.DoesNotExist:
                pass  # silently ignore bad/inactive appointment id

        reading = VitalReading.objects.create(
            patient=patient,
            appointment=appointment,
            heart_rate=data.get('heart_rate'),
            temperature=data.get('temperature'),
            spo2=data.get('spo2'),
            device_id=request.device_token.device_id,
            recorded_at=data['recorded_at'],
        )

        out = VitalReadingOutSerializer(reading)
        return Response(
            {'success': True, 'message': 'Reading saved.', 'data': out.data},
            status=status.HTTP_201_CREATED,
        )


# ─── Doctor endpoints ─────────────────────────────────────────────────────────

class PatientVitalsView(APIView):
    """
    GET /api/v1/vitals/patient/<patient_id>/

    Returns paginated vital readings for a patient.
    Doctors only.

    Query params:
        ?alerts_only=true   — only readings with has_alert=true
        ?limit=50           — number of readings to return (default 100, max 500)
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    @extend_schema(
        tags=['Vitals'],
        summary='Get vital readings for a patient (doctor)',
        parameters=[
            OpenApiParameter('alerts_only', OpenApiTypes.BOOL,  OpenApiParameter.QUERY,
                             description='Only return readings that triggered an alert.'),
            OpenApiParameter('limit',       OpenApiTypes.INT,   OpenApiParameter.QUERY,
                             description='Max number of readings to return (default 100).'),
        ],
        responses={200: VitalReadingOutSerializer(many=True)},
    )
    def get(self, request, patient_id):
        from accounts.models import PatientProfile
        try:
            patient = PatientProfile.objects.get(pk=patient_id)
        except PatientProfile.DoesNotExist:
            return Response(
                {'success': False, 'error': {'status_code': 404,
                 'message': 'Patient not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs = VitalReading.objects.filter(patient=patient)

        if request.query_params.get('alerts_only', '').lower() == 'true':
            qs = qs.filter(has_alert=True)

        limit = min(int(request.query_params.get('limit', 100)), 500)
        qs    = qs[:limit]

        serializer = VitalReadingOutSerializer(qs, many=True)

        # Also include latest summary at the top
        latest = VitalReading.objects.filter(patient=patient).first()
        latest_data = LatestVitalsSerializer(latest).data if latest else None

        return Response({
            'success': True,
            'data': {
                'patient_id':   patient_id,
                'patient_name': patient.user.get_full_name(),
                'latest':       latest_data,
                'readings':     serializer.data,
            }
        })


class AppointmentVitalsView(APIView):
    """
    GET /api/v1/vitals/appointment/<appointment_id>/

    Returns all readings taken during a specific appointment.
    Accessible by the doctor of that appointment only.
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    @extend_schema(
        tags=['Vitals'],
        summary='Get vitals for a specific appointment (doctor)',
        responses={200: VitalReadingOutSerializer(many=True)},
    )
    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                pk=appointment_id,
                doctor=request.user.doctor_profile,
            )
        except Appointment.DoesNotExist:
            return Response(
                {'success': False, 'error': {'status_code': 404,
                 'message': 'Appointment not found or not yours.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

        readings   = VitalReading.objects.filter(appointment=appointment)
        serializer = VitalReadingOutSerializer(readings, many=True)

        # Compute simple stats if there are readings
        stats = None
        if readings.exists():
            hr_values   = [r.heart_rate  for r in readings if r.heart_rate  is not None]
            temp_values = [r.temperature for r in readings if r.temperature is not None]
            spo2_values = [r.spo2        for r in readings if r.spo2        is not None]
            stats = {
                'total_readings': readings.count(),
                'alert_count':    readings.filter(has_alert=True).count(),
                'heart_rate': {
                    'min': min(hr_values)   if hr_values   else None,
                    'max': max(hr_values)   if hr_values   else None,
                    'avg': round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
                },
                'temperature': {
                    'min': float(min(temp_values)) if temp_values else None,
                    'max': float(max(temp_values)) if temp_values else None,
                    'avg': round(float(sum(temp_values)) / len(temp_values), 1) if temp_values else None,
                },
                'spo2': {
                    'min': min(spo2_values) if spo2_values else None,
                    'max': max(spo2_values) if spo2_values else None,
                    'avg': round(sum(spo2_values) / len(spo2_values), 1) if spo2_values else None,
                },
            }

        return Response({
            'success': True,
            'data': {
                'appointment_id': appointment_id,
                'stats':    stats,
                'readings': serializer.data,
            }
        })


class LatestVitalsView(APIView):
    """
    GET /api/v1/vitals/patient/<patient_id>/latest/

    Returns only the single most recent reading for a patient.
    Useful for the doctor's appointment panel to show live values.
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    @extend_schema(
        tags=['Vitals'],
        summary='Get the latest vital reading for a patient (doctor)',
        responses={200: VitalReadingOutSerializer},
    )
    def get(self, request, patient_id):
        reading = VitalReading.objects.filter(patient_id=patient_id).first()
        if not reading:
            return Response(
                {'success': False, 'error': {'status_code': 404,
                 'message': 'No readings found for this patient.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'success': True,
            'data': VitalReadingOutSerializer(reading).data,
        })


# ─── Patient's own vitals ─────────────────────────────────────────────────────

class MyVitalsView(APIView):
    """
    GET /api/v1/vitals/me/

    Patients can view their own recent readings.
    """
    permission_classes = [IsAuthenticated, IsPatient]

    @extend_schema(
        tags=['Vitals'],
        summary='Get my own recent vital readings (patient)',
        parameters=[
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Number of readings to return (default 50).'),
        ],
        responses={200: VitalReadingOutSerializer(many=True)},
    )
    def get(self, request):
        limit    = min(int(request.query_params.get('limit', 50)), 200)
        readings = VitalReading.objects.filter(
            patient=request.user.patient_profile
        )[:limit]
        return Response({
            'success': True,
            'data': VitalReadingOutSerializer(readings, many=True).data,
        })


# ─── Admin: manage device tokens ─────────────────────────────────────────────

class DeviceTokenListCreateView(APIView):
    """
    GET  /api/v1/vitals/devices/         — list all registered devices
    POST /api/v1/vitals/devices/         — register a new device for a patient

    Admin/staff only. Use the Django admin panel or this endpoint
    to generate a token and paste it into the Arduino sketch.
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        perms = super().get_permissions()
        # only staff can manage devices
        return perms

    @extend_schema(tags=['Vitals'], summary='List all device tokens (admin)')
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'success': False, 'error': {'status_code': 403,
                 'message': 'Admin access required.', 'details': {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        tokens = DeviceToken.objects.select_related('patient__user').all()
        return Response({
            'success': True,
            'data': DeviceTokenSerializer(tokens, many=True).data,
        })

    @extend_schema(
        tags=['Vitals'],
        summary='Register a new IoT device for a patient (admin)',
        request=DeviceTokenSerializer,
        responses={201: DeviceTokenSerializer},
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'success': False, 'error': {'status_code': 403,
                 'message': 'Admin access required.', 'details': {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        import secrets
        data = request.data.copy()
        # Auto-generate a secure token if not provided
        if not data.get('token'):
            data['token'] = secrets.token_hex(32)

        serializer = DeviceTokenSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'status_code': 400,
                 'message': 'Invalid data.', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = serializer.save()
        return Response(
            {
                'success': True,
                'message': 'Device registered. Copy the token into your Arduino sketch.',
                'data': DeviceTokenSerializer(token).data,
            },
            status=status.HTTP_201_CREATED,
        )


class DeviceTokenDetailView(APIView):
    """
    PATCH /api/v1/vitals/devices/<id>/   — enable/disable a device
    DELETE /api/v1/vitals/devices/<id>/  — remove a device
    """
    permission_classes = [IsAuthenticated]

    def _get_token(self, pk, request):
        if not request.user.is_staff:
            return None, Response(
                {'success': False, 'error': {'status_code': 403,
                 'message': 'Admin access required.', 'details': {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            return DeviceToken.objects.get(pk=pk), None
        except DeviceToken.DoesNotExist:
            return None, Response(
                {'success': False, 'error': {'status_code': 404,
                 'message': 'Device not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(tags=['Vitals'], summary='Enable or disable a device (admin)')
    def patch(self, request, pk):
        token, err = self._get_token(pk, request)
        if err:
            return err
        token.is_active = request.data.get('is_active', token.is_active)
        token.save(update_fields=['is_active'])
        return Response({'success': True, 'data': DeviceTokenSerializer(token).data})

    @extend_schema(tags=['Vitals'], summary='Delete a device token (admin)')
    def delete(self, request, pk):
        token, err = self._get_token(pk, request)
        if err:
            return err
        token.delete()
        return Response({'success': True, 'message': 'Device removed.'}, status=status.HTTP_200_OK)
