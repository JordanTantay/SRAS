from rest_framework import serializers
from .models import Violation, Camera, OriginalViolation

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name', 'stream_url']


class ViolationSerializer(serializers.ModelSerializer):
    camera = CameraSerializer(read_only=True)
    
    class Meta:
        model = Violation
        fields = ['id', 'camera', 'timestamp', 'plate_number', 'sms_sent', 'rider_hash', 
                 'status', 'verified_by', 'verified_at', 'verification_notes']

class ViolationVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Violation
        fields = ['status', 'verification_notes']

class OriginalViolationSerializer(serializers.ModelSerializer):
    camera = CameraSerializer(read_only=True)
    
    class Meta:
        model = OriginalViolation
        fields = ['id', 'camera', 'timestamp', 'plate_number', 'sms_sent', 'rider_hash', 
                 'verified_by', 'verified_at', 'verification_notes', 'original_violation']