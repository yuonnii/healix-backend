from django.db import models


class VitalReading(models.Model):
    """
    One reading pushed by the IoT device.
    The device sends: heart_rate, temperature, spo2.
    patient and appointment are linked server-side via the device key.
    """

    # Who this reading belongs to
    patient     = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='vital_readings',
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vital_readings',
        help_text='If taken during an appointment session.',
    )

    # The three values the ESP32 sends
    heart_rate  = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Heart rate in BPM.',
    )
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        help_text='Body temperature in °C.',
    )
    spo2        = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Blood oxygen saturation percentage (SpO2 %).',
    )

    # Device metadata
    device_id   = models.CharField(
        max_length=100, blank=True,
        help_text='Identifier of the physical device that sent this reading.',
    )

    # Alert flags — computed and stored so the doctor can filter by them
    is_fever           = models.BooleanField(default=False, help_text='Temperature > 38°C')
    is_tachycardia     = models.BooleanField(default=False, help_text='Heart rate > 110 BPM')
    is_low_spo2        = models.BooleanField(default=False, help_text='SpO2 < 95%')
    has_alert          = models.BooleanField(default=False, help_text='Any alert flag is true')

    # Timestamps
    recorded_at = models.DateTimeField(
        help_text='When the device actually measured this (device clock).',
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the server received this reading.',
    )

    class Meta:
        db_table = 'vital_readings'
        ordering = ['-recorded_at']
        indexes  = [
            models.Index(fields=['patient', '-recorded_at']),
            models.Index(fields=['appointment', '-recorded_at']),
            models.Index(fields=['has_alert', '-recorded_at']),
        ]

    def __str__(self):
        return (
            f'Vitals [{self.recorded_at:%Y-%m-%d %H:%M}] '
            f'— {self.patient.user.get_full_name()} '
            f'HR:{self.heart_rate} T:{self.temperature}°C SpO2:{self.spo2}%'
        )

    def save(self, *args, **kwargs):
        # Compute alert flags automatically on every save
        self.is_fever       = bool(self.temperature and self.temperature > 38)
        self.is_tachycardia = bool(self.heart_rate  and self.heart_rate  > 110)
        self.is_low_spo2    = bool(self.spo2        and self.spo2        < 95)
        self.has_alert      = self.is_fever or self.is_tachycardia or self.is_low_spo2
        super().save(*args, **kwargs)


class DeviceToken(models.Model):
    """
    One row per physical device.
    The device includes its token in every request header:
        X-Device-Key: <token>
    The server looks up which patient this device belongs to from here.
    """
    patient     = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='devices',
    )
    token       = models.CharField(max_length=64, unique=True)
    device_id   = models.CharField(
        max_length=100, blank=True,
        help_text='Human-readable label, e.g. HEALIX-DEVICE-001',
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    last_seen   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'device_tokens'

    def __str__(self):
        return f'{self.device_id} → {self.patient.user.get_full_name()}'
