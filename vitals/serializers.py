from django.utils import timezone
from rest_framework import serializers
from .models import VitalReading, DeviceToken


class VitalReadingInSerializer(serializers.Serializer):
    """
    What the ESP32 device sends.
    Matches the exact JSON keys in the Arduino sketch:
        {"heart_rate": 82, "temperature": 37.2, "spo2": 98}
    recorded_at is optional — if the device doesn't send it we use server time.
    """
    heart_rate  = serializers.IntegerField(min_value=0,   max_value=300, required=False, allow_null=True)
    temperature = serializers.DecimalField(max_digits=4,  decimal_places=1,
                                           min_value=-10, max_value=50,
                                           required=False, allow_null=True)
    spo2        = serializers.IntegerField(min_value=0,   max_value=100, required=False, allow_null=True)
    recorded_at = serializers.DateTimeField(required=False, default=None)

    def validate(self, data):
        if not any([data.get('heart_rate'), data.get('temperature'), data.get('spo2')]):
            raise serializers.ValidationError(
                'At least one of heart_rate, temperature, or spo2 must be provided.'
            )
        if data.get('recorded_at') is None:
            data['recorded_at'] = timezone.now()
        return data


class VitalReadingOutSerializer(serializers.ModelSerializer):
    """What the doctor sees when reading vitals."""
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model  = VitalReading
        fields = [
            'id',
            'patient_name',
            'appointment',
            'heart_rate',
            'temperature',
            'spo2',
            'device_id',
            'is_fever',
            'is_tachycardia',
            'is_low_spo2',
            'has_alert',
            'recorded_at',
            'received_at',
        ]
        read_only_fields = fields


class LatestVitalsSerializer(serializers.Serializer):
    """
    Summary of the most recent reading for a patient —
    used in the doctor's appointment view.
    """
    heart_rate  = serializers.IntegerField(allow_null=True)
    temperature = serializers.DecimalField(max_digits=4, decimal_places=1, allow_null=True)
    spo2        = serializers.IntegerField(allow_null=True)
    is_fever    = serializers.BooleanField()
    is_tachycardia = serializers.BooleanField()
    is_low_spo2 = serializers.BooleanField()
    has_alert   = serializers.BooleanField()
    recorded_at = serializers.DateTimeField()


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Admin-facing: create / list device tokens."""
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model  = DeviceToken
        fields = ['id', 'patient', 'patient_name', 'token', 'device_id', 'is_active', 'created_at', 'last_seen']
        read_only_fields = ['created_at', 'last_seen']
