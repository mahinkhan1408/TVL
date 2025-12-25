# Bid Writer Upgrade Guide - Username Tracking & Photo Upload

## ✅ What's Been Implemented

### 1. **Username Tracking**
- Every bid now saves the username of who created/saved it
- Username is displayed in the dashboard for all users to see
- Username is automatically captured when saving a bid

### 2. **Photo Upload to Supabase Storage**
- All photos are now uploaded to Supabase Storage when saving bids
- Photos are organized by: `user_id/wo_number/photo_key.jpg`
- Photos can be downloaded later from storage
- Photos are accessible to anyone with proper permissions

### 3. **Enhanced Search & Display**
- Dashboard shows "Created By" column with username
- All users can see who created each bid
- Search functionality works across all bids

## 📋 Setup Steps

### Step 1: Run SQL Migration

Run the SQL file `update_bids_table_complete.sql` in your Supabase Dashboard → SQL Editor.

This will:
- Add `property_address` column
- Add `created_by_username` column
- Create indexes for faster searching
- Update existing bids with usernames (if possible)

### Step 2: Create Supabase Storage Bucket

1. Go to Supabase Dashboard → Storage
2. Click "Create bucket"
3. Name: `bid-photos`
4. Set it as **Public** (so photos can be accessed)
5. Click "Create bucket"

**OR** run this SQL in the SQL Editor:
```sql
INSERT INTO storage.buckets (id, name, public) 
VALUES ('bid-photos', 'bid-photos', true)
ON CONFLICT (id) DO NOTHING;
```

### Step 3: Set Storage Policies (Important!)

Run this SQL to allow users to upload and download photos:

```sql
-- Allow authenticated users to upload photos
CREATE POLICY "Allow authenticated uploads" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'bid-photos');

-- Allow authenticated users to read photos
CREATE POLICY "Allow authenticated reads" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'bid-photos');

-- Allow authenticated users to update their photos
CREATE POLICY "Allow authenticated updates" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'bid-photos');

-- Allow authenticated users to delete their photos
CREATE POLICY "Allow authenticated deletes" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'bid-photos');
```

**Note:** Since we're using custom authentication (not Supabase Auth), you might need to adjust these policies. For now, you can make the bucket fully public for testing:

```sql
-- Make bucket fully public (for custom auth setup)
CREATE POLICY "Public upload" ON storage.objects
FOR INSERT TO public
WITH CHECK (bucket_id = 'bid-photos');

CREATE POLICY "Public read" ON storage.objects
FOR SELECT TO public
USING (bucket_id = 'bid-photos');
```

### Step 4: Test the Setup

1. **Create a new bid** - It will ask for Work Order and Property Address
2. **Add photos** to your bid items
3. **Save the bid** - Photos will be uploaded to Supabase Storage
4. **Check the dashboard** - You should see:
   - Work Order
   - Property Address
   - Bid Count
   - **Created By** (your username)
   - Last Modified
   - Delete/Export buttons

## 🔍 How It Works

### Saving Bids
1. When you click "Save State", the system:
   - Collects all bid data
   - Uploads all photos to Supabase Storage
   - Saves bid data with your username to the database
   - Creates references to photos in storage

### Loading Bids
1. When you open a bid:
   - Bid data is loaded from database
   - Photos can be downloaded from storage (optional)
   - All information is displayed including who created it

### Photo Storage Structure
```
bid-photos/
  ├── user_id_1/
  │   ├── WO123/
  │   │   ├── item_key_1.jpg
  │   │   ├── item_key_2.jpg
  │   │   └── ...
  │   └── WO456/
  │       └── ...
  └── user_id_2/
      └── ...
```

## 📸 Photo Management

### Current Implementation
- **Upload**: Photos are automatically uploaded when saving bids
- **Storage**: Photos stored in Supabase Storage bucket `bid-photos`
- **Reference**: Photo paths/URLs stored in `item_photos` JSONB field
- **Download**: Photos can be downloaded on demand when loading bids

### Future Enhancements (Optional)
- Add photo preview/management UI
- Bulk photo download
- Photo compression before upload
- Photo thumbnails generation

## ✅ Verification Checklist

After setup, verify:
- [ ] SQL migration ran successfully
- [ ] Storage bucket `bid-photos` exists and is public
- [ ] Storage policies are set correctly
- [ ] Can create a new bid with photos
- [ ] Photos upload successfully
- [ ] Dashboard shows "Created By" column
- [ ] Username appears correctly for saved bids
- [ ] Can search bids by Work Order or Property Address
- [ ] Can load existing bids with photos

## 🐛 Troubleshooting

### Photos Not Uploading
- Check storage bucket exists: `bid-photos`
- Verify bucket is public
- Check storage policies are set
- Check console for error messages

### Username Not Showing
- Verify SQL migration ran successfully
- Check `created_by_username` column exists in `bids` table
- Verify username is being passed when saving

### Storage Permission Errors
- Review storage policies
- Check bucket is set to public
- Verify RLS policies allow your operations

## 📝 Notes

- **Existing bids**: Old bids without usernames will show "N/A" in "Created By" column
- **Photo paths**: Old bids may still have local file paths - these will be preserved
- **Download**: Photos are downloaded on-demand when loading bids (optional feature)
- **Performance**: Large photos may take time to upload - progress indication can be added later

