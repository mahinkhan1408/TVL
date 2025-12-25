# Creating Users in Supabase

This guide explains how to create users (Aaron and Kent) in your Supabase database.

## Step 1: Run the SQL Script

1. Open your **Supabase Dashboard**
2. Go to **SQL Editor**
3. Copy and paste the contents of `create_users.sql`
4. Click **Run** to execute the script

This will create two users:
- **Username:** Aaron
- **Username:** Kent  
- **Password for both:** abcde

## Step 2: Verify Users Were Created

After running the script, you should see output showing the created users with their IDs. You can also verify by running:

```sql
SELECT id, username, created_at FROM users WHERE username IN ('Aaron', 'Kent');
```

## Important Notes

- The password is hashed using bcrypt before being stored
- The SQL script uses `ON CONFLICT` to update existing users if they already exist
- Users are created with the current timestamp
- You can update these users manually in the Supabase dashboard if needed

## Troubleshooting Deletion Issues

If deletion is not working in Supabase, check:

1. **RLS Policies**: Make sure Row Level Security policies allow deletion
   - Check the `supabase_schema.sql` file for RLS policies
   - The delete policy should be: `USING (true)` to allow all authenticated users

2. **User ID Matching**: Make sure the `user_id` in your application matches the user ID in Supabase
   - Check the console output when deleting - it should show the user_id being used

3. **Database Connection**: Verify the database connection is working
   - Run `test_db_connection.py` to verify

4. **Check Error Messages**: The improved `delete_bid` function now includes better error logging
   - Check the console/terminal for detailed error messages when deletion fails

