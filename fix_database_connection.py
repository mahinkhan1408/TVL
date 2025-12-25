#!/usr/bin/env python3
"""
Fix Database Connection - Install dependencies and verify setup
Run this script to ensure all required packages are installed
"""

import sys
import subprocess

def check_and_install_packages():
    """Check and install required packages"""
    required_packages = {
        'supabase': 'supabase>=2.0.0',
        'bcrypt': 'bcrypt>=4.0.0',
    }
    
    print("="*60)
    print("Database Connection Fix")
    print("="*60)
    print(f"\nPython executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"\n{'='*60}\n")
    
    missing_packages = []
    
    for package_name, package_spec in required_packages.items():
        print(f"Checking {package_name}...", end=" ")
        try:
            __import__(package_name)
            print("✅ Installed")
        except ImportError:
            print(f"❌ Missing")
            missing_packages.append(package_spec)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages detected: {', '.join([pkg.split('>=')[0] for pkg in missing_packages])}")
        print("\nInstalling missing packages...")
        
        for package in missing_packages:
            print(f"\nInstalling {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--upgrade"])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    else:
        print("\n✅ All required packages are installed!")
    
    # Test database connection
    print("\n" + "="*60)
    print("Testing database connection...")
    print("="*60 + "\n")
    
    try:
        from database_online import OnlineDatabaseManager
        db = OnlineDatabaseManager()
        print("✅ Database connection successful!")
        
        # Test checklist query
        items = db.get_checklist_items("Initial Secure")
        print(f"✅ Retrieved {len(items)} items for 'Initial Secure'")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_and_install_packages()
    
    print("\n" + "="*60)
    if success:
        print("✅ Setup complete! You can now run your app.")
        print("\nIf the app still shows 'DB Disconnected':")
        print("1. Close the app completely")
        print("2. Restart the app")
        print("3. The database should now connect successfully")
    else:
        print("❌ Setup incomplete. Please check the errors above.")
    print("="*60)

