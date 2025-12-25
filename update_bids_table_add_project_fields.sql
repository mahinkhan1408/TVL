-- Add Client Code and WO Type columns to Bids Table
-- Run this in Supabase Dashboard -> SQL Editor

-- Step 1: Add client_code column (if not exists)
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS client_code TEXT;

-- Step 2: Add wo_type column (if not exists)
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS wo_type TEXT;

-- Step 3: Create indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_bids_client_code ON bids(client_code);
CREATE INDEX IF NOT EXISTS idx_bids_wo_type ON bids(wo_type);

-- Step 4: Add comments to document the columns
COMMENT ON COLUMN bids.client_code IS 'Client Code for the work order';
COMMENT ON COLUMN bids.wo_type IS 'Work Order Type (e.g., Initial REO Service, Inspection, etc.)';

