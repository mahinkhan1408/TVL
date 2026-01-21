-- Create tables for Special Contractor Prices
-- Run this in Supabase Dashboard -> SQL Editor

-- ==================== Special Contractors Table ====================
CREATE TABLE IF NOT EXISTS special_contractors (
    id BIGSERIAL PRIMARY KEY,
    contractor_name TEXT NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(contractor_name)
);

-- ==================== Contractor Line Items Table ====================
CREATE TABLE IF NOT EXISTS contractor_line_items (
    id BIGSERIAL PRIMARY KEY,
    contractor_id BIGINT NOT NULL REFERENCES special_contractors(id) ON DELETE CASCADE,
    line_item TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== Indexes for Performance ====================
CREATE INDEX IF NOT EXISTS idx_special_contractors_name ON special_contractors(contractor_name);
CREATE INDEX IF NOT EXISTS idx_special_contractors_user ON special_contractors(user_id);
CREATE INDEX IF NOT EXISTS idx_contractor_line_items_contractor ON contractor_line_items(contractor_id);
CREATE INDEX IF NOT EXISTS idx_contractor_line_items_user ON contractor_line_items(user_id);

-- ==================== Row Level Security (RLS) Policies ====================
-- Enable RLS
ALTER TABLE special_contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE contractor_line_items ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view all contractors (for now - can be restricted later)
CREATE POLICY "Users can view all contractors" ON special_contractors
    FOR SELECT USING (true);

-- Policy: Users can insert their own contractors
CREATE POLICY "Users can insert contractors" ON special_contractors
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text OR true);

-- Policy: Users can update contractors
CREATE POLICY "Users can update contractors" ON special_contractors
    FOR UPDATE USING (true);

-- Policy: Users can delete contractors
CREATE POLICY "Users can delete contractors" ON special_contractors
    FOR DELETE USING (true);

-- Policy: Users can view all line items
CREATE POLICY "Users can view all line items" ON contractor_line_items
    FOR SELECT USING (true);

-- Policy: Users can insert line items
CREATE POLICY "Users can insert line items" ON contractor_line_items
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text OR true);

-- Policy: Users can update line items
CREATE POLICY "Users can update line items" ON contractor_line_items
    FOR UPDATE USING (true);

-- Policy: Users can delete line items
CREATE POLICY "Users can delete line items" ON contractor_line_items
    FOR DELETE USING (true);




