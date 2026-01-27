-- SQL script to add Serial Bid Templates to Supabase
-- Run this in your Supabase SQL editor

-- Create table for serial bid templates if it doesn't exist
CREATE TABLE IF NOT EXISTS gc_serial_bid_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_text TEXT NOT NULL,
    logic_formula JSONB,
    input_fields JSONB,
    calculated_fields JSONB,
    rate_per_lf DECIMAL(10, 2) DEFAULT 18.00,
    post_unit_price DECIMAL(10, 2) DEFAULT 133.62,
    fence_price_per_lf DECIMAL(10, 2) DEFAULT 18.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert BID TEMPLATE 1 — Staircase Installation
INSERT INTO gc_serial_bid_templates (template_name, template_text, logic_formula, input_fields, calculated_fields)
VALUES (
    'Staircase Installation',
    'Install a {STAIR_COUNT}-step staircase at the {LOCATION} of the property. Scope of work includes installation of {STRINGER_COUNT} stringers ({STRINGER_LENGTH_LF} LF each, Total – {TOTAL_STRINGER_LF} LF) and {STAIR_COUNT} steps ({STEP_WIDTH_LF} LF each, Total – {TOTAL_STEP_LF} LF). Price includes material, labor, time, and removal of generated debris.',
    '{
        "RATE_PER_LF": 18,
        "STRINGER_COUNT": "ceil(STEP_WIDTH_LF / 2) + 1",
        "STRINGER_LENGTH_LF": "STAIR_COUNT",
        "TOTAL_STRINGER_LF": "STRINGER_COUNT × STRINGER_LENGTH_LF",
        "TOTAL_STEP_LF": "STAIR_COUNT × STEP_WIDTH_LF",
        "STRINGER_COST": "TOTAL_STRINGER_LF × RATE_PER_LF",
        "STEP_COST": "TOTAL_STEP_LF × RATE_PER_LF",
        "TOTAL_PRICE": "STRINGER_COST + STEP_COST"
    }'::jsonb,
    '["STAIR_COUNT", "STEP_WIDTH_LF", "LOCATION"]'::jsonb,
    '["STRINGER_COUNT", "STRINGER_LENGTH_LF", "TOTAL_STRINGER_LF", "TOTAL_STEP_LF"]'::jsonb
)
ON CONFLICT (template_name) DO UPDATE SET
    template_text = EXCLUDED.template_text,
    logic_formula = EXCLUDED.logic_formula,
    input_fields = EXCLUDED.input_fields,
    calculated_fields = EXCLUDED.calculated_fields,
    updated_at = NOW();

-- Insert BID TEMPLATE 2 — Handrail & Posts
INSERT INTO gc_serial_bid_templates (template_name, template_text, logic_formula, input_fields, calculated_fields)
VALUES (
    'Handrail & Posts',
    'Install {TOTAL_POST_LF} LF ({POST_LENGTH_LF} LF each – {POST_COUNT} posts) of posts and {HANDRAIL_LF} LF of handrail (Total – {TOTAL_PROJECT_LF} LF) at the {LOCATION} of the property. Price includes time, labor, and equipment.',
    '{
        "RATE_PER_LF": 18,
        "POST_COUNT_LOGIC": "If HANDRAIL_LF ≤ 5 → POST_COUNT = 2; If HANDRAIL_LF ≤ 10 → POST_COUNT = 3; If HANDRAIL_LF ≤ 20 → POST_COUNT = 5",
        "POST_LENGTH_LF": 5,
        "TOTAL_POST_LF": "POST_COUNT × POST_LENGTH_LF",
        "TOTAL_PROJECT_LF": "HANDRAIL_LF + TOTAL_POST_LF",
        "TOTAL_PRICE": "TOTAL_PROJECT_LF × RATE_PER_LF"
    }'::jsonb,
    '["HANDRAIL_LF", "LOCATION"]'::jsonb,
    '["POST_COUNT", "POST_LENGTH_LF", "TOTAL_POST_LF", "TOTAL_PROJECT_LF"]'::jsonb
)
ON CONFLICT (template_name) DO UPDATE SET
    template_text = EXCLUDED.template_text,
    logic_formula = EXCLUDED.logic_formula,
    input_fields = EXCLUDED.input_fields,
    calculated_fields = EXCLUDED.calculated_fields,
    updated_at = NOW();

-- Insert BID TEMPLATE 3 — Guardrail Installation
INSERT INTO gc_serial_bid_templates (template_name, template_text, logic_formula, input_fields, calculated_fields)
VALUES (
    'Guardrail Installation',
    'Install guardrail in a {GUARDRAIL_LF} LF area. Scope of work includes installation of {TOP_RAIL_LF} LF of top rail and {MIDDLE_RAIL_LF} LF of middle rail (Total – {TOTAL_RAIL_LF} LF, 2x4 wood will be used), along with {POST_COUNT} posts ({POST_LENGTH_LF} LF each – Total {TOTAL_POST_LF} LF, 2x4 wood will be used) to secure the guardrail and prevent trip hazards at the {LOCATION} of the property. Total of {TOTAL_MATERIAL_LF} LF of 2x4 wood will be used. Price includes time, labor, equipment, and material.',
    '{
        "RATE_PER_LF": 18,
        "TOP_RAIL_LF": "GUARDRAIL_LF",
        "MIDDLE_RAIL_LF": "GUARDRAIL_LF",
        "TOTAL_RAIL_LF": "GUARDRAIL_LF × 2",
        "POST_COUNT": "ceil(GUARDRAIL_LF / 5)",
        "POST_LENGTH_LF": 5,
        "TOTAL_POST_LF": "POST_COUNT × POST_LENGTH_LF",
        "TOTAL_MATERIAL_LF": "TOTAL_RAIL_LF + TOTAL_POST_LF",
        "TOTAL_PRICE": "TOTAL_MATERIAL_LF × RATE_PER_LF"
    }'::jsonb,
    '["GUARDRAIL_LF", "LOCATION"]'::jsonb,
    '["TOP_RAIL_LF", "MIDDLE_RAIL_LF", "TOTAL_RAIL_LF", "POST_COUNT", "POST_LENGTH_LF", "TOTAL_POST_LF", "TOTAL_MATERIAL_LF"]'::jsonb
)
ON CONFLICT (template_name) DO UPDATE SET
    template_text = EXCLUDED.template_text,
    logic_formula = EXCLUDED.logic_formula,
    input_fields = EXCLUDED.input_fields,
    calculated_fields = EXCLUDED.calculated_fields,
    updated_at = NOW();

-- Insert BID TEMPLATE 4 — Wood Fence Replacement
INSERT INTO gc_serial_bid_templates (template_name, template_text, logic_formula, input_fields, calculated_fields)
VALUES (
    'Wood Fence Replacement',
    'Install {FENCE_LF} LF of damaged wood fence at the {LOCATION} of the property. Scope of work includes installation of {POST_COUNT} wooden fence posts, set in concrete. Permit will be pulled and invoiced as needed. Price includes equipment, labor, and removal of generated debris.',
    '{
        "POST_UNIT_PRICE": 133.62,
        "FENCE_PRICE_PER_LF": 18,
        "POST_COUNT": "ceil(FENCE_LF / 8) + 1",
        "POST_COST": "POST_COUNT × POST_UNIT_PRICE",
        "FENCE_PANEL_COST": "FENCE_LF × FENCE_PRICE_PER_LF",
        "TOTAL_PRICE": "POST_COST + FENCE_PANEL_COST"
    }'::jsonb,
    '["FENCE_LF", "LOCATION"]'::jsonb,
    '["POST_COUNT"]'::jsonb
)
ON CONFLICT (template_name) DO UPDATE SET
    template_text = EXCLUDED.template_text,
    logic_formula = EXCLUDED.logic_formula,
    input_fields = EXCLUDED.input_fields,
    calculated_fields = EXCLUDED.calculated_fields,
    updated_at = NOW();

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_gc_serial_bid_templates_name ON gc_serial_bid_templates(template_name);

-- Add comments
COMMENT ON TABLE gc_serial_bid_templates IS 'Serial bid templates for GC/Roof CE module';
COMMENT ON COLUMN gc_serial_bid_templates.template_name IS 'Name of the bid template';
COMMENT ON COLUMN gc_serial_bid_templates.template_text IS 'Template text with placeholders';
COMMENT ON COLUMN gc_serial_bid_templates.logic_formula IS 'JSON object containing calculation formulas';
COMMENT ON COLUMN gc_serial_bid_templates.input_fields IS 'Array of required input field names';
COMMENT ON COLUMN gc_serial_bid_templates.calculated_fields IS 'Array of automatically calculated field names';

