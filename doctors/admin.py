from django.contrib import admin
from .models import DoctorProfile, DoctorAvailability, DoctorReview, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'icon']
    search_fields = ['name']


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'specialty', 'clinic_name', 'is_verified', 'average_rating']
    list_filter   = ['is_verified', 'is_available_for_booking']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'license_number']
    actions       = ['verify_doctors']

    @admin.action(description='Verify selected doctors')
    def verify_doctors(self, request, queryset):
        for doctor in queryset:
            doctor.is_verified      = True
            doctor.user.is_verified = True
            doctor.save(update_fields=['is_verified'])
            doctor.user.save(update_fields=['is_verified'])
        self.message_user(request, f'{queryset.count()} doctor(s) verified.')


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter  = ['day_of_week', 'is_active']


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display  = ['doctor', 'patient', 'rating', 'created_at']
    list_filter   = ['rating']
