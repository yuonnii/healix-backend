from django.contrib import admin
from django.utils.html import format_html
from .models import VitalReading, DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display  = ['device_id', 'patient_name', 'token_preview', 'is_active', 'last_seen', 'created_at']
    list_filter   = ['is_active']
    search_fields = ['device_id', 'patient__user__first_name', 'patient__user__last_name', 'token']
    readonly_fields = ['created_at', 'last_seen']

    def patient_name(self, obj):
        return obj.patient.user.get_full_name()
    patient_name.short_description = 'Patient'

    def token_preview(self, obj):
        # Show only first 12 chars for security
        return f'{obj.token[:12]}...'
    token_preview.short_description = 'Token (preview)'


@admin.register(VitalReading)
class VitalReadingAdmin(admin.ModelAdmin):
    list_display  = [
        'recorded_at', 'patient_name', 'heart_rate_display',
        'temperature_display', 'spo2_display', 'alert_display', 'device_id',
    ]
    list_filter   = ['has_alert', 'is_fever', 'is_tachycardia', 'is_low_spo2', 'recorded_at']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'device_id']
    readonly_fields = [
        'is_fever', 'is_tachycardia', 'is_low_spo2', 'has_alert', 'received_at'
    ]
    ordering = ['-recorded_at']

    def patient_name(self, obj):
        return obj.patient.user.get_full_name()
    patient_name.short_description = 'Patient'

    def heart_rate_display(self, obj):
        if obj.heart_rate is None:
            return '—'
        color = 'red' if obj.is_tachycardia else 'green'
        return format_html('<span style="color:{}">{} BPM</span>', color, obj.heart_rate)
    heart_rate_display.short_description = 'Heart Rate'

    def temperature_display(self, obj):
        if obj.temperature is None:
            return '—'
        color = 'red' if obj.is_fever else 'green'
        return format_html('<span style="color:{}">{}°C</span>', color, obj.temperature)
    temperature_display.short_description = 'Temperature'

    def spo2_display(self, obj):
        if obj.spo2 is None:
            return '—'
        color = 'red' if obj.is_low_spo2 else 'green'
        return format_html('<span style="color:{}">{} %</span>', color, obj.spo2)
    spo2_display.short_description = 'SpO2'

    def alert_display(self, obj):
        if obj.has_alert:
            alerts = []
            if obj.is_fever:       alerts.append('Fièvre')
            if obj.is_tachycardia: alerts.append('Tachycardie')
            if obj.is_low_spo2:    alerts.append('SpO2 bas')
            return format_html('<span style="color:red;font-weight:bold">⚠ {}</span>', ', '.join(alerts))
        return format_html('<span style="color:green">✓ Normal</span>')
    alert_display.short_description = 'Alerts'
