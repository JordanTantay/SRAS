#!/usr/bin/env python3
"""
Setup script for SRAS MySQL Database
This script helps install required dependencies and set up the MySQL database.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 SRAS MySQL Database Setup")
    print("=" * 40)
    
    # Step 1: Install mysqlclient
    print("\n📦 Step 1: Installing MySQL client...")
    if not run_command("pip install mysqlclient", "Installing mysqlclient"):
        print("⚠️  If mysqlclient installation fails, try:")
        print("   pip install pymysql")
        print("   Then add this to your settings.py:")
        print("   import pymysql")
        print("   pymysql.install_as_MySQLdb()")
        return False
    
    # Step 2: Test Django connection
    print("\n🔗 Step 2: Testing Django database connection...")
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SRAS_Project.settings')
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Please ensure:")
        print("   1. MySQL server is running")
        print("   2. Database 'sras_django' exists")
        print("   3. User 'root' has access")
        print("   4. MySQL credentials are correct in settings.py")
        return False
    
    # Step 3: Run migrations
    print("\n🗄️  Step 3: Running database migrations...")
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Applying migrations"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Start the Django server: python manage.py runserver")
    print("   2. Start the stream server: python stream_mjpeg.py")
    print("   3. Visit: http://localhost:8000/monitor/")
    print("   4. Violations will be automatically saved to MySQL database")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 