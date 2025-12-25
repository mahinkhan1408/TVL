# Test script to diagnose checklist query issues
# Run this from command line: python test_checklist_query.py

from database_online import OnlineDatabaseManager

print("=" * 60)
print("Testing Checklist Query")
print("=" * 60)

try:
    db = OnlineDatabaseManager()
    print("✅ Database connection successful")
    
    # Test 1: Check if we can query any data
    print("\n[Test 1] Checking if table is accessible...")
    try:
        test_result = db.supabase.table('wo_inspection_checklist_items')\
            .select('inspection_type')\
            .limit(5)\
            .execute()
        
        if test_result.data:
            print(f"✅ Table is accessible. Found {len(test_result.data)} sample rows")
            print(f"   Sample inspection types: {[item['inspection_type'] for item in test_result.data[:3]]}")
        else:
            print("⚠️ Table accessible but no data returned")
    except Exception as e:
        print(f"❌ Cannot access table: {e}")
        exit(1)
    
    # Test 2: Get all inspection types
    print("\n[Test 2] Getting all inspection types...")
    try:
        all_types = db.supabase.table('wo_inspection_checklist_items')\
            .select('inspection_type')\
            .execute()
        
        if all_types.data:
            unique_types = set(item['inspection_type'] for item in all_types.data)
            print(f"✅ Found {len(unique_types)} unique inspection types:")
            for t in sorted(unique_types):
                count = sum(1 for item in all_types.data if item['inspection_type'] == t)
                print(f"   - '{t}': {count} items")
        else:
            print("⚠️ No inspection types found")
    except Exception as e:
        print(f"❌ Error getting types: {e}")
    
    # Test 3: Query for Initial Secure
    print("\n[Test 3] Querying for 'Initial Secure'...")
    try:
        secure_items = db.get_checklist_items("Initial Secure")
        if secure_items:
            print(f"✅ Successfully loaded {len(secure_items)} items for 'Initial Secure'")
            print(f"   First item: {secure_items[0][:70]}...")
            print(f"   Last item: {secure_items[-1][:70]}...")
        else:
            print("❌ No items returned for 'Initial Secure'")
            
            # Try direct query
            print("\n[Test 4] Trying direct query...")
            direct_result = db.supabase.table('wo_inspection_checklist_items')\
                .select('*')\
                .eq('inspection_type', 'Initial Secure')\
                .execute()
            
            if direct_result.data:
                print(f"⚠️ Direct query found {len(direct_result.data)} rows!")
                print(f"   This means RLS might be blocking the .get_checklist_items() method")
                print(f"   First row sample: {direct_result.data[0]}")
            else:
                print("❌ Direct query also returned no rows")
    except Exception as e:
        print(f"❌ Error querying Initial Secure: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()

