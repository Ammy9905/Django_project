# capture/serializers.py

from rest_framework import serializers
from .models import CapturedImage

class CapturedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedImage
        fields = ['id', 'image', 'timestamp']
