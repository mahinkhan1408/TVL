-- Complete Update for Bids Table with Property Address and Username
-- Run this in Supabase Dashboard -> SQL Editor

-- Step 1: Add property_address column (if not exists)
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS property_address TEXT;

-- Step 2: Add username column to track who created/saved the bid
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS created_by_username TEXT;

-- Step 3: Create indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_bids_property_address ON bids(property_address);
CREATE INDEX IF NOT EXISTS idx_bids_wo_number ON bids(wo_number);
CREATE INDEX IF NOT EXISTS idx_bids_user_property ON bids(user_id, property_address);
CREATE INDEX IF NOT EXISTS idx_bids_user_wo ON bids(user_id, wo_number);
CREATE INDEX IF NOT EXISTS idx_bids_created_by_username ON bids(created_by_username);
CREATE INDEX IF NOT EXISTS idx_bids_wo_username ON bids(wo_number, created_by_username);

-- Step 4: Update existing bids with username (optional - for existing data)
-- This will populate username from users table for existing bids
UPDATE bids 
SET created_by_username = (
    SELECT username 
    FROM users 
    WHERE users.id = bids.user_id
)
WHERE created_by_username IS NULL;

-- Step 5: Add comments to document the columns
COMMENT ON COLUMN bids.property_address IS 'USA Property Address for the work order';
COMMENT ON COLUMN bids.created_by_username IS 'Username of the user who created/saved this bid';

-- Step 6: Create storage bucket for bid photos
-- Create the storage bucket for bid photos
INSERT INTO storage.buckets (id, name, public) 
VALUES ('bid-photos', 'bid-photos', true)
ON CONFLICT (id) DO NOTHING;

-- Step 7: Set storage policies for photo uploads/downloads
-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Public upload bid photos" ON storage.objects;
DROP POLICY IF EXISTS "Public read bid photos" ON storage.objects;
DROP POLICY IF EXISTS "Public update bid photos" ON storage.objects;
DROP POLICY IF EXISTS "Public delete bid photos" ON storage.objects;

-- Allow public upload (adjust based on your auth setup)
CREATE POLICY "Public upload bid photos" ON storage.objects
FOR INSERT TO public
WITH CHECK (bucket_id = 'bid-photos');

-- Allow public read (so photos can be accessed)
CREATE POLICY "Public read bid photos" ON storage.objects
FOR SELECT TO public
USING (bucket_id = 'bid-photos');

-- Allow public update (to overwrite existing photos)
CREATE POLICY "Public update bid photos" ON storage.objects
FOR UPDATE TO public
USING (bucket_id = 'bid-photos');

-- Allow public delete (to remove photos)
CREATE POLICY "Public delete bid photos" ON storage.objects
FOR DELETE TO public
USING (bucket_id = 'bid-photos');

