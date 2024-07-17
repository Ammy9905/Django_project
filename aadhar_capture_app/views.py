from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CapturedImage
from .serializers import CapturedImageSerializer

class CapturedImageViewSet(viewsets.ModelViewSet):
    queryset = CapturedImage.objects.all()
    serializer_class = CapturedImageSerializer
    parser_classes = (MultiPartParser, FormParser)

