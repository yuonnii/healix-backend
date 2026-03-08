from datetime import date

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from healix.permissions import IsPatient, IsDoctor, IsAppointmentParticipant
from .models import Appointment, Message
from .serializers import (
    BookAppointmentSerializer,
    AppointmentSerializer,
    DoctorUpdateAppointmentSerializer,
    CancelAppointmentSerializer,
    MessageSerializer,
    SendMessageSerializer,
)


def ok(data=None, message='Success', status_code=status.HTTP_200_OK):
    return Response({'success': True, 'message': message, 'data': data}, status=status_code)


# ── Patient ────────────────────────────────────────────────────────────────────

@extend_schema(tags=['Appointments'])
class BookAppointmentView(generics.CreateAPIView):
    """Patient: book an appointment with a doctor."""
    serializer_class   = BookAppointmentSerializer
    permission_classes = [IsPatient]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response({
            'success': True,
            'message': 'Appointment booked successfully.',
            'data':    AppointmentSerializer(appointment, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Appointments'])
class PatientAppointmentListView(generics.ListAPIView):
    """Patient: list own appointments. Filter by ?status=pending|confirmed|completed|cancelled"""
    serializer_class   = AppointmentSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        qs = Appointment.objects.filter(
            patient=self.request.user.patient_profile
        ).select_related('doctor__user', 'patient__user').order_by('-appointment_date', '-appointment_time')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


@extend_schema(tags=['Appointments'])
class AppointmentDetailView(generics.RetrieveAPIView):
    """Get one appointment. Accessible to the patient or doctor of that appointment."""
    serializer_class   = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAppointmentParticipant]
    queryset           = Appointment.objects.select_related('doctor__user', 'patient__user')

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)


@extend_schema(tags=['Appointments'])
class CancelAppointmentView(APIView):
    """Patient or Doctor: cancel an appointment."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        user = request.user

        # Authorization
        if user.role == 'patient' and appointment.patient.user != user:
            raise PermissionDenied('Not your appointment.')
        if user.role == 'doctor' and appointment.doctor.user != user:
            raise PermissionDenied('Not your appointment.')

        if appointment.status in ('completed', 'cancelled', 'no_show'):
            return Response(
                {'success': False, 'error': {'message': f"Cannot cancel a '{appointment.status}' appointment."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment.status              = Appointment.Status.CANCELLED
        appointment.cancelled_by        = user
        appointment.cancellation_reason = serializer.validated_data.get('reason', '')
        appointment.cancelled_at        = timezone.now()
        appointment.save()

        return ok(
            data=AppointmentSerializer(appointment, context={'request': request}).data,
            message='Appointment cancelled.',
        )


@extend_schema(tags=['Appointments'])
class QueueStatusView(APIView):
    """Patient: get live queue position and estimated wait for an appointment."""
    permission_classes = [IsPatient]

    def get(self, request, pk):
        appointment = get_object_or_404(
            Appointment, pk=pk, patient=request.user.patient_profile
        )
        if appointment.status not in ('pending', 'confirmed'):
            return Response(
                {'success': False, 'error': {'message': f"Appointment is '{appointment.status}', not in queue."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.refresh_wait_estimate()

        return ok(data={
            'appointment_id':         appointment.id,
            'doctor_name':            f'Dr. {appointment.doctor.user.get_full_name()}',
            'clinic_address':         appointment.doctor.clinic_address,
            'appointment_date':       appointment.appointment_date,
            'appointment_time':       appointment.appointment_time,
            'queue_number':           appointment.queue_number,
            'queue_position':         appointment.queue_position + 1,
            'patients_ahead':         appointment.queue_position,
            'estimated_wait_minutes': appointment.estimated_wait_minutes,
            'status':                 appointment.status,
        })


# ── Doctor ─────────────────────────────────────────────────────────────────────

@extend_schema(tags=['Appointments'])
class DoctorAppointmentListView(generics.ListAPIView):
    """Doctor: list appointments. Filter by ?status= and/or ?date=YYYY-MM-DD"""
    serializer_class   = AppointmentSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        qs = Appointment.objects.filter(
            doctor=self.request.user.doctor_profile
        ).select_related('patient__user', 'doctor__user').order_by('appointment_date', 'appointment_time')

        status_filter = self.request.query_params.get('status')
        date_filter   = self.request.query_params.get('date')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_filter:
            qs = qs.filter(appointment_date=date_filter)
        return qs


@extend_schema(tags=['Appointments'])
class DoctorUpdateAppointmentView(generics.UpdateAPIView):
    """Doctor: update appointment status, notes, and diagnosis."""
    serializer_class   = DoctorUpdateAppointmentSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.doctor_profile)

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return ok(
            data=AppointmentSerializer(appointment, context={'request': request}).data,
            message='Appointment updated.',
        )


@extend_schema(tags=['Appointments'])
class TodayQueueView(APIView):
    """Doctor: see today's full queue with per-status counts."""
    permission_classes = [IsDoctor]

    def get(self, request):
        today = date.today()
        qs    = Appointment.objects.filter(
            doctor=request.user.doctor_profile,
            appointment_date=today,
        ).select_related('patient__user').order_by('queue_number')

        return ok(data={
            'date':        today,
            'summary': {
                'total':       qs.count(),
                'pending':     qs.filter(status='pending').count(),
                'confirmed':   qs.filter(status='confirmed').count(),
                'in_progress': qs.filter(status='in_progress').count(),
                'completed':   qs.filter(status='completed').count(),
                'cancelled':   qs.filter(status='cancelled').count(),
            },
            'queue': AppointmentSerializer(qs, many=True, context={'request': request}).data,
        })


@extend_schema(tags=['Appointments'])
class DoctorDashboardView(APIView):
    """Doctor: aggregated stats for the dashboard."""
    permission_classes = [IsDoctor]

    def get(self, request):
        from datetime import timedelta
        doctor   = request.user.doctor_profile
        today    = date.today()
        week_ago = today - timedelta(days=7)

        return ok(data={
            'today': {
                'total':     Appointment.objects.filter(doctor=doctor, appointment_date=today).count(),
                'completed': Appointment.objects.filter(doctor=doctor, appointment_date=today, status='completed').count(),
                'pending':   Appointment.objects.filter(doctor=doctor, appointment_date=today, status__in=['pending', 'confirmed']).count(),
            },
            'this_week': {
                'total':     Appointment.objects.filter(doctor=doctor, appointment_date__range=[week_ago, today]).count(),
                'completed': Appointment.objects.filter(doctor=doctor, appointment_date__range=[week_ago, today], status='completed').count(),
            },
            'overall': {
                'total_appointments': doctor.total_appointments,
                'average_rating':     float(doctor.average_rating),
                'total_reviews':      doctor.total_reviews,
            },
        })


# ── Messaging ──────────────────────────────────────────────────────────────────

@extend_schema(tags=['Appointments'])
class AppointmentMessagesView(generics.ListCreateAPIView):
    """Doctor ↔ Patient messaging within an appointment thread."""
    permission_classes = [permissions.IsAuthenticated]

    def _get_appointment(self):
        appt = get_object_or_404(Appointment, pk=self.kwargs['pk'])
        user = self.request.user
        if user.role == 'patient' and appt.patient.user != user:
            raise PermissionDenied('Not your appointment.')
        if user.role == 'doctor' and appt.doctor.user != user:
            raise PermissionDenied('Not your appointment.')
        return appt

    def get_serializer_class(self):
        return SendMessageSerializer if self.request.method == 'POST' else MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(appointment=self._get_appointment())

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['appointment'] = self._get_appointment()
        return ctx

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        # Auto-mark incoming messages as read
        qs.exclude(sender=request.user).filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return ok(data=MessageSerializer(qs, many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return Response({
            'success': True,
            'message': 'Message sent.',
            'data':    MessageSerializer(msg).data,
        }, status=status.HTTP_201_CREATED)
