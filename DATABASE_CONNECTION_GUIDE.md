# Database Connection Setup Guide

## ✅ Quick Test

Run this command to test your database connection:
```bash
python test_db_connection.py
```

If this test passes, your database connection is working!

## Common Issues and Solutions

### 1. Database Connection Not Available (🔴 DB Disconnected)

**Symptoms:**
- Status shows "🔴 DB Disconnected" in WO Inspection page
- Checklist items don't load

**Solutions:**

#### A. Check Internet Connection
- Make sure you have an active internet connection
- Supabase requires internet to work

#### B. Verify config.py
Open `config.py` and make sure it contains:
```python
SUPABASE_URL = "https://tpurxqpicyoolvrupxwa.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_wQxfua8Di6OkZGQhU3CsLw_XcsXmVXo"
```

#### C. Check Required Packages
Run:
```bash
pip install supabase bcrypt
```

#### D. Run Test Script
```bash
python test_db_connection.py
```
This will tell you exactly what's wrong.

### 2. Database Connected but Checklist is Blank

**Symptoms:**
- Status shows "🟢 DB Connected"
- But checklist shows "No items found"

**Solutions:**

#### A. Run SQL Scripts in Supabase
1. Go to: https://supabase.com/dashboard/project/tpurxqpicyoolvrupxwa/sql
2. Run `wo_inspection_checklist_setup.sql` first
3. Then run `add_initial_secure_checklist.sql`

#### B. Refresh the Page
Click the "🔄 Refresh from DB" button on the WO Inspection page

#### C. Check Console Output
When you open the Initial Secure checklist, check the console/terminal for debug messages. It should show:
```
[DEBUG] ✅ Successfully loaded 22 checklist items for 'Initial Secure'
```

## Verification Steps

1. **Test Database Connection:**
   ```bash
   python test_db_connection.py
   ```
   Should show: ✅ All tests completed!

2. **Check Console When Opening WO Inspection:**
   - Run your app
   - Open WO Inspection section
   - Check terminal/console for database initialization messages
   - Should see: `✅ Database connection verified successfully`

3. **Verify Data in Supabase:**
   - Go to Supabase Dashboard
   - Navigate to Table Editor
   - Check `wo_inspection_checklist_items` table
   - Should see rows for "Initial Secure" and "Winterization"

## Still Having Issues?

1. Check the console output when you open the app
2. Look for error messages starting with `[WOInspectionModule.__init__]`
3. Share the error message for further help

