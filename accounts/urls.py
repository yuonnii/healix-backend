from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('auth/register/patient/',  views.PatientRegisterView.as_view(),  name='register-patient'),
    path('auth/register/doctor/',   views.DoctorRegisterView.as_view(),   name='register-doctor'),
    path('auth/register/pharmacy/', views.PharmacyRegisterView.as_view(), name='register-pharmacy'),

    # Auth
    path('auth/login/',          views.LoginView.as_view(),         name='login'),
    path('auth/logout/',         views.LogoutView.as_view(),        name='logout'),
    path('auth/token/refresh/',  views.TokenRefreshView.as_view(),  name='token-refresh'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # Current user
    path('auth/me/',            views.MeView.as_view(),           name='me'),
    path('patients/profile/',   views.PatientProfileView.as_view(), name='patient-profile'),
]
