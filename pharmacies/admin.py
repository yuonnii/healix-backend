from django.contrib import admin
from .models import Pharmacy, Medicine, PharmacyInventory


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'address', 'is_verified', 'is_active', 'is_open_24h']
    list_filter   = ['is_verified', 'is_active', 'is_open_24h']
    search_fields = ['name', 'address', 'license_number']
    actions       = ['verify_pharmacies']

    @admin.action(description='Verify selected pharmacies')
    def verify_pharmacies(self, request, queryset):
        for pharmacy in queryset:
            pharmacy.is_verified      = True
            pharmacy.user.is_verified = True
            pharmacy.save(update_fields=['is_verified'])
            pharmacy.user.save(update_fields=['is_verified'])
        self.message_user(request, f'{queryset.count()} pharmacy(s) verified.')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display  = ['name', 'generic_name', 'dosage_form', 'strength', 'requires_prescription']
    list_filter   = ['dosage_form', 'requires_prescription', 'category']
    search_fields = ['name', 'generic_name', 'brand_name', 'barcode']


@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display  = ['pharmacy', 'medicine', 'stock_quantity', 'price', 'is_available']
    list_filter   = ['is_available']
    search_fields = ['pharmacy__name', 'medicine__name']
