-- Supabase Database Schema for Techvengers App
-- Run this in Supabase Dashboard -> SQL Editor

-- ==================== Users Table ====================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- ==================== Bids Table ====================
CREATE TABLE IF NOT EXISTS bids (
    id BIGSERIAL PRIMARY KEY,
    wo_number TEXT NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selected_items JSONB NOT NULL DEFAULT '{}',
    item_photos JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(wo_number, user_id)
);

-- ==================== Tasks Table ====================
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'todo',
    deadline TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ==================== Notices Table ====================
CREATE TABLE IF NOT EXISTS notices (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== Approvals Table ====================
CREATE TABLE IF NOT EXISTS approvals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    approval_date DATE NOT NULL,
    work_order TEXT NOT NULL,
    approval_amount DECIMAL(15, 2) NOT NULL,
    vendor_price DECIMAL(15, 2) NOT NULL,
    gross_profit DECIMAL(15, 2) NOT NULL,
    source_work_order TEXT,
    month_year TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== WO Inspections Table ====================
CREATE TABLE IF NOT EXISTS wo_inspections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    inspection_type TEXT NOT NULL,
    work_order TEXT NOT NULL,
    inspection_data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== WO Inspection Checklist Items Table ====================
CREATE TABLE IF NOT EXISTS wo_inspection_checklist_items (
    id BIGSERIAL PRIMARY KEY,
    inspection_type TEXT NOT NULL,
    item_order INTEGER NOT NULL,
    item_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(inspection_type, item_order)
);

-- ==================== Indexes for Performance ====================
CREATE INDEX IF NOT EXISTS idx_bids_wo ON bids(wo_number);
CREATE INDEX IF NOT EXISTS idx_bids_user ON bids(user_id);
CREATE INDEX IF NOT EXISTS idx_bids_updated ON bids(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_notices_created ON notices(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approvals_user ON approvals(user_id);
CREATE INDEX IF NOT EXISTS idx_approvals_month_year ON approvals(month_year);
CREATE INDEX IF NOT EXISTS idx_approvals_date ON approvals(approval_date DESC);
CREATE INDEX IF NOT EXISTS idx_wo_inspections_user ON wo_inspections(user_id);
CREATE INDEX IF NOT EXISTS idx_wo_inspections_type ON wo_inspections(inspection_type);
CREATE INDEX IF NOT EXISTS idx_wo_inspections_wo ON wo_inspections(work_order);
CREATE INDEX IF NOT EXISTS idx_checklist_items_type ON wo_inspection_checklist_items(inspection_type);
CREATE INDEX IF NOT EXISTS idx_checklist_items_order ON wo_inspection_checklist_items(inspection_type, item_order);

-- ==================== Row Level Security (RLS) ====================
-- Enable RLS on all tables
ALTER TABLE bids ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE wo_inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE wo_inspection_checklist_items ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Bids Table
-- Note: Since we're using custom authentication (not Supabase Auth),
-- these policies allow operations when user_id is present
CREATE POLICY "Users can view own bids" ON bids FOR SELECT 
    USING (true);
CREATE POLICY "Users can insert own bids" ON bids FOR INSERT 
    WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can update own bids" ON bids FOR UPDATE 
    USING (true) WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can delete own bids" ON bids FOR DELETE 
    USING (true);

-- RLS Policies for Tasks Table
CREATE POLICY "Users can view own tasks" ON tasks FOR SELECT 
    USING (true);
CREATE POLICY "Users can insert own tasks" ON tasks FOR INSERT 
    WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can update own tasks" ON tasks FOR UPDATE 
    USING (true) WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can delete own tasks" ON tasks FOR DELETE 
    USING (true);

-- RLS Policies for Notices Table
CREATE POLICY "Users can view own notices" ON notices FOR SELECT 
    USING (true);
CREATE POLICY "Users can insert own notices" ON notices FOR INSERT 
    WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can update own notices" ON notices FOR UPDATE 
    USING (true) WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can delete own notices" ON notices FOR DELETE 
    USING (true);

-- RLS Policies for Approvals Table
CREATE POLICY "Users can view own approvals" ON approvals FOR SELECT 
    USING (true);
CREATE POLICY "Users can insert own approvals" ON approvals FOR INSERT 
    WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can update own approvals" ON approvals FOR UPDATE 
    USING (true) WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can delete own approvals" ON approvals FOR DELETE 
    USING (true);

-- RLS Policies for WO Inspections Table
CREATE POLICY "Users can view own wo_inspections" ON wo_inspections FOR SELECT 
    USING (true);
CREATE POLICY "Users can insert own wo_inspections" ON wo_inspections FOR INSERT 
    WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can update own wo_inspections" ON wo_inspections FOR UPDATE 
    USING (true) WITH CHECK (user_id IS NOT NULL);
CREATE POLICY "Users can delete own wo_inspections" ON wo_inspections FOR DELETE 
    USING (true);

-- RLS Policies for WO Inspection Checklist Items Table (public read access)
CREATE POLICY "Anyone can view checklist items" ON wo_inspection_checklist_items FOR SELECT 
    USING (true);
CREATE POLICY "Anyone can insert checklist items" ON wo_inspection_checklist_items FOR INSERT 
    WITH CHECK (true);
CREATE POLICY "Anyone can update checklist items" ON wo_inspection_checklist_items FOR UPDATE 
    USING (true);
CREATE POLICY "Anyone can delete checklist items" ON wo_inspection_checklist_items FOR DELETE 
    USING (true);

-- ==================== Function to Update updated_at ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on bids
CREATE TRIGGER update_bids_updated_at BEFORE UPDATE ON bids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on approvals
CREATE TRIGGER update_approvals_updated_at BEFORE UPDATE ON approvals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on wo_inspections
CREATE TRIGGER update_wo_inspections_updated_at BEFORE UPDATE ON wo_inspections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Initialize Checklist Items ====================
-- Note: This INSERT will only work if the table was created above.
-- If you get an error, run wo_inspection_checklist_setup.sql separately
-- Insert Winterization checklist items (only if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'wo_inspection_checklist_items') THEN
        INSERT INTO wo_inspection_checklist_items (inspection_type, item_order, item_text)
        VALUES 
            ('Winterization', 0, 'Water shut off at curb + zip tied'),
            ('Winterization', 1, 'Breakers OFF (unless sump pump/dehumidifier → ON)'),
            ('Winterization', 2, 'All water systems drained (heater, softener, tanks, lines, fixtures)'),
            ('Winterization', 3, 'Boiler/radiator draining photos (if applicable)'),
            ('Winterization', 4, 'Heating system photos provided'),
            ('Winterization', 5, 'All faucets/valves opened + radiators pressure released'),
            ('Winterization', 6, 'Compressor connected and running to blow out lines'),
            ('Winterization', 7, 'Compressor photos included'),
            ('Winterization', 8, 'Well pump drained (if applicable)'),
            ('Winterization', 9, 'Proper pressure test (35 PSI, stand-alone gauge, 30-min rest, final reading photo)'),
            ('Winterization', 10, 'Antifreeze poured in all drains'),
            ('Winterization', 11, 'Toilets cleaned, water removed, antifreeze added'),
            ('Winterization', 12, 'Winterization stickers filled (name/date)'),
            ('Winterization', 13, 'Stickers applied to all fixtures + front door/window'),
            ('Winterization', 14, 'Securing sticker placed on front door/window')
        ON CONFLICT (inspection_type, item_order) DO NOTHING;
    END IF;
END $$;

