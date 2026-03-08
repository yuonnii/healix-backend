import math
from datetime import date, datetime, timedelta

from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from healix.permissions import IsDoctor, IsPatient
from .models import DoctorProfile, DoctorAvailability, DoctorReview, Specialty
from .serializers import (
    DoctorProfileSerializer, DoctorListSerializer, UpdateDoctorProfileSerializer,
    DoctorAvailabilitySerializer, DoctorReviewSerializer, CreateReviewSerializer,
    SpecialtySerializer,
)
from .filters import DoctorFilter


def ok(data=None, message='Success', status_code=status.HTTP_200_OK):
    return Response({'success': True, 'message': message, 'data': data}, status=status_code)


@extend_schema(tags=['Doctors'])
class SpecialtyListView(generics.ListAPIView):
    """List all medical specialties."""
    serializer_class   = SpecialtySerializer
    permission_classes = [permissions.AllowAny]
    queryset           = Specialty.objects.all()

    def list(self, request, *args, **kwargs):
        return ok(data=SpecialtySerializer(self.get_queryset(), many=True).data)


@extend_schema(tags=['Doctors'])
class DoctorListView(generics.ListAPIView):
    """
    Search and filter doctors.
    Add ?lat=36.75&lng=3.04&radius_km=10 for nearby search.
    Add ?sort_by=distance to order by proximity.
    """
    serializer_class   = DoctorListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = DoctorFilter
    search_fields      = ['user__first_name', 'user__last_name', 'specialty', 'clinic_name', 'clinic_address']
    ordering_fields    = ['average_rating', 'consultation_fee', 'years_of_experience']
    ordering           = ['-average_rating']

    def get_queryset(self):
        qs = DoctorProfile.objects.select_related('user').filter(is_verified=True)

        lat      = self.request.query_params.get('lat')
        lng      = self.request.query_params.get('lng')
        radius   = float(self.request.query_params.get('radius_km', 10))

        if lat and lng:
            try:
                lat, lng = float(lat), float(lng)
                lat_delta = radius / 111.0
                lng_delta = radius / (111.0 * abs(math.cos(math.radians(lat))))
                qs = qs.filter(
                    latitude__isnull=False,
                    longitude__isnull=False,
                    latitude__range=(lat - lat_delta, lat + lat_delta),
                    longitude__range=(lng - lng_delta, lng + lng_delta),
                )
            except (ValueError, TypeError):
                pass

        return qs


@extend_schema(tags=['Doctors'])
class DoctorDetailView(generics.RetrieveAPIView):
    """Full doctor profile with availability slots and recent reviews."""
    serializer_class   = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset           = DoctorProfile.objects.select_related('user').prefetch_related(
        'availability_slots', 'reviews__patient__user'
    )

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)


@extend_schema(tags=['Doctors'])
class DoctorAvailableSlotsView(APIView):
    """
    Returns available time slots for a doctor on a given date.
    Required query param: ?date=YYYY-MM-DD
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'success': False, 'error': {'message': 'date query param is required (YYYY-MM-DD).'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {'success': False, 'error': {'message': 'Invalid date format. Use YYYY-MM-DD.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor = get_object_or_404(DoctorProfile, pk=pk, is_verified=True)

        # Appointments already booked on this date
        from appointments.models import Appointment
        booked = set(
            Appointment.objects.filter(
                doctor=doctor,
                appointment_date=target_date,
                status__in=['pending', 'confirmed', 'in_progress'],
            ).values_list('appointment_time', flat=True)
        )

        slots = DoctorAvailability.objects.filter(
            doctor=doctor, day_of_week=target_date.weekday(), is_active=True
        )

        available_slots = []
        for slot in slots:
            cursor = datetime.combine(target_date, slot.start_time)
            end    = datetime.combine(target_date, slot.end_time)
            while cursor + timedelta(minutes=slot.slot_duration_minutes) <= end:
                available_slots.append({
                    'time':             cursor.strftime('%H:%M'),
                    'is_available':     cursor.time() not in booked,
                    'duration_minutes': slot.slot_duration_minutes,
                })
                cursor += timedelta(minutes=slot.slot_duration_minutes)

        return ok(data={
            'doctor_id': pk,
            'date':      date_str,
            'day':       target_date.strftime('%A'),
            'slots':     available_slots,
        })


@extend_schema(tags=['Doctors'])
class MyDoctorProfileView(generics.RetrieveUpdateAPIView):
    """Doctor: view or update own profile."""
    permission_classes = [IsDoctor]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateDoctorProfileSerializer
        return DoctorProfileSerializer

    def get_object(self):
        return self.request.user.doctor_profile

    def retrieve(self, request, *args, **kwargs):
        return ok(data=DoctorProfileSerializer(self.get_object(), context={'request': request}).data)

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = UpdateDoctorProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(
            data=DoctorProfileSerializer(instance, context={'request': request}).data,
            message='Profile updated.',
        )


@extend_schema(tags=['Doctors'])
class DoctorAvailabilityListCreateView(generics.ListCreateAPIView):
    """Doctor: list or add weekly availability slots."""
    serializer_class   = DoctorAvailabilitySerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return self.request.user.doctor_profile.availability_slots.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)

    def list(self, request, *args, **kwargs):
        return ok(data=DoctorAvailabilitySerializer(self.get_queryset(), many=True).data)


@extend_schema(tags=['Doctors'])
class DoctorAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Doctor: update or soft-delete an availability slot."""
    serializer_class   = DoctorAvailabilitySerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return self.request.user.doctor_profile.availability_slots.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return ok(message='Availability slot removed.')


@extend_schema(tags=['Doctors'])
class DoctorReviewListView(generics.ListAPIView):
    """Public: list all reviews for a doctor."""
    serializer_class   = DoctorReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DoctorReview.objects.filter(
            doctor_id=self.kwargs['pk']
        ).select_related('patient__user')


@extend_schema(tags=['Doctors'])
class CreateReviewView(generics.CreateAPIView):
    """Patient: submit a review for a doctor (requires a completed appointment)."""
    serializer_class   = CreateReviewSerializer
    permission_classes = [IsPatient]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['doctor'] = get_object_or_404(DoctorProfile, pk=self.kwargs['pk'])
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response({
            'success': True,
            'message': 'Review submitted.',
            'data':    DoctorReviewSerializer(review, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)
