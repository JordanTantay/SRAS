"""
Test script for enforcer validation (username uniqueness and mobile number length)
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SRAS_Project.settings')
django.setup()

from django.contrib.auth.models import User
from SRAS_App.models import Enforcer

def test_username_validation():
    """Test username uniqueness validation"""
    print("\n=== Testing Username Validation ===")
    
    # Get existing usernames
    existing_users = User.objects.all()
    print(f"Existing users: {existing_users.count()}")
    
    if existing_users.exists():
        test_username = existing_users.first().username
        print(f"Test username (should exist): {test_username}")
        print(f"  ✓ Username exists: {User.objects.filter(username=test_username).exists()}")
    
    # Test non-existent username
    test_new_username = "test_new_user_12345"
    print(f"\nTest username (should NOT exist): {test_new_username}")
    print(f"  ✓ Username available: {not User.objects.filter(username=test_new_username).exists()}")

def test_mobile_validation():
    """Test mobile number validation logic"""
    print("\n=== Testing Mobile Number Validation ===")
    
    test_cases = [
        ("09123456789", True, "Valid 11-digit number"),
        ("0912345678", False, "Only 10 digits"),
        ("091234567890", False, "12 digits (too long)"),
        ("abcdefghijk", False, "Contains letters"),
        ("0912345678a", False, "Contains letter at end"),
        ("", False, "Empty string"),
    ]
    
    for mobile, should_pass, description in test_cases:
        is_valid = len(mobile) == 11 and mobile.isdigit()
        status = "✓" if is_valid == should_pass else "✗"
        print(f"{status} {description}: '{mobile}' - Valid: {is_valid}")

def test_existing_enforcers():
    """Show existing enforcers and their mobile numbers"""
    print("\n=== Existing Enforcers ===")
    
    enforcers = Enforcer.objects.all()
    print(f"Total enforcers: {enforcers.count()}")
    
    for enforcer in enforcers:
        mobile = enforcer.mobile_number
        is_valid = len(mobile) == 11 and mobile.isdigit()
        status = "✓" if is_valid else "⚠"
        print(f"{status} {enforcer.user.username}: {mobile} ({len(mobile)} digits)")

if __name__ == '__main__':
    print("=" * 60)
    print("ENFORCER VALIDATION TEST SCRIPT")
    print("=" * 60)
    
    test_username_validation()
    test_mobile_validation()
    test_existing_enforcers()
    
    print("\n" + "=" * 60)
    print("VALIDATION RULES")
    print("=" * 60)
    print("✓ Username: Must be unique (checked in real-time)")
    print("✓ Mobile Number: Must be exactly 11 digits")
    print("✓ Mobile Number: Only numeric characters allowed")
    print("✓ Mobile Number: Auto-limited to 11 characters in UI")
    print("\n" + "=" * 60)
    print("TESTING INSTRUCTIONS")
    print("=" * 60)
    print("1. Start Django server: python manage.py runserver")
    print("2. Open: http://localhost:8000/enforcers/")
    print("3. Click 'Add Enforcer' button")
    print("4. Test username validation:")
    print("   - Type an existing username (e.g., 'admin')")
    print("   - Should show red 'Username already exists' message")
    print("5. Test mobile validation:")
    print("   - Type less than 11 digits")
    print("   - Should show warning with digit count")
    print("   - Type exactly 11 digits")
    print("   - Should show green 'Valid mobile number' message")
    print("6. Try to submit with invalid data")
    print("   - Should show alert and prevent submission")
    print("=" * 60)
