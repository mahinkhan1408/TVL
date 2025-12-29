-- Add is_admin column to users table
-- Run this in Supabase Dashboard -> SQL Editor

-- Add is_admin column (defaults to false)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;

-- Update existing users to be non-admin by default (if needed)
-- UPDATE users SET is_admin = false WHERE is_admin IS NULL;

-- Example: Make a user admin (replace 'Aaron' with desired username)
-- UPDATE users SET is_admin = true WHERE username = 'Aaron';

