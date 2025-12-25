-- Fix: Add the missing first item (item_order 0) for Initial Secure
-- Run this in Supabase Dashboard -> SQL Editor

-- Check current count
SELECT COUNT(*) as current_count FROM wo_inspection_checklist_items WHERE inspection_type = 'Initial Secure';

-- Insert the missing first item (item_order 0)
INSERT INTO wo_inspection_checklist_items (inspection_type, item_order, item_text)
VALUES 
    ('Initial Secure', 0, 'Vendor completed all required work as per instructions')
ON CONFLICT (inspection_type, item_order) DO UPDATE
SET item_text = EXCLUDED.item_text;

-- Verify all items are present (should show 22 items)
SELECT item_order, item_text 
FROM wo_inspection_checklist_items 
WHERE inspection_type = 'Initial Secure' 
ORDER BY item_order;

