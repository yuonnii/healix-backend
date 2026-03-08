from django.db import models


class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        PROCESSED = 'processed', 'Processed'
        DISPENSED = 'dispensed', 'Dispensed'
        EXPIRED   = 'expired',   'Expired'

    # All string refs
    patient     = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE, related_name='prescriptions')
    doctor      = models.ForeignKey('doctors.DoctorProfile',   on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='prescription',
    )
    prescription_image = models.ImageField(upload_to='prescriptions/', blank=True, null=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes       = models.TextField(blank=True)
    issue_date  = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Prescription #{self.pk} — {self.patient.user.get_full_name()}'


class PrescriptionItem(models.Model):
    prescription      = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine          = models.ForeignKey('pharmacies.Medicine', on_delete=models.SET_NULL, null=True, blank=True)
    medicine_name_raw = models.CharField(max_length=200, help_text='As written on prescription')
    dosage            = models.CharField(max_length=100, blank=True)
    frequency         = models.CharField(max_length=100, blank=True)
    duration          = models.CharField(max_length=100, blank=True)
    instructions      = models.TextField(blank=True)
    quantity          = models.PositiveIntegerField(default=1)
    is_dispensed      = models.BooleanField(default=False)

    class Meta:
        db_table = 'prescription_items'

    def __str__(self):
        return f'{self.medicine_name_raw} — {self.dosage}'


class ScannedPrescription(models.Model):
    """Stores the uploaded image and AI-identified medicines from a prescription scan."""
    patient              = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE, related_name='scanned_prescriptions')
    image                = models.ImageField(upload_to='scans/')
    raw_text             = models.TextField(blank=True, help_text='OCR-extracted text')
    identified_medicines = models.JSONField(default=list)
    linked_prescription  = models.ForeignKey(
        Prescription, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='scans',
    )
    processed  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scanned_prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Scan #{self.pk} by {self.patient.user.get_full_name()}'
