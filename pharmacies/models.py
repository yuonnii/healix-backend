from django.db import models
from django.utils import timezone as tz


class Pharmacy(models.Model):
    # String ref — avoids importing accounts directly
    user           = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='pharmacy_profile')
    name           = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    address        = models.TextField()
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone_number   = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    opening_time   = models.TimeField(null=True, blank=True)
    closing_time   = models.TimeField(null=True, blank=True)
    is_open_24h    = models.BooleanField(default=False)
    is_verified    = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table           = 'pharmacies'
        verbose_name_plural = 'Pharmacies'
        ordering            = ['name']

    def __str__(self):
        return self.name

    @property
    def is_open_now(self):
        if self.is_open_24h:
            return True
        now = tz.localtime().time()
        if self.opening_time and self.closing_time:
            return self.opening_time <= now <= self.closing_time
        return False


class Medicine(models.Model):
    class DosageForm(models.TextChoices):
        TABLET    = 'tablet',    'Tablet'
        CAPSULE   = 'capsule',   'Capsule'
        SYRUP     = 'syrup',     'Syrup'
        INJECTION = 'injection', 'Injection'
        CREAM     = 'cream',     'Cream'
        DROPS     = 'drops',     'Drops'
        INHALER   = 'inhaler',   'Inhaler'
        PATCH     = 'patch',     'Patch'
        OTHER     = 'other',     'Other'

    name                   = models.CharField(max_length=200)
    generic_name           = models.CharField(max_length=200, blank=True)
    brand_name             = models.CharField(max_length=200, blank=True)
    manufacturer           = models.CharField(max_length=200, blank=True)
    dosage_form            = models.CharField(max_length=20, choices=DosageForm.choices, default=DosageForm.TABLET)
    strength               = models.CharField(max_length=100, blank=True)
    description            = models.TextField(blank=True)
    requires_prescription  = models.BooleanField(default=False)
    category               = models.CharField(max_length=100, blank=True)
    barcode                = models.CharField(max_length=100, blank=True, unique=True, null=True)
    created_at             = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medicines'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} {self.strength} ({self.get_dosage_form_display()})'


class PharmacyInventory(models.Model):
    pharmacy       = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='inventory')
    medicine       = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='pharmacy_stocks')
    stock_quantity = models.PositiveIntegerField(default=0)
    price          = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date    = models.DateField(null=True, blank=True)
    is_available   = models.BooleanField(default=True)
    last_updated   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table       = 'pharmacy_inventory'
        unique_together = ['pharmacy', 'medicine']
        ordering        = ['medicine__name']

    def __str__(self):
        return f'{self.pharmacy.name} — {self.medicine.name} x{self.stock_quantity}'

    @property
    def in_stock(self):
        return self.is_available and self.stock_quantity > 0
