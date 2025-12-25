#!/usr/bin/env python3
"""
Test database connection script
This will verify if Supabase connection is working
"""

print("="*60)
print("Database Connection Test")
print("="*60)

try:
    print("\n1. Checking config.py...")
    from config import SUPABASE_URL, SUPABASE_ANON_KEY
    print(f"   ✅ Config imported successfully")
    print(f"   URL: {SUPABASE_URL}")
    print(f"   API Key (first 20 chars): {SUPABASE_ANON_KEY[:20]}...")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("\n   ❌ ERROR: SUPABASE_URL or SUPABASE_ANON_KEY is missing!")
        print("   Please check your config.py file")
        exit(1)
    
    print("\n2. Testing Supabase client creation...")
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"   ✅ Supabase client created: {client}")
    
    print("\n3. Testing database connection with a simple query...")
    try:
        result = client.table('users').select('id').limit(1).execute()
        print(f"   ✅ Connection successful! Query executed.")
        print(f"   Result: {result.data if result.data else 'No data (table might be empty)'}")
    except Exception as query_e:
        print(f"   ⚠️  Query failed (might be RLS or table issue): {query_e}")
        print(f"   But the connection itself might be working.")
    
    print("\n4. Testing OnlineDatabaseManager initialization...")
    from database_online import OnlineDatabaseManager
    db = OnlineDatabaseManager()
    print(f"   ✅ OnlineDatabaseManager created: {db}")
    print(f"   Has supabase client: {hasattr(db, 'supabase')}")
    if hasattr(db, 'supabase'):
        print(f"   Supabase client: {db.supabase}")
    
    print("\n5. Testing checklist items query...")
    try:
        items = db.get_checklist_items("Initial Secure")
        print(f"   ✅ Query executed successfully!")
        print(f"   Found {len(items)} items for 'Initial Secure'")
        if items:
            print(f"   First item: {items[0][:50]}...")
    except Exception as checklist_e:
        print(f"   ❌ Checklist query failed: {checklist_e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("   Make sure you have installed: pip install supabase")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    print("TROUBLESHOOTING:")
    print("="*60)
    print("1. Check your internet connection")
    print("2. Verify config.py has correct SUPABASE_URL and SUPABASE_ANON_KEY")
    print("3. Make sure Supabase project is active")
    print("4. Check if you have the required packages: pip install supabase")
    print("="*60)

