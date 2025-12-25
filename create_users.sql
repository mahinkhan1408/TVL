-- Create Users in Supabase
-- Run this in Supabase Dashboard -> SQL Editor
-- This will create two users: Aaron and Kent with password "abcde"
-- Passwords are stored in plain text (no hashing)

-- First, let's check if users already exist and remove them if needed
-- (Optional - comment out if you want to keep existing users)
-- DELETE FROM bids WHERE user_id IN (SELECT id FROM users WHERE username IN ('Aaron', 'Kent'));
-- DELETE FROM users WHERE username IN ('Aaron', 'Kent');

-- ========================================
-- ADDING NEW USERS
-- ========================================
-- To add new users, simply use:
-- INSERT INTO users (username, password_hash, created_at)
-- VALUES ('Username', 'PlainTextPassword', NOW())
-- ON CONFLICT (username) DO UPDATE 
-- SET password_hash = EXCLUDED.password_hash;
-- ========================================

-- Create Aaron user
INSERT INTO users (username, password_hash, created_at)
VALUES (
    'Aaron', 
    'abcde', -- Plain text password
    NOW()
)
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash;

-- Create Kent user  
INSERT INTO users (username, password_hash, created_at)
VALUES (
    'Kent',
    'abcde', -- Plain text password
    NOW()
)
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash;

-- Verify users were created
SELECT id, username, created_at FROM users WHERE username IN ('Aaron', 'Kent');

