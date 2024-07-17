from django.shortcuts import render
from rest_framework import generics
from .models import CapturedImage
from .serializers import CapturedImageSerializer

class CapturedImageListCreateView(generics.ListCreateAPIView):
    queryset = CapturedImage.objects.all()
    serializer_class = CapturedImageSerializer

