# Supabase Integration Setup Instructions

## Step 1: Install Required Packages

Run the following command to install all required packages:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install supabase bcrypt python-docx Pillow requests
```

## Step 2: Set Up Supabase Database

1. Go to your Supabase project dashboard: https://supabase.com/dashboard/project/tpurxqpicyoolvrupxwa

2. Navigate to **SQL Editor** (left sidebar)

3. Click **New Query**

4. Copy and paste the entire contents of `supabase_schema.sql`

5. Click **Run** to execute the SQL and create all tables

6. Verify tables were created by going to **Table Editor** - you should see:
   - `users`
   - `bids`
   - `tasks`
   - `notices`

## Step 3: Verify Configuration

The `config.py` file already contains your Supabase credentials. The configuration is set up with:
- Project URL: `https://tpurxqpicyoolvrupxwa.supabase.co`
- API Key: Already configured

## Step 4: Test the Application

1. Run the application:
   ```bash
   python main.py
   ```

2. On the login screen, click **"Create New Account"** to create your first user account

3. Login with your new credentials

4. Try creating a bid, task, or notice to verify database connectivity

## Features Now Available

✅ **User Authentication**: Create accounts and login through the app
✅ **Cloud Storage**: All bids, tasks, and notices are saved to Supabase
✅ **Multi-User Support**: Each user sees only their own data
✅ **Automatic Sync**: Data syncs automatically when you save
✅ **Offline Fallback**: If database is unavailable, falls back to local JSON files

## Troubleshooting

### "Failed to connect to Supabase"
- Check your internet connection
- Verify the Supabase project is active
- Check that the API key in `config.py` is correct

### "Table does not exist"
- Make sure you ran the SQL schema in Supabase SQL Editor
- Check that all tables were created successfully

### "Username already exists"
- This is normal - try a different username
- Or login with existing credentials

### Database connection issues
- The app will automatically fall back to local JSON files if database is unavailable
- Your data will be saved locally and can be synced later

## Security Notes

- The `config.py` file contains your API keys
- For production, consider using environment variables instead
- Never commit `config.py` with real keys to public repositories
- The anon/public key is safe for client-side use
- The service role key should be kept secret

## Next Steps

1. Create user accounts for your team members
2. Start using the app - all data will be saved to the cloud
3. Access your data from the Supabase dashboard anytime
4. Data is automatically backed up by Supabase

