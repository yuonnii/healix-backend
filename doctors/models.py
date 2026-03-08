from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Specialty(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    icon        = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table           = 'specialties'
        verbose_name_plural = 'Specialties'
        ordering            = ['name']

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    # 'accounts.User' — string reference avoids circular import
    user         = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='doctor_profile')
    specialty    = models.CharField(max_length=100)
    specialty_obj = models.ForeignKey(
        Specialty, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors'
    )
    license_number      = models.CharField(max_length=50, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    bio                 = models.TextField(blank=True)
    education           = models.TextField(blank=True)
    languages           = models.CharField(max_length=200, blank=True, help_text='Comma-separated')

    clinic_name     = models.CharField(max_length=200, blank=True)
    clinic_address  = models.TextField(blank=True)
    latitude        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_available_for_booking = models.BooleanField(default=True)
    is_verified              = models.BooleanField(default=False)

    # Cached aggregates (updated via update_rating_cache)
    average_rating      = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews       = models.PositiveIntegerField(default=0)
    total_appointments  = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_profiles'

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} — {self.specialty}'

    def update_rating_cache(self):
        from django.db.models import Avg, Count
        agg = self.reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        self.average_rating = round(agg['avg'] or 0, 2)
        self.total_reviews  = agg['count']
        self.save(update_fields=['average_rating', 'total_reviews'])


class DoctorAvailability(models.Model):
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    doctor               = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week          = models.IntegerField(choices=DAYS)
    start_time           = models.TimeField()
    end_time             = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=30)
    max_patients         = models.PositiveIntegerField(default=1)
    is_active            = models.BooleanField(default=True)

    class Meta:
        db_table       = 'doctor_availability'
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering        = ['day_of_week', 'start_time']

    def __str__(self):
        return f'Dr. {self.doctor.user.last_name} — {self.get_day_of_week_display()} {self.start_time}–{self.end_time}'


class DoctorReview(models.Model):
    doctor      = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='reviews')
    # String refs for cross-app FKs
    patient     = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE, related_name='reviews_given')
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='review',
    )
    rating      = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment     = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table       = 'doctor_reviews'
        unique_together = ['doctor', 'patient']
        ordering        = ['-created_at']

    def __str__(self):
        return f'Review for Dr. {self.doctor.user.last_name} by {self.patient.user.get_full_name()}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Refresh cached rating on the doctor profile
        self.doctor.update_rating_cache()
