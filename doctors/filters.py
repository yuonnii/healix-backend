import django_filters
from .models import DoctorProfile


class DoctorFilter(django_filters.FilterSet):
    specialty      = django_filters.CharFilter(field_name='specialty', lookup_expr='icontains')
    min_rating     = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_fee        = django_filters.NumberFilter(field_name='consultation_fee', lookup_expr='lte')
    min_fee        = django_filters.NumberFilter(field_name='consultation_fee', lookup_expr='gte')
    min_experience = django_filters.NumberFilter(field_name='years_of_experience', lookup_expr='gte')
    available      = django_filters.BooleanFilter(field_name='is_available_for_booking')
    verified       = django_filters.BooleanFilter(field_name='is_verified')
    language       = django_filters.CharFilter(field_name='languages', lookup_expr='icontains')

    class Meta:
        model  = DoctorProfile
        fields = [
            'specialty', 'min_rating', 'max_fee', 'min_fee',
            'min_experience', 'available', 'verified', 'language',
        ]
