from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import date
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

algerian_phone_validator = RegexValidator(
    regex=r'^(?:\+213|0)(5|6|7)\d{8}$',
    message="Enter a valid Algerian phone number."
)

def validate_date_of_birth(self, value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 18:
        raise ValueError("You must be at least 18 years old.")

    return value

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PATIENT  = 'patient',  'Patient'
        DOCTOR   = 'doctor',   'Doctor'
        PHARMACY = 'pharmacy', 'Pharmacy'
        ADMIN    = 'admin',    'Admin'

    email           = models.EmailField(unique=True)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    phone_number    = models.CharField(max_length=20, blank=True, validators=[algerian_phone_validator])
    role            = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active       = models.BooleanField(default=True)
    is_verified     = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    date_joined     = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table     = 'users'
        verbose_name = 'User'

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class PatientProfile(models.Model):
    class BloodType(models.TextChoices):
        A_POS   = 'A+',      'A+'
        A_NEG   = 'A-',      'A-'
        B_POS   = 'B+',      'B+'
        B_NEG   = 'B-',      'B-'
        AB_POS  = 'AB+',     'AB+'
        AB_NEG  = 'AB-',     'AB-'
        O_POS   = 'O+',      'O+'
        O_NEG   = 'O-',      'O-'
        UNKNOWN = 'unknown', 'Unknown'

    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female')]

    user                   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth          = models.DateField(null=True, blank=True)
    gender                 = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_type             = models.CharField(max_length=10, choices=BloodType.choices, default=BloodType.UNKNOWN)
    allergies              = models.TextField(blank=True)
    chronic_conditions     = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone= models.CharField(max_length=20, blank=True)
    address                = models.TextField(blank=True)
    latitude               = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude              = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_profiles'

    def __str__(self):
        return f'Patient: {self.user.get_full_name()}'

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
