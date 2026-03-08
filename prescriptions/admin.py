from django.contrib import admin
from .models import Prescription, PrescriptionItem, ScannedPrescription


class PrescriptionItemInline(admin.TabularInline):
    model  = PrescriptionItem
    extra  = 1
    fields = ['medicine', 'medicine_name_raw', 'dosage', 'frequency', 'duration', 'quantity', 'is_dispensed']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display   = ['id', 'patient', 'doctor', 'status', 'issue_date', 'expiry_date']
    list_filter    = ['status']
    search_fields  = ['patient__user__email', 'doctor__user__email']
    inlines        = [PrescriptionItemInline]


@admin.register(ScannedPrescription)
class ScannedPrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'processed', 'created_at']
    list_filter  = ['processed']
