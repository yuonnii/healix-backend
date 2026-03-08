from django.db import models
from django.utils import timezone


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING     = 'pending',     'Pending'
        CONFIRMED   = 'confirmed',   'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED   = 'completed',   'Completed'
        CANCELLED   = 'cancelled',   'Cancelled'
        NO_SHOW     = 'no_show',     'No Show'

    class AppointmentType(models.TextChoices):
        IN_PERSON = 'in_person', 'In Person'
        VIDEO     = 'video',     'Video Consultation'
        PHONE     = 'phone',     'Phone Consultation'

    # String refs — avoids circular imports with accounts / doctors
    patient = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE, related_name='appointments')
    doctor  = models.ForeignKey('doctors.DoctorProfile',   on_delete=models.CASCADE, related_name='appointments')

    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20, choices=AppointmentType.choices, default=AppointmentType.IN_PERSON
    )
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    queue_number = models.PositiveIntegerField(null=True, blank=True)
    estimated_wait_minutes = models.PositiveIntegerField(default=0)

    reason_for_visit  = models.TextField(blank=True)
    symptoms          = models.TextField(blank=True)
    notes_by_doctor   = models.TextField(blank=True)
    diagnosis         = models.TextField(blank=True)

    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid          = models.BooleanField(default=False)

    checked_in_at       = models.DateTimeField(null=True, blank=True)
    started_at          = models.DateTimeField(null=True, blank=True)
    completed_at        = models.DateTimeField(null=True, blank=True)
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by        = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cancellations',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table       = 'appointments'
        ordering       = ['appointment_date', 'appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']

    def __str__(self):
        return (
            f'Appointment #{self.pk} — {self.patient.user.get_full_name()} '
            f'with Dr. {self.doctor.user.last_name} on {self.appointment_date} {self.appointment_time}'
        )

    def save(self, *args, **kwargs):
        # Auto-set consultation fee from doctor if not set
        if not self.consultation_fee:
            self.consultation_fee = self.doctor.consultation_fee
        # Assign queue number on first save
        if not self.pk and not self.queue_number:
            self.queue_number = self._next_queue_number()
        super().save(*args, **kwargs)

    def _next_queue_number(self):
        last = (
            Appointment.objects
            .filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                status__in=['pending', 'confirmed', 'in_progress'],
            )
            .order_by('-queue_number')
            .first()
        )
        return (last.queue_number or 0) + 1 if last else 1

    @property
    def queue_position(self):
        """Number of active appointments scheduled before this one today."""
        return Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            status__in=['confirmed', 'in_progress'],
            queue_number__lt=self.queue_number,
        ).count()

    def refresh_wait_estimate(self):
        """Recalculate estimated wait and persist it."""
        slot = self.doctor.availability_slots.filter(
            day_of_week=self.appointment_date.weekday(), is_active=True
        ).first()
        duration = slot.slot_duration_minutes if slot else 30
        self.estimated_wait_minutes = self.queue_position * duration
        self.save(update_fields=['estimated_wait_minutes'])
        return self.estimated_wait_minutes


class Message(models.Model):
    """Doctor ↔ Patient messaging scoped to an appointment."""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender      = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    content     = models.TextField()
    is_read     = models.BooleanField(default=False)
    read_at     = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f'Message from {self.sender.get_full_name()} in appointment #{self.appointment_id}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
