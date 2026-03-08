from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    # Public
    path('doctors/',                            views.DoctorListView.as_view(),               name='list'),
    path('doctors/specialties/',                views.SpecialtyListView.as_view(),             name='specialties'),
    path('doctors/<int:pk>/',                   views.DoctorDetailView.as_view(),              name='detail'),
    path('doctors/<int:pk>/slots/',             views.DoctorAvailableSlotsView.as_view(),      name='slots'),
    path('doctors/<int:pk>/reviews/',           views.DoctorReviewListView.as_view(),          name='reviews'),
    path('doctors/<int:pk>/reviews/add/',       views.CreateReviewView.as_view(),              name='add-review'),

    # Doctor (authenticated)
    path('doctors/me/profile/',                 views.MyDoctorProfileView.as_view(),           name='my-profile'),
    path('doctors/me/availability/',            views.DoctorAvailabilityListCreateView.as_view(), name='my-availability'),
    path('doctors/me/availability/<int:pk>/',   views.DoctorAvailabilityDetailView.as_view(),  name='availability-detail'),
]
