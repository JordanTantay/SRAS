from django.core.management.base import BaseCommand
from django.utils import timezone
from SRAS_App.models import ViolationStaging, Camera
import os

class Command(BaseCommand):
    help = 'Create test staging violations for testing'

    def handle(self, *args, **options):
        # Get or create a test camera
        camera, created = Camera.objects.get_or_create(
            name="Test Camera",
            defaults={'stream_url': 'http://example.com/stream'}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created test camera'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing test camera'))

        # Create some test staging violations
        test_violations = [
            {
                'plate_number': 'ABC-123',
                'rider_hash': 'test_hash_1',
            },
            {
                'plate_number': 'XYZ-789',
                'rider_hash': 'test_hash_2',
            },
            {
                'plate_number': 'DEF-456',
                'rider_hash': 'test_hash_3',
            },
        ]

        for i, violation_data in enumerate(test_violations):
            # Create a dummy image (1x1 pixel JPEG)
            dummy_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
            
            staging_violation = ViolationStaging.objects.create(
                camera=camera,
                plate_number=violation_data['plate_number'],
                rider_hash=violation_data['rider_hash'],
                image=dummy_image,
                status='pending'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created staging violation {staging_violation.id}: {violation_data["plate_number"]}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(test_violations)} test staging violations')
        )
