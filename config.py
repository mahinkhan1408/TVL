# config.py
# Supabase Configuration
# IMPORTANT: For production, use environment variables instead of hardcoding

import os

# Supabase Project Configuration
# Extract project ID from dashboard URL: https://supabase.com/dashboard/project/tpurxqpicyoolvrupxwa
SUPABASE_PROJECT_ID = "tpurxqpicyoolvrupxwa"
SUPABASE_URL = f"https://{SUPABASE_PROJECT_ID}.supabase.co"

# API Keys
# Published key (anon/public key) - safe to use in client-side code
SUPABASE_ANON_KEY = "sb_publishable_wQxfua8Di6OkZGQhU3CsLw_XcsXmVXo"

# Secret key (service role key) - KEEP SECRET! Only use in server-side code
# For this desktop app, we'll use the anon key for most operations
SUPABASE_SERVICE_KEY = "sb_secret_HHY9y7s8kkx8UoE3gskY-w_cH-2KGml"

# For production, use environment variables:
# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
# SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

