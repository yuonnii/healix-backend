from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import User, PatientProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterPatientSerializer,
    RegisterDoctorSerializer,
    RegisterPharmacySerializer,
    UserProfileSerializer,
    PatientProfileSerializer,
    ChangePasswordSerializer,
)


def ok(data=None, message='Success', status_code=status.HTTP_200_OK):
    return Response({'success': True, 'message': message, 'data': data}, status=status_code)


# ─── Registration ──────────────────────────────────────────────────────────────

@extend_schema(tags=['Auth'])
class PatientRegisterView(generics.CreateAPIView):
    """Register a new patient account. Returns JWT tokens immediately."""
    serializer_class   = RegisterPatientSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': 'Patient account created successfully.',
            'data': {
                'user':   UserProfileSerializer(user, context={'request': request}).data,
                'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)},
            },
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'])
class DoctorRegisterView(generics.CreateAPIView):
    """Register a new doctor account. Account is active but flagged as unverified until admin approves."""
    serializer_class   = RegisterDoctorSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': 'Doctor account created. Pending license verification by admin.',
            'data': {
                'user':   UserProfileSerializer(user, context={'request': request}).data,
                'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)},
            },
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'])
class PharmacyRegisterView(generics.CreateAPIView):
    """Register a new pharmacy account."""
    serializer_class   = RegisterPharmacySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': 'Pharmacy account created. Pending verification by admin.',
            'data': {
                'user':   UserProfileSerializer(user, context={'request': request}).data,
                'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)},
            },
        }, status=status.HTTP_201_CREATED)


# ─── Auth ──────────────────────────────────────────────────────────────────────

@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView):
    """Login with email + password. Returns access token, refresh token, and user info."""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response({'success': True, 'message': 'Login successful.', 'data': response.data})
        return response


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    """Blacklist the refresh token to invalidate the session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'success': False, 'error': {'message': 'refresh_token is required.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response(
                {'success': False, 'error': {'message': 'Invalid or already-expired token.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return ok(message='Logged out successfully.')


@extend_schema(tags=['Auth'])
class TokenRefreshView(BaseTokenRefreshView):
    """Exchange a refresh token for a new access token."""
    pass


@extend_schema(tags=['Auth'])
class ChangePasswordView(APIView):
    """Change the authenticated user's password."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return ok(message='Password changed successfully.')


# ─── Profile ───────────────────────────────────────────────────────────────────

@extend_schema(tags=['Auth'])
class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the currently authenticated user's account info."""
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(data=serializer.data, message='Profile updated.')


@extend_schema(tags=['Patients'])
class PatientProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the patient's medical profile (blood type, allergies, etc.)."""
    serializer_class   = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = PatientProfile.objects.get_or_create(user=self.request.user)
        return profile

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(data=serializer.data, message='Medical profile updated.')
