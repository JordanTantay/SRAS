#!/usr/bin/env python3
"""
Test script for SRAS Database View functionality
This script helps test the violation database views and image display.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SRAS_Project.settings')
django.setup()

from SRAS_App.models import Violation, Camera
from django.utils import timezone

def test_database_views():
    """Test the database view functionality"""
    print("🧪 Testing SRAS Database Views")
    print("=" * 40)
    
    # Check if we have any violations
    total_violations = Violation.objects.count()
    print(f"📊 Total violations in database: {total_violations}")
    
    if total_violations == 0:
        print("⚠️  No violations found in database.")
        print("   Start the stream server to capture violations first.")
        return
    
    # Get recent violations
    recent_violations = Violation.objects.all().order_by('-timestamp')[:5]
    print(f"\n📋 Recent violations:")
    for violation in recent_violations:
        print(f"   ID: {violation.id}, Time: {violation.timestamp}, Plate: {violation.plate_number or 'UNKNOWN'}")
    
    # Test statistics
    today = timezone.now().date()
    today_violations = Violation.objects.filter(timestamp__date=today).count()
    print(f"\n📈 Today's violations: {today_violations}")
    
    # Test image access
    if recent_violations:
        first_violation = recent_violations[0]
        print(f"\n🖼️  Testing image access for violation {first_violation.id}:")
        print(f"   Image size: {len(first_violation.image)} bytes")
        print(f"   Image type: BLOB data")
    
    print("\n✅ Database view test completed!")
    print("\n🌐 Access your violation database at:")
    print("   http://localhost:8000/violations/")

def create_test_data():
    """Create some test violation data for demonstration"""
    print("\n🔧 Creating test violation data...")
    
    # Get or create camera
    camera, created = Camera.objects.get_or_create(
        name="Test Camera",
        defaults={'stream_url': "http://test-camera:8080/video"}
    )
    
    # Create test violations
    test_violations = [
        {
            'plate_number': 'ABC123',
            'rider_hash': 'test_hash_1',
            'timestamp': timezone.now() - timedelta(hours=1)
        },
        {
            'plate_number': 'XYZ789',
            'rider_hash': 'test_hash_2',
            'timestamp': timezone.now() - timedelta(hours=2)
        },
        {
            'plate_number': 'DEF456',
            'rider_hash': 'test_hash_3',
            'timestamp': timezone.now() - timedelta(hours=3)
        }
    ]
    
    # Create a simple test image (1x1 pixel JPEG)
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    created_count = 0
    for test_data in test_violations:
        violation, created = Violation.objects.get_or_create(
            rider_hash=test_data['rider_hash'],
            defaults={
                'camera': camera,
                'plate_number': test_data['plate_number'],
                'image': test_image_data,
                'timestamp': test_data['timestamp']
            }
        )
        if created:
            created_count += 1
            print(f"   ✅ Created test violation {violation.id}")
    
    print(f"📝 Created {created_count} test violations")
    print("   You can now test the database views!")

def main():
    """Main function"""
    print("🚀 SRAS Database View Test")
    print("=" * 40)
    
    try:
        # Test existing data
        test_database_views()
        
        # Ask if user wants to create test data
        response = input("\n❓ Do you want to create test violation data? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_test_data()
            test_database_views()
        
        print("\n🎉 Test completed!")
        print("\n📋 Next steps:")
        print("   1. Start Django server: python manage.py runserver")
        print("   2. Visit: http://localhost:8000/violations/")
        print("   3. Test search, filtering, and image viewing")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        print("   Make sure your database is properly configured.")

if __name__ == "__main__":
    main() 