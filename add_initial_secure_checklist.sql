-- Add Initial Secure checklist items to database
-- Run this in Supabase Dashboard -> SQL Editor

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

