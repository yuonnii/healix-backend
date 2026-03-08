from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Patient
    path('appointments/book/',          views.BookAppointmentView.as_view(),        name='book'),
    path('appointments/my/',            views.PatientAppointmentListView.as_view(), name='my-list'),
    path('appointments/<int:pk>/',      views.AppointmentDetailView.as_view(),      name='detail'),
    path('appointments/<int:pk>/cancel/', views.CancelAppointmentView.as_view(),    name='cancel'),
    path('appointments/<int:pk>/queue/', views.QueueStatusView.as_view(),           name='queue'),
    path('appointments/<int:pk>/messages/', views.AppointmentMessagesView.as_view(), name='messages'),

    # Doctor
    path('appointments/doctor/list/',      views.DoctorAppointmentListView.as_view(), name='doctor-list'),
    path('appointments/doctor/queue/',     views.TodayQueueView.as_view(),            name='today-queue'),
    path('appointments/doctor/dashboard/', views.DoctorDashboardView.as_view(),       name='dashboard'),
    path('appointments/<int:pk>/update/',  views.DoctorUpdateAppointmentView.as_view(), name='doctor-update'),
]
