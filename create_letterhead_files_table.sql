-- Create Letterhead Files Table
-- Run this in Supabase Dashboard -> SQL Editor

-- Step 1: Create the letterhead_files table
CREATE TABLE IF NOT EXISTS letterhead_files (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('Estimate', 'Invoice')),
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Path in Supabase Storage
    uploaded_by_username TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_letterhead_files_category ON letterhead_files(category);
CREATE INDEX IF NOT EXISTS idx_letterhead_files_user ON letterhead_files(user_id);
CREATE INDEX IF NOT EXISTS idx_letterhead_files_user_category ON letterhead_files(user_id, category);

-- Step 3: Create storage bucket for letterhead files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('letterhead-files', 'letterhead-files', true)
ON CONFLICT (id) DO NOTHING;

-- Step 4: Set storage policies for letterhead files (make bucket fully public for custom auth)
DROP POLICY IF EXISTS "Public upload letterhead files" ON storage.objects;
DROP POLICY IF EXISTS "Public read letterhead files" ON storage.objects;
DROP POLICY IF EXISTS "Public delete letterhead files" ON storage.objects;

CREATE POLICY "Public upload letterhead files" ON storage.objects
FOR INSERT TO public
WITH CHECK (bucket_id = 'letterhead-files');

CREATE POLICY "Public read letterhead files" ON storage.objects
FOR SELECT TO public
USING (bucket_id = 'letterhead-files');

CREATE POLICY "Public delete letterhead files" ON storage.objects
FOR DELETE TO public
USING (bucket_id = 'letterhead-files');

-- Step 5: Add comments
COMMENT ON TABLE letterhead_files IS 'Stores uploaded Word files for Estimate and Invoice sections';
COMMENT ON COLUMN letterhead_files.category IS 'Either Estimate or Invoice';
COMMENT ON COLUMN letterhead_files.file_path IS 'Path to file in Supabase Storage bucket';

