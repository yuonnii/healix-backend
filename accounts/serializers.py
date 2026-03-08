from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import User, PatientProfile
from datetime import date
import re


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user info to JWT payload and login response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role']      = user.role
        token['full_name'] = user.get_full_name()
        token['email']     = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id':              user.id,
            'email':           user.email,
            'full_name':       user.get_full_name(),
            'role':            user.role,
            'is_verified':     user.is_verified,
            'profile_picture': (
                self.context['request'].build_absolute_uri(user.profile_picture.url)
                if user.profile_picture else None
            ),
        }
        return data


class RegisterPatientSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    date_of_birth    = serializers.DateField(required=False)
    gender           = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        required=False,
    )
    blood_type = serializers.ChoiceField(
        choices=PatientProfile.BloodType.choices,
        required=False,
    )
    
    def validate_date_of_birth(self, value):
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("You must be atleast 18 years old.")
            if value > today:
                raise serializers.ValidationError("Invalid date of birth.")
            return value

    class Meta:
        model  = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm',
            'date_of_birth', 'gender', 'blood_type',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def validate_phone_number(self, value):
        if value and not re.match(r'^(?:\+213|0)(5|6|7)\d{8}$', value):
            raise serializers.ValidationError("Please enter a valid Algerian phone number.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        profile_keys = ['date_of_birth', 'gender', 'blood_type']
        profile_data = {k: validated_data.pop(k) for k in profile_keys if k in validated_data}
        user = User.objects.create_user(role=User.Role.PATIENT, **validated_data)
        PatientProfile.objects.create(user=user, **profile_data)
        return user


class RegisterDoctorSerializer(serializers.ModelSerializer):
    password            = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm    = serializers.CharField(write_only=True)
    specialty           = serializers.CharField(max_length=100)
    license_number      = serializers.CharField(max_length=50)
    years_of_experience = serializers.IntegerField(min_value=0, required=False)
    clinic_name         = serializers.CharField(max_length=200, required=False, allow_blank=True)
    clinic_address      = serializers.CharField(required=False, allow_blank=True)
    consultation_fee    = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    bio                 = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm',
            'specialty', 'license_number', 'years_of_experience',
            'clinic_name', 'clinic_address', 'consultation_fee', 'bio',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from doctors.models import DoctorProfile
        profile_keys = [
            'specialty', 'license_number', 'years_of_experience',
            'clinic_name', 'clinic_address', 'consultation_fee', 'bio',
        ]
        profile_data = {k: validated_data.pop(k) for k in profile_keys if k in validated_data}
        user = User.objects.create_user(role=User.Role.DOCTOR, **validated_data)
        DoctorProfile.objects.create(user=user, **profile_data)
        return user


class RegisterPharmacySerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    pharmacy_name    = serializers.CharField(max_length=200)
    license_number   = serializers.CharField(max_length=50)
    address          = serializers.CharField()
    phone_number_pharmacy = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model  = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm',
            'pharmacy_name', 'license_number', 'address', 'phone_number_pharmacy',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from pharmacies.models import Pharmacy
        pharmacy_name    = validated_data.pop('pharmacy_name')
        license_number   = validated_data.pop('license_number')
        address          = validated_data.pop('address')
        phone_number_pharmacy = validated_data.pop('phone_number_pharmacy', '')
        user = User.objects.create_user(role=User.Role.PHARMACY, **validated_data)
        Pharmacy.objects.create(
            user=user,
            name=pharmacy_name,
            license_number=license_number,
            address=address,
            phone_number=phone_number_pharmacy,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name            = serializers.SerializerMethodField()
    profile_picture_url  = serializers.SerializerMethodField()

    class Meta:
        model        = User
        fields       = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'profile_picture', 'profile_picture_url',
            'is_verified', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and request:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    age  = serializers.ReadOnlyField()

    class Meta:
        model  = PatientProfile
        fields = [
            'id', 'user', 'date_of_birth', 'age', 'gender', 'blood_type',
            'allergies', 'chronic_conditions',
            'emergency_contact_name', 'emergency_contact_phone',
            'address', 'latitude', 'longitude',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(required=True)
    new_password         = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})
        return attrs
