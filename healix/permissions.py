from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPatient(BasePermission):
    message = 'This action requires a patient account.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'patient'
        )


class IsDoctor(BasePermission):
    message = 'This action requires a doctor account.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'doctor'
            and hasattr(request.user, 'doctor_profile')
        )


class IsPharmacy(BasePermission):
    message = 'This action requires a pharmacy account.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'pharmacy'
            and hasattr(request.user, 'pharmacy_profile')
        )


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: owner can write, everyone else read-only."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, 'user', None)
        return owner == request.user


class IsAppointmentParticipant(BasePermission):
    """Only the patient or doctor linked to an appointment may access it."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == 'patient':
            return obj.patient.user == user
        if user.role == 'doctor':
            return obj.doctor.user == user
        return user.is_staff
