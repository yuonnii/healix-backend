from rest_framework import serializers
from .models import Pharmacy, Medicine, PharmacyInventory


class PharmacySerializer(serializers.ModelSerializer):
    is_open_now = serializers.ReadOnlyField()

    class Meta:
        model  = Pharmacy
        fields = [
            'id', 'name', 'license_number', 'address', 'latitude', 'longitude',
            'phone_number', 'email', 'opening_time', 'closing_time',
            'is_open_24h', 'is_open_now', 'is_verified', 'is_active',
        ]
        read_only_fields = ['id', 'is_verified', 'is_open_now']


class MedicineSerializer(serializers.ModelSerializer):
    dosage_form_display = serializers.CharField(source='get_dosage_form_display', read_only=True)

    class Meta:
        model  = Medicine
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'manufacturer',
            'dosage_form', 'dosage_form_display', 'strength',
            'description', 'requires_prescription', 'category', 'barcode',
        ]


class PharmacyInventorySerializer(serializers.ModelSerializer):
    medicine    = MedicineSerializer(read_only=True)
    medicine_id = serializers.PrimaryKeyRelatedField(
        queryset=Medicine.objects.all(), source='medicine', write_only=True
    )
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model  = PharmacyInventory
        fields = [
            'id', 'medicine', 'medicine_id', 'stock_quantity', 'price',
            'expiry_date', 'is_available', 'in_stock', 'last_updated',
        ]
        read_only_fields = ['id', 'in_stock', 'last_updated']


class MedicineAvailabilityEntrySerializer(serializers.Serializer):
    pharmacy_id      = serializers.IntegerField()
    pharmacy_name    = serializers.CharField()
    pharmacy_address = serializers.CharField()
    pharmacy_phone   = serializers.CharField()
    latitude         = serializers.FloatField()
    longitude        = serializers.FloatField()
    is_open_now      = serializers.BooleanField()
    price            = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity   = serializers.IntegerField()
