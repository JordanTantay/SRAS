from django.core.management.base import BaseCommand
from SRAS_App.models import ViolationStaging

class Command(BaseCommand):
    help = 'List all staging violations'

    def handle(self, *args, **options):
        violations = ViolationStaging.objects.all().order_by('-timestamp')
        
        if not violations.exists():
            self.stdout.write(self.style.WARNING('No staging violations found'))
            return
        
        self.stdout.write(f"Found {violations.count()} staging violations:")
        self.stdout.write("-" * 80)
        
        for violation in violations:
            status_color = {
                'pending': self.style.WARNING,
                'approved': self.style.SUCCESS,
                'rejected': self.style.ERROR
            }.get(violation.status, self.style.NORMAL)
            
            self.stdout.write(
                f"ID: {violation.id} | "
                f"Plate: {violation.plate_number or 'Unknown'} | "
                f"Camera: {violation.camera.name} | "
                f"Status: {status_color(violation.get_status_display())} | "
                f"Time: {violation.timestamp}"
            )
