-- SQL script to update the notices table with new columns
-- Run this in your Supabase SQL editor

-- Add category column if it doesn't exist
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'ALL';

-- Add title_color column if it doesn't exist
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS title_color TEXT DEFAULT '#000000';

-- Add card_color column if it doesn't exist
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS card_color TEXT DEFAULT '#ffffff';

-- Update existing notices to have default values if they are NULL
UPDATE notices 
SET category = 'ALL' 
WHERE category IS NULL;

UPDATE notices 
SET title_color = '#000000' 
WHERE title_color IS NULL;

UPDATE notices 
SET card_color = '#ffffff' 
WHERE card_color IS NULL;

