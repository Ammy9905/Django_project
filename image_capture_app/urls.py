from django.urls import path
from .views import CapturedImageListCreateView

urlpatterns = [
    path('images/', CapturedImageListCreateView.as_view(), name='image-list-create'),
]
