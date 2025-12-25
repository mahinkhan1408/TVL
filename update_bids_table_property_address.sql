-- Update Bids Table to Add Property Address
-- Run this in Supabase Dashboard -> SQL Editor

-- Add property_address column to bids table
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS property_address TEXT;

-- Create indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_bids_property_address ON bids(property_address);
CREATE INDEX IF NOT EXISTS idx_bids_wo_number ON bids(wo_number);
CREATE INDEX IF NOT EXISTS idx_bids_user_property ON bids(user_id, property_address);
CREATE INDEX IF NOT EXISTS idx_bids_user_wo ON bids(user_id, wo_number);

-- Add comment to document the column
COMMENT ON COLUMN bids.property_address IS 'USA Property Address for the work order';

