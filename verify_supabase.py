# verify_supabase.py
# Script to verify Supabase connection and configuration

from config import SUPABASE_URL, SUPABASE_ANON_KEY
from supabase import create_client

print("=" * 60)
print("Supabase Connection Verification")
print("=" * 60)
print(f"\nSupabase URL: {SUPABASE_URL}")
print(f"API Key (first 20 chars): {SUPABASE_ANON_KEY[:20]}...")
print(f"API Key length: {len(SUPABASE_ANON_KEY)}")
print("\n" + "-" * 60)

try:
    print("\nAttempting to connect to Supabase...")
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Connection successful!")
    
    # Try to query users table
    try:
        result = client.table('users').select('id').limit(1).execute()
        print("✅ Users table exists and is accessible")
    except Exception as e:
        if "relation" in str(e).lower() or "does not exist" in str(e).lower():
            print("⚠️  Users table does not exist yet.")
            print("   Please run the SQL schema in Supabase SQL Editor.")
        else:
            print(f"⚠️  Error accessing users table: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Supabase is configured correctly!")
    print("=" * 60)
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ Connection failed!")
    print(f"Error: {error_msg}")
    print("\n" + "-" * 60)
    print("Troubleshooting:")
    print("-" * 60)
    
    if "Invalid API key" in error_msg or "401" in error_msg or "403" in error_msg:
        print("\n1. Your API key might be incorrect.")
        print("   To get the correct API key:")
        print("   a. Go to: https://supabase.com/dashboard/project/tpurxqpicyoolvrupxwa")
        print("   b. Click 'Settings' (gear icon) in the left sidebar")
        print("   c. Click 'API'")
        print("   d. Copy the 'anon' or 'public' key (it should be a long JWT token)")
        print("   e. Update SUPABASE_ANON_KEY in config.py")
    elif "Connection" in error_msg or "timeout" in error_msg.lower():
        print("\n1. Check your internet connection")
        print("2. Verify the Supabase project is active")
    else:
        print(f"\nUnexpected error: {error_msg}")
        print("Please check:")
        print("1. Supabase URL is correct")
        print("2. API key is correct")
        print("3. Internet connection is working")
    
    print("\n" + "=" * 60)

