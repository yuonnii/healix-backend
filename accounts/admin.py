from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'date_joined']
    list_filter    = ['role', 'is_active', 'is_verified', 'is_staff']
    search_fields  = ['email', 'first_name', 'last_name']
    ordering       = ['-date_joined']
    fieldsets = (
        (None,          {'fields': ('email', 'password')}),
        ('Personal',    {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')}),
        ('Role',        {'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser')}),
        ('Dates',       {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'date_of_birth', 'gender', 'blood_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
