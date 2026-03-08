from django.contrib import admin
from .models import Appointment, Message


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display   = ['id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'queue_number']
    list_filter    = ['status', 'appointment_type', 'appointment_date']
    search_fields  = ['patient__user__email', 'doctor__user__email']
    ordering       = ['-appointment_date', '-appointment_time']
    date_hierarchy = 'appointment_date'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'appointment', 'is_read', 'created_at']
    list_filter  = ['is_read']
