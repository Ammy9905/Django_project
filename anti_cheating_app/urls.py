# anti_cheating_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('start_recording/', views.start_recording, name='start_recording'),
    path('stop_recording/', views.stop_recording, name='stop_recording'),
    path('get_recordings/', views.get_recordings, name='get_recordings'),
]

