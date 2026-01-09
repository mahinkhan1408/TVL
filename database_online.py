# database_online.py
# Supabase Database Manager for Techvengers App

from supabase import create_client, Client
import json
from typing import Optional, List, Dict
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_ANON_KEY
import bcrypt
import os

class OnlineDatabaseManager:
    """
    Manages all database operations with Supabase
    Handles users, bids, tasks, and notices
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        print(f"[OnlineDatabaseManager.__init__] Starting initialization...", flush=True)
        try:
            # Validate URL and key format
            print(f"[OnlineDatabaseManager.__init__] Validating config...", flush=True)
            if not SUPABASE_URL or not SUPABASE_ANON_KEY:
                raise ValueError("Supabase URL or API key is missing in config.py")
            print(f"[OnlineDatabaseManager.__init__] Config valid. URL: {SUPABASE_URL}", flush=True)
            
            print(f"[OnlineDatabaseManager.__init__] Creating Supabase client...", flush=True)
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            print(f"[OnlineDatabaseManager.__init__] ✅ Supabase client created", flush=True)
            
            # Test connection by trying a simple query
            # This will fail gracefully if tables don't exist yet
            try:
                self.supabase.table('users').select('id').limit(1).execute()
            except Exception:
                # Tables might not exist yet - that's okay, connection is working
                pass
                
        except Exception as e:
            error_msg = str(e)
            print(f"[OnlineDatabaseManager.__init__] ERROR during initialization: {error_msg}", flush=True)
            import traceback
            traceback.print_exc()
            if "Invalid API key" in error_msg or "401" in error_msg or "403" in error_msg:
                raise ConnectionError(f"Invalid Supabase API key. Please check your API key in config.py.\nError: {e}")
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                raise ConnectionError(f"Could not connect to Supabase. Please check your internet connection.\nError: {e}")
            else:
                raise ConnectionError(f"Failed to connect to Supabase: {e}")
    
    # ==================== User Management ====================
    
    def create_user(self, username: str, password: str) -> Dict:
        """
        Create a new user with plain text password
        
        Args:
            username: Unique username
            password: Plain text password (stored as-is)
            
        Returns:
            User dictionary with id, username, created_at
        """
        try:
            # Store password in plain text (no hashing)
            # Insert user
            result = self.supabase.table('users').insert({
                'username': username,
                'password_hash': password  # Store as plain text
            }).execute()
            
            if result.data:
                user = result.data[0]
                # Don't return password hash
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'created_at': user['created_at']
                }
            return None
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                raise ValueError("Username already exists")
            raise e
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            result = self.supabase.table('users').select('*').eq('username', username).execute()
            if result.data:
                user = result.data[0]
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'password_hash': user['password_hash'],
                    'created_at': user['created_at'],
                    'last_login': user.get('last_login')
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Verify user credentials (plain text comparison)
        
        Returns:
            User dict if valid, None if invalid
        """
        user = self.get_user(username)
        # Compare passwords in plain text
        if user and password == user['password_hash']:
            # Update last login
            self.update_last_login(user['id'])
            return {
                'id': user['id'],
                'username': user['username'],
                'created_at': user['created_at']
            }
        return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login time"""
        try:
            self.supabase.table('users').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    # ==================== Bid Management ====================
    
    def create_project(self, wo_number: str, user_id: int, property_address: str = None, 
                     client_code: str = None, wo_type: str = None, username: str = None):
        """Create a new project entry in the database with all project fields."""
        try:
            # Check if project already exists
            existing = self.supabase.table('bids').select('id').eq('wo_number', wo_number).eq('user_id', user_id).execute()
            
            if existing.data:
                # Project exists, update it with new fields
                update_data = {}
                if property_address is not None:
                    update_data['property_address'] = property_address
                if client_code is not None:
                    update_data['client_code'] = client_code
                if wo_type is not None:
                    update_data['wo_type'] = wo_type
                if username and not existing.data[0].get('created_by_username'):
                    update_data['created_by_username'] = username
                elif not existing.data[0].get('created_by_username'):
                    # Try to get username from user_id if not provided
                    user = self.get_user_by_id(user_id)
                    if user:
                        update_data['created_by_username'] = user.get('username')
                
                if update_data:
                    update_data['updated_at'] = datetime.now().isoformat()
                    self.supabase.table('bids').update(update_data).eq('id', existing.data[0]['id']).execute()
            else:
                # Create new project entry
                project_data = {
                    'wo_number': wo_number,
                    'user_id': user_id,
                    'selected_items': {},  # Empty initially
                    'item_photos': {},    # Empty initially
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                if property_address is not None:
                    project_data['property_address'] = property_address
                if client_code is not None:
                    project_data['client_code'] = client_code
                if wo_type is not None:
                    project_data['wo_type'] = wo_type
                if username:
                    project_data['created_by_username'] = username
                
                self.supabase.table('bids').insert(project_data).execute()
        except Exception as e:
            print(f"Warning: Could not create project: {e}")
            # Don't raise - allow app to continue
    
    def save_bid(self, wo_number: str, user_id: int, selected_items: dict, item_photos: dict, property_address: str = None, username: str = None, client_code: str = None, wo_type: str = None):
        """
        Save or update a bid with photos uploaded to Supabase Storage
        
        Args:
            wo_number: Work Order number
            user_id: User ID who owns this bid
            selected_items: Dictionary of selected items
            item_photos: Dictionary of item photos (with 'path' keys pointing to local files)
            property_address: USA Property Address (optional)
            username: Username of the user saving the bid (optional, will be fetched if not provided)
        """
        try:
            # Get username if not provided
            if not username:
                user = self.get_user_by_id(user_id)
                username = user['username'] if user else None
            
            # Upload photos to Supabase Storage and get URLs
            uploaded_photos = {}
            print(f"\n[save_bid] Received item_photos: {item_photos}")
            print(f"[save_bid] item_photos type: {type(item_photos)}, length: {len(item_photos) if item_photos else 0}")
            if item_photos:
                print(f"[save_bid] Processing {len(item_photos)} photos for upload")
                print(f"[save_bid] item_photos keys: {list(item_photos.keys())}")
                uploaded_photos = self.upload_bid_photos(wo_number, user_id, item_photos)
                print(f"[save_bid] Uploaded photos result: {len(uploaded_photos)} photos")
                print(f"[save_bid] Uploaded photos keys: {list(uploaded_photos.keys())}")
            else:
                print(f"[save_bid] ⚠️ No photos to upload (item_photos is empty or None)")
            
            # Check if bid exists
            existing = self.supabase.table('bids').select('id, property_address, client_code, wo_type, created_by_username').eq('wo_number', wo_number).eq('user_id', user_id).execute()
            
            bid_data = {
                'wo_number': wo_number,
                'user_id': user_id,
                'selected_items': selected_items,  # Supabase handles JSON automatically
                'item_photos': uploaded_photos,  # Store URLs/references instead of local paths
                'updated_at': datetime.now().isoformat()
            }
            
            # Add property_address if provided (only update if provided or doesn't exist)
            if property_address is not None:
                bid_data['property_address'] = property_address
            elif existing.data and existing.data[0].get('property_address'):
                # Preserve existing property_address if not provided
                bid_data['property_address'] = existing.data[0]['property_address']
            
            # Add username (set on creation, update if not set)
            if not existing.data:
                # New bid - set created_by_username
                if username:
                    bid_data['created_by_username'] = username
                else:
                    # Get username from user_id if not provided
                    user = self.get_user_by_id(user_id)
                    if user:
                        bid_data['created_by_username'] = user.get('username')
            else:
                # Existing bid - always ensure username is set
                if username:
                    # Always update if username is provided
                    bid_data['created_by_username'] = username
                else:
                    # Try to get username from user_id if not provided
                    user = self.get_user_by_id(user_id)
                    if user:
                        bid_data['created_by_username'] = user.get('username')
                    elif existing.data[0].get('created_by_username'):
                        # Preserve existing username only as last resort
                        bid_data['created_by_username'] = existing.data[0].get('created_by_username')
            
            # Add client_code if provided
            if client_code is not None:
                bid_data['client_code'] = client_code
            elif existing.data and existing.data[0].get('client_code'):
                # Preserve existing client_code if not provided
                bid_data['client_code'] = existing.data[0]['client_code']
            
            # Add wo_type if provided
            if wo_type is not None:
                bid_data['wo_type'] = wo_type
            elif existing.data and existing.data[0].get('wo_type'):
                # Preserve existing wo_type if not provided
                bid_data['wo_type'] = existing.data[0]['wo_type']
            
            if existing.data:
                # Update existing
                self.supabase.table('bids').update(bid_data).eq('id', existing.data[0]['id']).execute()
            else:
                # Insert new
                bid_data['created_at'] = datetime.now().isoformat()
                self.supabase.table('bids').insert(bid_data).execute()
        except Exception as e:
            raise Exception(f"Failed to save bid: {e}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                return user.get('is_admin', False)
            return False
        except Exception as e:
            print(f"Error checking admin status: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        try:
            result = self.supabase.table('users').select('id, username, created_at, last_login, is_admin').order('username').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def delete_user(self, user_id: int):
        """Delete a user (admin only)"""
        try:
            self.supabase.table('users').delete().eq('id', user_id).execute()
        except Exception as e:
            raise Exception(f"Failed to delete user: {e}")
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """
        Get daily statistics for bids and work orders
        
        Args:
            date: Date in format 'YYYY-MM-DD'. If None, uses today.
            
        Returns:
            Dictionary with stats: {
                'date': date,
                'total_bids': count,
                'total_work_orders': count,
                'bids_by_user': {username: count},
                'work_orders_by_user': {username: count}
            }
        """
        try:
            from datetime import datetime, timedelta
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Get all bids created on this date
            start_date = f"{date} 00:00:00"
            end_date = f"{date} 23:59:59"
            
            # Get bids for the date
            bids_result = self.supabase.table('bids').select('id, wo_number, user_id, created_by_username, created_at').gte('created_at', start_date).lte('created_at', end_date).execute()
            
            total_bids = len(bids_result.data) if bids_result.data else 0
            unique_work_orders = set()
            bids_by_user = {}
            work_orders_by_user = {}
            
            for bid in (bids_result.data or []):
                wo_number = bid.get('wo_number', '')
                if wo_number:
                    unique_work_orders.add(wo_number)
                
                username = bid.get('created_by_username', 'Unknown')
                if not username or username == 'Unknown':
                    # Try to get username from user_id
                    user_id = bid.get('user_id')
                    if user_id:
                        user = self.get_user_by_id(user_id)
                        if user:
                            username = user.get('username', 'Unknown')
                
                bids_by_user[username] = bids_by_user.get(username, 0) + 1
                if wo_number:
                    work_orders_by_user[username] = work_orders_by_user.get(username, 0) + 1
            
            return {
                'date': date,
                'total_bids': total_bids,
                'total_work_orders': len(unique_work_orders),
                'bids_by_user': bids_by_user,
                'work_orders_by_user': work_orders_by_user
            }
        except Exception as e:
            print(f"Error getting daily stats: {e}")
            return {
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'total_bids': 0,
                'total_work_orders': 0,
                'bids_by_user': {},
                'work_orders_by_user': {}
            }
    
    def upload_bid_photos(self, wo_number: str, user_id: int, item_photos: dict) -> dict:
        """
        Upload bid photos to Supabase Storage
        
        Args:
            wo_number: Work Order number
            user_id: User ID
            item_photos: Dictionary with photo keys and data containing 'path' to local file
            
        Returns:
            Dictionary with photo keys and storage paths/URLs
        """
        uploaded_photos = {}
        
        print(f"\n[upload_bid_photos] Starting upload for WO: {wo_number}, user_id: {user_id}")
        print(f"[upload_bid_photos] Received {len(item_photos)} photos to process")
        
        if not item_photos:
            print("[upload_bid_photos] No photos to upload")
            return {}
        
        try:
            # Ensure storage bucket exists (create if needed)
            bucket_name = 'bid-photos'
            
            # Test if bucket exists
            try:
                self.supabase.storage.from_(bucket_name).list()
                print(f"[upload_bid_photos] ✅ Storage bucket '{bucket_name}' exists")
            except Exception as bucket_error:
                print(f"[upload_bid_photos] ❌ Storage bucket '{bucket_name}' error: {bucket_error}")
                print(f"[upload_bid_photos] Returning original photos dict as fallback")
                return item_photos
            
            for photo_key, photo_data in item_photos.items():
                print(f"\n[upload_bid_photos] Processing photo_key: {photo_key}")
                print(f"  photo_data type: {type(photo_data)}")
                print(f"  photo_data value: {photo_data}")
                
                # Handle both dict format and string format (for backward compatibility)
                if isinstance(photo_data, str):
                    # If it's just a string (path), convert to dict format
                    photo_path = photo_data
                    photo_data = {'path': photo_path}
                    print(f"  Converted string to dict, path: {photo_path}")
                elif isinstance(photo_data, dict):
                    photo_path = photo_data.get('path', '')
                    print(f"  Dict format, path: {photo_path}")
                else:
                    # Skip invalid formats
                    print(f"  ⚠️ Skipping invalid format: {type(photo_data)}")
                    continue
                
                # Skip if already uploaded (has storage_path or url)
                if isinstance(photo_data, dict) and ('storage_path' in photo_data or 'url' in photo_data):
                    print(f"  ✅ Already uploaded, preserving: {photo_data}")
                    uploaded_photos[photo_key] = photo_data
                    continue
                
                if not photo_path:
                    print(f"  ⚠️ No photo path found")
                    continue
                
                if not os.path.exists(photo_path):
                    print(f"  ⚠️ Photo path doesn't exist: {photo_path}")
                    # If path doesn't exist, might already be a URL - preserve it
                    uploaded_photos[photo_key] = photo_data
                    continue
                
                try:
                    # Create storage path: user_id/wo_number/photo_key_filename
                    file_name = os.path.basename(photo_path)
                    file_ext = os.path.splitext(file_name)[1] or '.jpg'
                    storage_path = f"{user_id}/{wo_number}/{photo_key}{file_ext}"
                    
                    print(f"  📤 Uploading to storage: {storage_path}")
                    print(f"  📁 Local file: {photo_path}")
                    print(f"  📏 File size: {os.path.getsize(photo_path)} bytes")
                    
                    # Read photo file
                    with open(photo_path, 'rb') as f:
                        photo_bytes = f.read()
                    
                    print(f"  ✅ File read successfully, {len(photo_bytes)} bytes")
                    
                    # Upload to Supabase Storage
                    upload_result = self.supabase.storage.from_(bucket_name).upload(
                        path=storage_path,
                        file=photo_bytes,
                        file_options={"content-type": "image/jpeg", "upsert": "true"}
                    )
                    
                    print(f"  ✅ Upload successful: {upload_result}")
                    
                    # Get public URL
                    photo_url = self.supabase.storage.from_(bucket_name).get_public_url(storage_path)
                    
                    print(f"  🔗 Public URL: {photo_url}")
                    
                    # Store both path (for reference) and URL
                    uploaded_photos[photo_key] = {
                        'storage_path': storage_path,
                        'url': photo_url,
                        'original_path': photo_path  # Keep original for reference
                    }
                    
                    print(f"  ✅ Photo {photo_key} uploaded and saved to dict")
                except Exception as upload_error:
                    print(f"  ❌ Error uploading photo {photo_key}: {upload_error}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: store local path if upload fails
                    uploaded_photos[photo_key] = photo_data
        except Exception as e:
            print(f"[upload_bid_photos] ❌ Error in upload_bid_photos: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return original photos dict if storage not available
            return item_photos
        
        print(f"\n[upload_bid_photos] ✅ Upload complete. {len(uploaded_photos)} photos processed")
        print(f"[upload_bid_photos] Result: {uploaded_photos}\n")
        
        return uploaded_photos
    
    def download_bid_photo(self, storage_path: str, local_path: str) -> bool:
        """
        Download a photo from Supabase Storage to local path
        
        Args:
            storage_path: Path in Supabase Storage
            local_path: Local file path to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            bucket_name = 'bid-photos'
            photo_data = self.supabase.storage.from_(bucket_name).download(storage_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Write to file
            with open(local_path, 'wb') as f:
                f.write(photo_data)
            
            return True
        except Exception as e:
            print(f"Error downloading photo {storage_path}: {e}")
            return False
    
    def load_bid(self, wo_number: str, user_id: int = None, download_photos: bool = False, local_photo_dir: str = None, all_users: bool = False) -> Optional[Dict]:
        """
        Load a bid by WO number and optionally user ID
        
        Args:
            wo_number: Work Order number
            user_id: User ID (optional if all_users=True)
            download_photos: If True, download photos from storage to local files
            local_photo_dir: Directory to save downloaded photos (required if download_photos=True)
            all_users: If True, load bid from any user (user_id is ignored)
            
        Returns:
            Bid dictionary with all data including username and photos
        """
        try:
            query = self.supabase.table('bids').select('*').eq('wo_number', wo_number)
            if not all_users and user_id:
                query = query.eq('user_id', user_id)
            result = query.execute()
            
            if result.data:
                row = result.data[0]
                
                # Download photos if requested
                item_photos = row.get('item_photos', {}) or {}
                if download_photos and local_photo_dir and item_photos:
                    downloaded_photos = {}
                    os.makedirs(local_photo_dir, exist_ok=True)
                    
                    for photo_key, photo_data in item_photos.items():
                        if isinstance(photo_data, dict) and 'storage_path' in photo_data:
                            storage_path = photo_data['storage_path']
                            local_path = os.path.join(local_photo_dir, f"{photo_key}_{os.path.basename(storage_path)}")
                            
                            if self.download_bid_photo(storage_path, local_path):
                                downloaded_photos[photo_key] = {'path': local_path}
                            else:
                                # Fallback to URL if download fails
                                downloaded_photos[photo_key] = photo_data
                        else:
                            downloaded_photos[photo_key] = photo_data
                    
                    item_photos = downloaded_photos
                
                return {
                    'wo_number': row['wo_number'],
                    'property_address': row.get('property_address', ''),
                    'client_code': row.get('client_code', ''),
                    'wo_type': row.get('wo_type', ''),
                    'created_by_username': row.get('created_by_username', ''),
                    'user_id': row.get('user_id'),
                    'selected_items': row['selected_items'] if row['selected_items'] else {},
                    'item_photos': item_photos,
                    'created_at': row.get('created_at', ''),
                    'updated_at': row.get('updated_at', '')
                }
            return None
        except Exception as e:
            print(f"Error loading bid: {e}")
            return None
    
    def get_user_bids(self, user_id: int = None, all_bids: bool = False) -> List[Dict]:
        """
        Get all bids, optionally filtered by user
        
        Args:
            user_id: User ID to filter by (if None and all_bids=False, returns empty)
            all_bids: If True, return all bids regardless of user_id
            
        Returns:
            List of bid dictionaries ordered by most recent
        """
        try:
            query = self.supabase.table('bids').select('wo_number, property_address, client_code, wo_type, created_by_username, updated_at, created_at, user_id')
            
            if not all_bids:
                if user_id:
                    query = query.eq('user_id', user_id)
                else:
                    return []
            
            result = query.order('updated_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user bids: {e}")
            return []
    
    def search_bids_by_property_address(self, user_id: int = None, property_address: str = "", all_bids: bool = False) -> List[Dict]:
        """
        Search bids by property address (case-insensitive partial match)
        
        Args:
            user_id: User ID
            property_address: Property address to search for
            
        Returns:
            List of bid dictionaries matching the property address
        """
        try:
            # Use ilike for case-insensitive partial match
            query = self.supabase.table('bids')\
                .select('wo_number, property_address, client_code, wo_type, created_by_username, updated_at, created_at, user_id')\
                .ilike('property_address', f'%{property_address}%')
            
            if not all_bids and user_id:
                query = query.eq('user_id', user_id)
            
            result = query.order('updated_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching bids by property address: {e}")
            return []
    
    def search_bids_by_wo_number(self, user_id: int = None, wo_number: str = "", all_bids: bool = False) -> List[Dict]:
        """
        Search bids by work order number (case-insensitive partial match)
        
        Args:
            user_id: User ID
            wo_number: Work order number to search for
            
        Returns:
            List of bid dictionaries matching the work order number
        """
        try:
            # Use ilike for case-insensitive partial match
            query = self.supabase.table('bids')\
                .select('wo_number, property_address, client_code, wo_type, created_by_username, updated_at, created_at, user_id')\
                .ilike('wo_number', f'%{wo_number}%')
            
            if not all_bids and user_id:
                query = query.eq('user_id', user_id)
            
            result = query.order('updated_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching bids by work order: {e}")
            return []
    
    def get_bid_by_wo_and_property(self, user_id: int, wo_number: str, property_address: str = None) -> Optional[Dict]:
        """
        Get a bid by work order number and optionally property address
        
        Args:
            user_id: User ID
            wo_number: Work order number
            property_address: Optional property address for additional verification
            
        Returns:
            Bid dictionary if found, None otherwise
        """
        try:
            query = self.supabase.table('bids').select('*').eq('user_id', user_id).eq('wo_number', wo_number)
            if property_address:
                query = query.eq('property_address', property_address)
            
            result = query.execute()
            
            if result.data:
                row = result.data[0]
                return {
                    'wo_number': row['wo_number'],
                    'property_address': row.get('property_address', ''),
                    'selected_items': row['selected_items'] if row['selected_items'] else {},
                    'item_photos': row['item_photos'] if row['item_photos'] else {}
                }
            return None
        except Exception as e:
            print(f"Error getting bid by WO and property: {e}")
            return None
    
    def delete_bid(self, wo_number: str, user_id: int):
        """Delete a bid"""
        try:
            # First verify the bid exists for this user
            result = self.supabase.table('bids').select('id').eq('wo_number', wo_number).eq('user_id', user_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise Exception(f"No bid found for WO# {wo_number} for user_id {user_id}")
            
            # Delete the bid
            delete_result = self.supabase.table('bids').delete().eq('wo_number', wo_number).eq('user_id', user_id).execute()
            
            # Verify deletion (check if result contains deleted data or count)
            print(f"[delete_bid] Deleted bid WO# {wo_number} for user_id {user_id}. Result: {delete_result}")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"[delete_bid] Error deleting bid WO# {wo_number} for user_id {user_id}: {error_msg}")
            raise Exception(f"Failed to delete bid WO# {wo_number}: {error_msg}")
    
    # ==================== Task Management ====================
    
    def save_task(self, user_id: int, task_data: dict) -> int:
        """
        Save or update a task
        
        Args:
            user_id: User ID who owns the task
            task_data: Dictionary with task fields (id, title, description, etc.)
            
        Returns:
            Task ID
        """
        try:
            task_record = {
                'user_id': user_id,
                'title': task_data.get('title'),
                'description': task_data.get('description', ''),
                'priority': task_data.get('priority', 'medium'),
                'status': task_data.get('status', 'todo'),
                'deadline': task_data.get('deadline'),
                'completed_at': task_data.get('completed_at')
            }
            
            if 'id' in task_data and task_data['id']:
                # Update existing
                self.supabase.table('tasks').update(task_record).eq('id', task_data['id']).eq('user_id', user_id).execute()
                return task_data['id']
            else:
                # Insert new
                result = self.supabase.table('tasks').insert(task_record).execute()
                return result.data[0]['id'] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to save task: {e}")
    
    def get_user_tasks(self, user_id: int) -> List[Dict]:
        """Get all tasks for a user"""
        try:
            result = self.supabase.table('tasks').select('*').eq('user_id', user_id).order('created_at', desc=False).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user tasks: {e}")
            return []
    
    def delete_task(self, task_id: int, user_id: int):
        """Delete a task"""
        try:
            self.supabase.table('tasks').delete().eq('id', task_id).eq('user_id', user_id).execute()
        except Exception as e:
            raise Exception(f"Failed to delete task: {e}")
    
    # ==================== Notice Management ====================
    
    def save_notice(self, user_id: int, title: str, content: str, category: str = 'ALL', title_color: str = '#000000', card_color: str = '#ffffff') -> int:
        """Save a notice with category, title color, and card color"""
        try:
            result = self.supabase.table('notices').insert({
                'user_id': user_id,
                'title': title,
                'content': content,
                'category': category,
                'title_color': title_color,
                'card_color': card_color
            }).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to save notice: {e}")
    
    def get_all_notices(self) -> List[Dict]:
        """Get all notices, ordered by most recent"""
        try:
            result = self.supabase.table('notices').select('*, users(username)').order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting notices: {e}")
            return []
    
    def update_notice(self, notice_id: int, title: str, content: str, category: str = 'ALL', title_color: str = '#000000', card_color: str = '#ffffff'):
        """Update an existing notice"""
        try:
            result = self.supabase.table('notices').update({
                'title': title,
                'content': content,
                'category': category,
                'title_color': title_color,
                'card_color': card_color
            }).eq('id', notice_id).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to update notice: {e}")
    
    def delete_notice(self, notice_id: int, user_id: int = None):
        """Delete a notice (any user can delete)"""
        try:
            if user_id:
                # Try with user_id first, but don't require it
                self.supabase.table('notices').delete().eq('id', notice_id).execute()
            else:
                # Delete without user_id check
                self.supabase.table('notices').delete().eq('id', notice_id).execute()
        except Exception as e:
            raise Exception(f"Failed to delete notice: {e}")
    
    # ==================== Approval Management ====================
    
    def save_approval(self, user_id: int, approval_data: dict) -> int:
        """
        Save or update an approval entry
        
        Args:
            user_id: User ID who owns the approval
            approval_data: Dictionary with approval fields (id, approval_date, work_order, approval_amount, vendor_price, gross_profit, source_work_order, month_year)
            
        Returns:
            Approval ID
        """
        try:
            approval_record = {
                'user_id': user_id,
                'approval_date': approval_data.get('approval_date'),
                'work_order': approval_data.get('work_order'),
                'approval_amount': float(approval_data.get('approval_amount', 0)),
                'vendor_price': float(approval_data.get('vendor_price', 0)),
                'gross_profit': float(approval_data.get('gross_profit', 0)),
                'source_work_order': approval_data.get('source_work_order', ''),
                'month_year': approval_data.get('month_year')
            }
            
            if 'id' in approval_data and approval_data['id']:
                # Update existing
                self.supabase.table('approvals').update(approval_record).eq('id', approval_data['id']).eq('user_id', user_id).execute()
                return approval_data['id']
            else:
                # Insert new
                approval_record['updated_at'] = datetime.now().isoformat()
                result = self.supabase.table('approvals').insert(approval_record).execute()
                return result.data[0]['id'] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to save approval: {e}")
    
    def get_user_approvals_by_month(self, user_id: int, month_year: str) -> List[Dict]:
        """
        Get all approvals for a user for a specific month
        
        Args:
            user_id: User ID
            month_year: Month-year string in format "YYYY-MM"
            
        Returns:
            List of approval dictionaries
        """
        try:
            result = self.supabase.table('approvals').select('*').eq('user_id', user_id).eq('month_year', month_year).order('approval_date', desc=False).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user approvals: {e}")
            return []
    
    def get_all_user_approvals(self, user_id: int) -> List[Dict]:
        """Get all approvals for a user"""
        try:
            result = self.supabase.table('approvals').select('*').eq('user_id', user_id).order('approval_date', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting all user approvals: {e}")
            return []
    
    def delete_approval(self, approval_id: int, user_id: int):
        """Delete an approval entry"""
        try:
            self.supabase.table('approvals').delete().eq('id', approval_id).eq('user_id', user_id).execute()
        except Exception as e:
            raise Exception(f"Failed to delete approval: {e}")
    
    # ==================== Letterhead Files Management ====================
    
    def save_letterhead_file(self, user_id: int, file_data: dict) -> int:
        """
        Save a letterhead file entry
        
        Args:
            user_id: User ID who uploaded the file
            file_data: Dictionary with:
                - category: 'Estimate' or 'Invoice'
                - title: Display title for the file
                - file_name: Original filename
                - file_path: Path in Supabase Storage
                - uploaded_by_username: Username of uploader
                
        Returns:
            File ID
        """
        try:
            file_record = {
                'user_id': user_id,
                'category': file_data.get('category'),
                'title': file_data.get('title'),
                'file_name': file_data.get('file_name'),
                'file_path': file_data.get('file_path'),
                'uploaded_by_username': file_data.get('uploaded_by_username')
            }
            
            print(f"[save_letterhead_file] Inserting record: {file_record}")
            result = self.supabase.table('letterhead_files').insert(file_record).execute()
            print(f"[save_letterhead_file] Insert result: {result.data}")
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            error_msg = str(e)
            print(f"[save_letterhead_file] Error: {error_msg}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to save letterhead file: {e}")
    
    def get_letterhead_files(self, category: str = None) -> List[Dict]:
        """
        Get all letterhead files, optionally filtered by category
        
        Args:
            category: 'Estimate' or 'Invoice' (optional, None for all)
            
        Returns:
            List of file dictionaries
        """
        try:
            query = self.supabase.table('letterhead_files').select('*')
            if category:
                query = query.eq('category', category)
            result = query.order('created_at', desc=True).execute()
            print(f"[get_letterhead_files] Query for category '{category}': Found {len(result.data) if result.data else 0} files")
            return result.data if result.data else []
        except Exception as e:
            error_msg = str(e)
            print(f"[get_letterhead_files] Error: {error_msg}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_letterhead_file(self, file_id: int, user_id: int = None):
        """
        Delete a letterhead file entry
        
        Args:
            file_id: ID of the file to delete
            user_id: Optional user ID for verification
        """
        try:
            query = self.supabase.table('letterhead_files').delete().eq('id', file_id)
            if user_id:
                query = query.eq('user_id', user_id)
            query.execute()
        except Exception as e:
            raise Exception(f"Failed to delete letterhead file: {e}")
    
    # ==================== WO Inspections Management ====================
    
    def save_wo_inspection(self, user_id: int, inspection_data: dict) -> int:
        """
        Save or update a WO inspection entry
        
        Args:
            user_id: User ID who owns the inspection
            inspection_data: Dictionary containing:
                - id (optional): For updates
                - inspection_type: Type of inspection (e.g., "Grass Cut", "Initial Secure")
                - work_order: Work order number
                - inspection_data: JSONB data for inspection details
                - status: Status of inspection (default: 'pending')
                
        Returns:
            Inspection ID
        """
        try:
            inspection_record = {
                'user_id': user_id,
                'inspection_type': inspection_data.get('inspection_type', ''),
                'work_order': inspection_data.get('work_order', ''),
                'inspection_data': json.dumps(inspection_data.get('inspection_data', {})),
                'status': inspection_data.get('status', 'pending')
            }
            
            if 'id' in inspection_data and inspection_data['id']:
                # Update existing
                inspection_record['updated_at'] = datetime.now().isoformat()
                self.supabase.table('wo_inspections').update(inspection_record).eq('id', inspection_data['id']).eq('user_id', user_id).execute()
                return inspection_data['id']
            else:
                # Insert new
                inspection_record['updated_at'] = datetime.now().isoformat()
                result = self.supabase.table('wo_inspections').insert(inspection_record).execute()
                return result.data[0]['id'] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to save WO inspection: {e}")
    
    def get_user_wo_inspections(self, user_id: int, inspection_type: Optional[str] = None) -> List[Dict]:
        """
        Get all WO inspections for a user, optionally filtered by type
        
        Args:
            user_id: User ID
            inspection_type: Optional filter by inspection type
            
        Returns:
            List of inspection dictionaries
        """
        try:
            query = self.supabase.table('wo_inspections').select('*').eq('user_id', user_id)
            if inspection_type:
                query = query.eq('inspection_type', inspection_type)
            result = query.order('created_at', desc=True).execute()
            if result.data:
                # Parse JSONB inspection_data back to dict
                for inspection in result.data:
                    if isinstance(inspection.get('inspection_data'), str):
                        try:
                            inspection['inspection_data'] = json.loads(inspection['inspection_data'])
                        except:
                            inspection['inspection_data'] = {}
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user WO inspections: {e}")
            return []
    
    def get_wo_inspection_by_wo(self, user_id: int, work_order: str, inspection_type: Optional[str] = None) -> List[Dict]:
        """
        Get WO inspections by work order number
        
        Args:
            user_id: User ID
            work_order: Work order number
            inspection_type: Optional filter by inspection type
            
        Returns:
            List of inspection dictionaries
        """
        try:
            query = self.supabase.table('wo_inspections').select('*').eq('user_id', user_id).eq('work_order', work_order)
            if inspection_type:
                query = query.eq('inspection_type', inspection_type)
            result = query.order('created_at', desc=True).execute()
            if result.data:
                # Parse JSONB inspection_data back to dict
                for inspection in result.data:
                    if isinstance(inspection.get('inspection_data'), str):
                        try:
                            inspection['inspection_data'] = json.loads(inspection['inspection_data'])
                        except:
                            inspection['inspection_data'] = {}
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting WO inspection by work order: {e}")
            return []
    
    def delete_wo_inspection(self, inspection_id: int, user_id: int):
        """Delete a WO inspection entry"""
        try:
            self.supabase.table('wo_inspections').delete().eq('id', inspection_id).eq('user_id', user_id).execute()
        except Exception as e:
            raise Exception(f"Failed to delete WO inspection: {e}")
    
    # ==================== WO Inspection Checklist Items Management ====================
    
    def save_checklist_items(self, inspection_type: str, items: List[str]):
        """
        Save or update checklist items for an inspection type
        
        Args:
            inspection_type: Type of inspection (e.g., "Winterization")
            items: List of checklist item text strings
            
        Returns:
            Number of items saved
        """
        try:
            # Delete existing items for this type
            self.supabase.table('wo_inspection_checklist_items').delete().eq('inspection_type', inspection_type).execute()
            
            # Insert new items
            items_to_insert = [
                {'inspection_type': inspection_type, 'item_order': idx, 'item_text': item}
                for idx, item in enumerate(items)
            ]
            
            if items_to_insert:
                self.supabase.table('wo_inspection_checklist_items').insert(items_to_insert).execute()
            
            return len(items)
        except Exception as e:
            raise Exception(f"Failed to save checklist items: {e}")
    
    def get_checklist_items(self, inspection_type: str) -> List[str]:
        """
        Get checklist items for an inspection type
        
        Args:
            inspection_type: Type of inspection
            
        Returns:
            List of checklist item text strings, ordered by item_order
        """
        try:
            print(f"\n[DEBUG] Querying database for inspection_type: '{inspection_type}'")
            
            # First, let's check what inspection types exist (with error handling)
            try:
                all_types_result = self.supabase.table('wo_inspection_checklist_items')\
                    .select('inspection_type')\
                    .execute()
                
                if all_types_result.data:
                    unique_types = set(item['inspection_type'] for item in all_types_result.data)
                    print(f"[DEBUG] Found inspection types in DB: {sorted(unique_types)}")
                else:
                    print(f"[DEBUG] No data in wo_inspection_checklist_items table")
            except Exception as e:
                print(f"[DEBUG] Error checking all types: {e}")
            
            # Try multiple query approaches
            result = None
            
            # Approach 1: Standard query
            try:
                result = self.supabase.table('wo_inspection_checklist_items')\
                    .select('item_text, item_order')\
                    .eq('inspection_type', inspection_type)\
                    .order('item_order', desc=False)\
                    .execute()
                print(f"[DEBUG] Standard query returned {len(result.data) if result.data else 0} rows")
            except Exception as e1:
                print(f"[DEBUG] Standard query failed: {e1}")
                
                # Approach 2: Try selecting all columns
                try:
                    result = self.supabase.table('wo_inspection_checklist_items')\
                        .select('*')\
                        .eq('inspection_type', inspection_type)\
                        .order('item_order', desc=False)\
                        .execute()
                    print(f"[DEBUG] All-columns query returned {len(result.data) if result.data else 0} rows")
                except Exception as e2:
                    print(f"[DEBUG] All-columns query also failed: {e2}")
                    
                    # Approach 3: Try without order
                    try:
                        result = self.supabase.table('wo_inspection_checklist_items')\
                            .select('item_text, item_order')\
                            .eq('inspection_type', inspection_type)\
                            .execute()
                        print(f"[DEBUG] No-order query returned {len(result.data) if result.data else 0} rows")
                    except Exception as e3:
                        print(f"[DEBUG] All query approaches failed. Last error: {e3}")
                        raise e3
            
            if result and result.data:
                # Sort by item_order to ensure correct order
                sorted_data = sorted(result.data, key=lambda x: x.get('item_order', 0))
                items = [item['item_text'] for item in sorted_data]
                
                print(f"[DEBUG] ✅ Successfully loaded {len(items)} checklist items for '{inspection_type}'")
                if items:
                    print(f"[DEBUG] First item: {items[0][:60]}...")
                    print(f"[DEBUG] Last item: {items[-1][:60]}...")
                
                return items
            else:
                print(f"[DEBUG] ❌ No checklist items found in database for '{inspection_type}'")
                # Try one more time with case-insensitive approach
                try:
                    all_items_result = self.supabase.table('wo_inspection_checklist_items')\
                        .select('inspection_type, item_text, item_order')\
                        .execute()
                    
                    if all_items_result.data:
                        print(f"[DEBUG] Found {len(all_items_result.data)} total rows in table")
                        matching = [item for item in all_items_result.data if item.get('inspection_type', '').lower() == inspection_type.lower()]
                        if matching:
                            print(f"[DEBUG] Found {len(matching)} matching items (case-insensitive)")
                            sorted_matching = sorted(matching, key=lambda x: x.get('item_order', 0))
                            items = [item['item_text'] for item in sorted_matching]
                            return items
                except Exception as e:
                    print(f"[DEBUG] Case-insensitive fallback also failed: {e}")
                
                return []
        except Exception as e:
            print(f"[ERROR] Error getting checklist items for '{inspection_type}': {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_checklist_items(self) -> Dict[str, List[str]]:
        """
        Get all checklist items grouped by inspection type
        
        Returns:
            Dictionary mapping inspection_type to list of items
        """
        try:
            result = self.supabase.table('wo_inspection_checklist_items')\
                .select('*')\
                .order('inspection_type', desc=False)\
                .order('item_order', desc=False)\
                .execute()
            
            checklist_dict = {}
            if result.data:
                for item in result.data:
                    inspection_type = item['inspection_type']
                    if inspection_type not in checklist_dict:
                        checklist_dict[inspection_type] = []
                    checklist_dict[inspection_type].append(item['item_text'])
            
            return checklist_dict
        except Exception as e:
            print(f"Error getting all checklist items: {e}")
            return {}
    
    # ==================== Special Contractor Prices ====================
    
    def create_special_contractor(self, contractor_name: str, user_id: int) -> Dict:
        """Create a new special contractor entry."""
        try:
            result = self.supabase.table('special_contractors').insert({
                'contractor_name': contractor_name,
                'user_id': user_id,
                'updated_by': user_id,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error creating special contractor: {e}")
            raise e
    
    def get_special_contractor(self, contractor_name: str) -> Optional[Dict]:
        """Get a special contractor by name."""
        try:
            result = self.supabase.table('special_contractors')\
                .select('*')\
                .eq('contractor_name', contractor_name)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting special contractor: {e}")
            return None
    
    def get_all_special_contractors(self) -> List[Dict]:
        """Get all special contractors."""
        try:
            result = self.supabase.table('special_contractors')\
                .select('*')\
                .order('contractor_name', desc=False)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting all special contractors: {e}")
            return []
    
    def add_contractor_line_item(self, contractor_id: int, line_item: str, price: float, user_id: int) -> Dict:
        """Add a line item to a contractor."""
        try:
            result = self.supabase.table('contractor_line_items').insert({
                'contractor_id': contractor_id,
                'line_item': line_item,
                'price': price,
                'user_id': user_id
            }).execute()
            
            # Update contractor's updated_by and updated_at
            self.supabase.table('special_contractors')\
                .update({
                    'updated_by': user_id,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', contractor_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error adding contractor line item: {e}")
            raise e
    
    def get_contractor_line_items(self, contractor_id: int) -> List[Dict]:
        """Get all line items for a contractor."""
        try:
            result = self.supabase.table('contractor_line_items')\
                .select('*')\
                .eq('contractor_id', contractor_id)\
                .order('id', desc=False)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting contractor line items: {e}")
            return []
    
    def update_contractor_line_item(self, item_id: int, line_item: str, price: float, user_id: int) -> bool:
        """Update a contractor line item."""
        try:
            # Get contractor_id from line item
            item_result = self.supabase.table('contractor_line_items')\
                .select('contractor_id')\
                .eq('id', item_id)\
                .execute()
            
            if not item_result.data:
                return False
            
            contractor_id = item_result.data[0]['contractor_id']
            
            # Update line item
            self.supabase.table('contractor_line_items')\
                .update({
                    'line_item': line_item,
                    'price': price
                })\
                .eq('id', item_id)\
                .execute()
            
            # Update contractor's updated_by and updated_at
            self.supabase.table('special_contractors')\
                .update({
                    'updated_by': user_id,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', contractor_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"Error updating contractor line item: {e}")
            return False
    
    def delete_contractor_line_item(self, item_id: int, user_id: int) -> bool:
        """Delete a contractor line item."""
        try:
            # Get contractor_id from line item
            item_result = self.supabase.table('contractor_line_items')\
                .select('contractor_id')\
                .eq('id', item_id)\
                .execute()
            
            if not item_result.data:
                return False
            
            contractor_id = item_result.data[0]['contractor_id']
            
            # Delete line item
            self.supabase.table('contractor_line_items')\
                .delete()\
                .eq('id', item_id)\
                .execute()
            
            # Update contractor's updated_by and updated_at
            self.supabase.table('special_contractors')\
                .update({
                    'updated_by': user_id,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', contractor_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"Error deleting contractor line item: {e}")
            return False
    
    def delete_special_contractor(self, contractor_id: int) -> bool:
        """Delete a special contractor and all its line items."""
        try:
            # Delete all line items first
            self.supabase.table('contractor_line_items')\
                .delete()\
                .eq('contractor_id', contractor_id)\
                .execute()
            
            # Delete contractor
            self.supabase.table('special_contractors')\
                .delete()\
                .eq('id', contractor_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"Error deleting special contractor: {e}")
            return False
    
    def get_contractor_with_items(self, contractor_id: int) -> Optional[Dict]:
        """Get a contractor with all its line items."""
        try:
            contractor_result = self.supabase.table('special_contractors')\
                .select('*')\
                .eq('id', contractor_id)\
                .execute()
            
            if not contractor_result.data:
                return None
            
            contractor = contractor_result.data[0]
            line_items = self.get_contractor_line_items(contractor_id)
            contractor['line_items'] = line_items
            
            return contractor
        except Exception as e:
            print(f"Error getting contractor with items: {e}")
            return None
    
    # ==================== Password Utilities ====================
    
    # Password hashing methods - no longer used, passwords stored in plain text
    def _hash_password(self, password: str) -> str:
        """No longer used - passwords stored in plain text"""
        return password
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """No longer used - plain text comparison is done directly"""
        return password == password_hash

