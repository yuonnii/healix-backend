from rest_framework import serializers
from django.db import transaction
from .models import Prescription, PrescriptionItem, ScannedPrescription


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True, default=None)

    class Meta:
        model  = PrescriptionItem
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_name_raw',
            'dosage', 'frequency', 'duration', 'instructions',
            'quantity', 'is_dispensed',
        ]


class PrescriptionItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PrescriptionItem
        fields = ['medicine', 'medicine_name_raw', 'dosage', 'frequency', 'duration', 'instructions', 'quantity']


class PrescriptionSerializer(serializers.ModelSerializer):
    items       = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name  = serializers.SerializerMethodField()
    image_url    = serializers.SerializerMethodField()

    class Meta:
        model  = Prescription
        fields = [
            'id', 'patient_name', 'doctor_name',
            'appointment', 'prescription_image', 'image_url',
            'status', 'notes', 'issue_date', 'expiry_date',
            'items', 'created_at',
        ]
        read_only_fields = ['id', 'patient_name', 'doctor_name', 'created_at']

    def get_doctor_name(self, obj):
        return f'Dr. {obj.doctor.user.get_full_name()}' if obj.doctor else None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.prescription_image and request:
            return request.build_absolute_uri(obj.prescription_image.url)
        return None


class CreatePrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemWriteSerializer(many=True)

    class Meta:
        model  = Prescription
        fields = ['appointment', 'notes', 'issue_date', 'expiry_date', 'items']

    def validate_appointment(self, appointment):
        if appointment and appointment.doctor.user != self.context['request'].user:
            raise serializers.ValidationError('This appointment does not belong to your account.')
        if appointment and appointment.status != 'completed':
            raise serializers.ValidationError('Prescription can only be issued for completed appointments.')
        return appointment

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        doctor     = self.context['request'].user.doctor_profile
        appointment = validated_data.get('appointment')
        patient    = appointment.patient if appointment else None

        prescription = Prescription.objects.create(
            doctor=doctor, patient=patient, **validated_data
        )
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        return prescription


class ScannedPrescriptionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ScannedPrescription
        fields = ['id', 'image', 'image_url', 'raw_text', 'identified_medicines',
                  'linked_prescription', 'processed', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ScanUploadSerializer(serializers.Serializer):
    """Accepts just the image file for scanning."""
    image = serializers.ImageField()
