from rest_framework import serializers
from accounts.serializers import UserProfileSerializer
from .models import DoctorProfile, DoctorAvailability, DoctorReview, Specialty


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Specialty
        fields = ['id', 'name', 'icon', 'description']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model  = DoctorAvailability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time',
                  'slot_duration_minutes', 'max_patients', 'is_active']

    def validate(self, attrs):
        if attrs.get('start_time') and attrs.get('end_time'):
            if attrs['start_time'] >= attrs['end_time']:
                raise serializers.ValidationError('end_time must be after start_time.')
        return attrs


class DoctorReviewSerializer(serializers.ModelSerializer):
    patient_name    = serializers.SerializerMethodField()
    patient_picture = serializers.SerializerMethodField()

    class Meta:
        model  = DoctorReview
        fields = ['id', 'rating', 'comment', 'is_anonymous',
                  'patient_name', 'patient_picture', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_patient_name(self, obj):
        return 'Anonymous' if obj.is_anonymous else obj.patient.user.get_full_name()

    def get_patient_picture(self, obj):
        if obj.is_anonymous:
            return None
        request = self.context.get('request')
        if obj.patient.user.profile_picture and request:
            return request.build_absolute_uri(obj.patient.user.profile_picture.url)
        return None


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DoctorReview
        fields = ['rating', 'comment', 'is_anonymous', 'appointment']

    def validate_appointment(self, appointment):
        if appointment is None:
            return appointment
        patient = self.context['request'].user.patient_profile
        if appointment.patient != patient:
            raise serializers.ValidationError('This appointment does not belong to you.')
        if appointment.status != 'completed':
            raise serializers.ValidationError('You can only review after a completed appointment.')
        return appointment

    def validate(self, attrs):
        doctor  = self.context['doctor']
        patient = self.context['request'].user.patient_profile
        if DoctorReview.objects.filter(doctor=doctor, patient=patient).exists():
            raise serializers.ValidationError('You have already reviewed this doctor.')
        return attrs

    def create(self, validated_data):
        return DoctorReview.objects.create(
            doctor  = self.context['doctor'],
            patient = self.context['request'].user.patient_profile,
            **validated_data,
        )


class DoctorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for search results."""
    full_name       = serializers.CharField(source='user.get_full_name', read_only=True)
    profile_picture = serializers.SerializerMethodField()
    distance_km     = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model  = DoctorProfile
        fields = [
            'id', 'full_name', 'profile_picture', 'specialty',
            'clinic_name', 'clinic_address', 'consultation_fee',
            'average_rating', 'total_reviews',
            'is_available_for_booking', 'is_verified', 'distance_km',
        ]

    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.user.profile_picture and request:
            return request.build_absolute_uri(obj.user.profile_picture.url)
        return None


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Full doctor profile — used for detail view and my-profile."""
    user              = UserProfileSerializer(read_only=True)
    availability_slots = DoctorAvailabilitySerializer(many=True, read_only=True)
    recent_reviews    = serializers.SerializerMethodField()
    distance_km       = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model  = DoctorProfile
        fields = [
            'id', 'user', 'specialty', 'license_number', 'years_of_experience',
            'bio', 'education', 'languages',
            'clinic_name', 'clinic_address', 'latitude', 'longitude',
            'consultation_fee', 'is_available_for_booking', 'is_verified',
            'average_rating', 'total_reviews', 'total_appointments',
            'availability_slots', 'recent_reviews', 'distance_km', 'created_at',
        ]
        read_only_fields = [
            'id', 'is_verified', 'average_rating',
            'total_reviews', 'total_appointments', 'created_at',
        ]

    def get_recent_reviews(self, obj):
        return DoctorReviewSerializer(
            obj.reviews.all()[:5], many=True, context=self.context
        ).data


class UpdateDoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DoctorProfile
        fields = [
            'specialty', 'years_of_experience', 'bio', 'education', 'languages',
            'clinic_name', 'clinic_address', 'latitude', 'longitude',
            'consultation_fee', 'is_available_for_booking',
        ]
