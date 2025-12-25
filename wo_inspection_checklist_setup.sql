-- Standalone SQL script to create checklist items table and populate Winterization items
-- Run this in Supabase Dashboard -> SQL Editor

-- Create the checklist items table if it doesn't exist
CREATE TABLE IF NOT EXISTS wo_inspection_checklist_items (
    id BIGSERIAL PRIMARY KEY,
    inspection_type TEXT NOT NULL,
    item_order INTEGER NOT NULL,
    item_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(inspection_type, item_order)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_checklist_items_type ON wo_inspection_checklist_items(inspection_type);
CREATE INDEX IF NOT EXISTS idx_checklist_items_order ON wo_inspection_checklist_items(inspection_type, item_order);

-- Enable RLS
ALTER TABLE wo_inspection_checklist_items ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies (drop existing policies first if they exist)
DROP POLICY IF EXISTS "Anyone can view checklist items" ON wo_inspection_checklist_items;
DROP POLICY IF EXISTS "Anyone can insert checklist items" ON wo_inspection_checklist_items;
DROP POLICY IF EXISTS "Anyone can update checklist items" ON wo_inspection_checklist_items;
DROP POLICY IF EXISTS "Anyone can delete checklist items" ON wo_inspection_checklist_items;

CREATE POLICY "Anyone can view checklist items" ON wo_inspection_checklist_items FOR SELECT 
    USING (true);
CREATE POLICY "Anyone can insert checklist items" ON wo_inspection_checklist_items FOR INSERT 
    WITH CHECK (true);
CREATE POLICY "Anyone can update checklist items" ON wo_inspection_checklist_items FOR UPDATE 
    USING (true);
CREATE POLICY "Anyone can delete checklist items" ON wo_inspection_checklist_items FOR DELETE 
    USING (true);

-- Insert Winterization checklist items
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

-- Insert Initial Secure checklist items
INSERT INTO wo_inspection_checklist_items (inspection_type, item_order, item_text)
VALUES 
    ('Initial Secure', 0, 'Vendor completed all required work as per instructions'),
    ('Initial Secure', 1, 'Read the WO Instructions and verified the completed job'),
    ('Initial Secure', 2, 'Locks changed to correct key code & lock code (Provided Photos)'),
    ('Initial Secure', 3, 'Provided Property Note'),
    ('Initial Secure', 4, 'Vendor Provided photos of all sides and all structure of the property.'),
    ('Initial Secure', 5, 'All structured are secured as per the instructions.'),
    ('Initial Secure', 6, 'Checked Garage Condition'),
    ('Initial Secure', 7, 'Checked Winterization Status'),
    ('Initial Secure', 8, 'Checked Grass Condition'),
    ('Initial Secure', 9, 'Addressed Perishables (Interior + Refrigerator)'),
    ('Initial Secure', 10, 'Checked Heating system and HWH'),
    ('Initial Secure', 11, 'Checked Basement/Crawlspace Present'),
    ('Initial Secure', 12, 'Addressed Sump Pump'),
    ('Initial Secure', 13, 'Addressed all the molds'),
    ('Initial Secure', 14, 'Addressed Ceiling damages/Attic Damages'),
    ('Initial Secure', 15, 'Addressed Debris Removal (Interior/Exterior)'),
    ('Initial Secure', 16, 'Addressed Gutter/Siding/Soffit/Fascia'),
    ('Initial Secure', 17, 'Bid provided for overgrowths (Tree/Shrubs)'),
    ('Initial Secure', 18, 'Bid provided for overgrowths (Saplings/Vines)'),
    ('Initial Secure', 19, '3rd party Inspection bids provided if needed'),
    ('Initial Secure', 20, 'Full property condition report completed'),
    ('Initial Secure', 21, 'Roof addressed: mold, tarp, ladder rental (if 2-story), roof replacement if old')
ON CONFLICT (inspection_type, item_order) DO NOTHING;

