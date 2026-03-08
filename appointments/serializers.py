from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, Message


class BookAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Appointment
        fields = [
            'doctor', 'appointment_date', 'appointment_time',
            'appointment_type', 'reason_for_visit', 'symptoms',
        ]

    def validate_appointment_date(self, value):
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError('Appointment date cannot be in the past.')
        return value

    def validate(self, attrs):
        doctor   = attrs['doctor']
        appt_date = attrs['appointment_date']
        appt_time = attrs['appointment_time']

        # Slot conflict
        if Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status__in=['pending', 'confirmed', 'in_progress'],
        ).exists():
            raise serializers.ValidationError(
                {'appointment_time': 'This time slot is already booked. Please choose another.'}
            )

        # Doctor availability
        from doctors.models import DoctorAvailability
        available = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=appt_date.weekday(),
            start_time__lte=appt_time,
            end_time__gt=appt_time,
            is_active=True,
        ).exists()
        if not available:
            raise serializers.ValidationError(
                {'appointment_time': 'Doctor has no availability at this time. Check /api/v1/doctors/{id}/slots/?date=YYYY-MM-DD'}
            )

        if not doctor.is_available_for_booking:
            raise serializers.ValidationError({'doctor': 'This doctor is not accepting bookings.'})

        return attrs

    def create(self, validated_data):
        patient     = self.context['request'].user.patient_profile
        appointment = Appointment.objects.create(patient=patient, **validated_data)
        appointment.refresh_wait_estimate()
        return appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name     = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    patient_phone    = serializers.CharField(source='patient.user.phone_number',  read_only=True)
    doctor_name      = serializers.SerializerMethodField()
    doctor_specialty = serializers.CharField(source='doctor.specialty',   read_only=True)
    doctor_clinic    = serializers.CharField(source='doctor.clinic_name', read_only=True)
    queue_position   = serializers.ReadOnlyField()
    has_review       = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            'id', 'patient_name', 'patient_phone',
            'doctor_name', 'doctor_specialty', 'doctor_clinic',
            'appointment_date', 'appointment_time', 'appointment_type',
            'status', 'queue_number', 'queue_position', 'estimated_wait_minutes',
            'reason_for_visit', 'symptoms', 'notes_by_doctor', 'diagnosis',
            'consultation_fee', 'is_paid',
            'checked_in_at', 'started_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'has_review', 'created_at',
        ]
        read_only_fields = [
            'id', 'queue_number', 'queue_position', 'estimated_wait_minutes',
            'consultation_fee', 'checked_in_at', 'started_at',
            'completed_at', 'cancelled_at', 'created_at',
        ]

    def get_doctor_name(self, obj):
        return f'Dr. {obj.doctor.user.get_full_name()}'

    def get_has_review(self, obj):
        return hasattr(obj, 'review')


class DoctorUpdateAppointmentSerializer(serializers.ModelSerializer):
    """Doctor-facing: update status, notes, diagnosis."""

    VALID_TRANSITIONS = {
        'pending':     ['confirmed', 'cancelled'],
        'confirmed':   ['in_progress', 'cancelled', 'no_show'],
        'in_progress': ['completed'],
    }

    class Meta:
        model  = Appointment
        fields = ['status', 'notes_by_doctor', 'diagnosis', 'estimated_wait_minutes']

    def validate_status(self, value):
        instance = self.instance
        if instance and instance.status in self.VALID_TRANSITIONS:
            allowed = self.VALID_TRANSITIONS[instance.status]
            if value not in allowed:
                raise serializers.ValidationError(
                    f"Cannot move from '{instance.status}' to '{value}'. "
                    f"Allowed: {allowed}"
                )
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        now = timezone.now()
        if new_status == 'confirmed'   and not instance.checked_in_at:
            instance.checked_in_at = now
        if new_status == 'in_progress' and not instance.started_at:
            instance.started_at = now
        if new_status == 'completed'   and not instance.completed_at:
            instance.completed_at = now
            # Update doctor's total appointment count
            instance.doctor.total_appointments = (
                Appointment.objects.filter(doctor=instance.doctor, status='completed').count() + 1
            )
            instance.doctor.save(update_fields=['total_appointments'])
        return super().update(instance, validated_data)


class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role',          read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'sender_name', 'sender_role', 'content', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'sender_name', 'sender_role', 'is_read', 'read_at', 'created_at']


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['content']

    def create(self, validated_data):
        return Message.objects.create(
            appointment=self.context['appointment'],
            sender=self.context['request'].user,
            **validated_data,
        )
