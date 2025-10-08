from django.core.management.base import BaseCommand
from SRAS_App.models import Violation, Camera
from django.utils import timezone
import random
import os

class Command(BaseCommand):
    help = 'Creates test violations with pending_verification status for testing auto-refresh'

    def add_arguments(self, parser):
        parser.add_argument('num_violations', type=int, default=3, nargs='?',
                           help='The number of pending violations to create')

    def handle(self, *args, **options):
        num_violations = options['num_violations']
        cameras = Camera.objects.all()

        if not cameras.exists():
            self.stdout.write(self.style.ERROR('No cameras found. Please create some cameras first.'))
            return

        # Create a dummy image for violations (1x1 pixel JPEG)
        dummy_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'

        created_count = 0
        for i in range(num_violations):
            plate_number = f"TEST{random.randint(100, 999)}"
            camera = random.choice(cameras)
            
            violation = Violation.objects.create(
                camera=camera,
                plate_number=plate_number,
                image=dummy_image,
                status='pending_verification',
                timestamp=timezone.now() - timezone.timedelta(minutes=random.randint(1, 60))
            )
            created_count += 1
            self.stdout.write(f'Created violation: {violation}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} pending violations for testing auto-refresh!')
        )
        self.stdout.write(
            self.style.WARNING('Now test the auto-refresh functionality:')
        )
        self.stdout.write('1. Open the Android app and go to Pending Verifications')
        self.stdout.write('2. Open the admin violation list in your browser')
        self.stdout.write('3. Both should auto-refresh every 30 seconds')
        self.stdout.write('4. Approve/reject violations in Android app to see them move to admin list')