from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Camera(models.Model):
    name = models.CharField(max_length=100)
    stream_url = models.URLField()

    def __str__(self):
        return self.name


class Enforcer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15)
    assigned_camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Violation(models.Model):
    STATUS_CHOICES = [
        ('pending_verification', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    # parsed from your detector label (e.g., "plate_AB1234")
    plate_number = models.CharField(max_length=20, null=True, blank=True)

    # full annotated snapshot (JPG bytes)
    image = models.BinaryField()

    # NEW: cropped plate image (JPG bytes)
    plate_image = models.BinaryField(null=True, blank=True)

    # verification workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)

    # misc flags
    sms_sent = models.BooleanField(default=False)

    # duplicate control
    rider_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"Violation @ {self.timestamp} - {self.plate_number or 'UNKNOWN'} ({self.status})"

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['rider_hash']),
            models.Index(fields=['status']),
        ]


class OriginalViolation(models.Model):
    """
    Final database for approved violations from Android app verification.
    This model stores violations that have been verified and approved by users.
    """
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()  # Changed from auto_now_add to preserve original timestamp

    # parsed from your detector label (e.g., "plate_AB1234")
    plate_number = models.CharField(max_length=20, null=True, blank=True)

    # full annotated snapshot (JPG bytes)
    image = models.BinaryField()

    # cropped plate image (JPG bytes)
    plate_image = models.BinaryField(null=True, blank=True)

    # verification details
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)

    # reference to original violation
    original_violation = models.ForeignKey(Violation, on_delete=models.SET_NULL, null=True, blank=True, 
                                         help_text="Reference to the original violation that was approved")

    # misc flags
    sms_sent = models.BooleanField(default=False)

    # duplicate control
    rider_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"Original Violation @ {self.timestamp} - {self.plate_number or 'UNKNOWN'}"

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['rider_hash']),
            models.Index(fields=['verified_at']),
        ]
