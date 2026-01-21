# letterhead_bid_module.py
import tkinter as tk
from tkinter import messagebox, filedialog
import os
from datetime import datetime
import tempfile
import shutil
import json
import threading
from theme_manager import theme_manager

try:
    from database_online import OnlineDatabaseManager
except ImportError:
    OnlineDatabaseManager = None

class LetterheadBidModule:
    def __init__(self, root, username=None, user_id=None):
        self.root = root
        # Only set title if root is a Toplevel or Tk window
        if hasattr(root, 'title'):
            self.root.title("Letterheads")
        self.username = username
        self.user_id = user_id
        
        # Use theme manager for colors
        self.colors = theme_manager.get_current_colors()
        self.root.configure(bg=self.colors['background'])
        
        # Initialize database
        try:
            self.db = OnlineDatabaseManager() if OnlineDatabaseManager else None
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            self.db = None
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
        
        # Local cache file path
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.cache_file = os.path.join(self.app_data_dir, "letterhead-files.json")
        
        # Setup UI first for fast opening
        self.setup_ui()
        
        # Load files asynchronously after UI is ready (non-blocking)
        self.root.after(10, self.load_files_async)
    
    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        self.root.configure(bg=self.colors['background'])
        # Rebuild UI with new theme
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
        self.load_files_async()
    
    def setup_ui(self):
        """Create main user interface with Estimate and Invoice sections"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(main_container, bg=self.colors['background'])
        title_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(title_frame, text="📝 Letterheads", 
                font=("Segoe UI", 24, "bold"),
                bg=self.colors['background'],
                fg=self.colors.get('text_primary', '#1F2937')).pack(side='left')
        
        if self.username:
            tk.Label(title_frame, text=f"User: {self.username}", 
                    font=("Segoe UI", 12),
                    bg=self.colors['background'],
                    fg=self.colors.get('text_secondary', '#6B7280')).pack(side='right', padx=10)
        
        # Create two sections side by side - full height
        sections_frame = tk.Frame(main_container, bg=self.colors['background'])
        sections_frame.pack(fill='both', expand=True)
        sections_frame.grid_columnconfigure(0, weight=1)
        sections_frame.grid_columnconfigure(1, weight=1)
        sections_frame.grid_rowconfigure(0, weight=1)  # Make rows expand to fill height
        
        # Estimate Section
        self.estimate_frame = self.create_section(sections_frame, "Estimate", 0)
        
        # Invoice Section
        self.invoice_frame = self.create_section(sections_frame, "Invoice", 1)
    
    def create_section(self, parent, category, col):
        """Create a section (Estimate or Invoice) with upload button and file grid"""
        card_bg = self.colors.get('white', '#FFFFFF')
        card_border = self.colors.get('gray_light', '#E5E7EB')
        
        # Section card - expand to fill available height
        section_card = tk.Frame(parent, bg=card_bg, 
                               relief='solid', bd=1,
                               highlightbackground=card_border, highlightthickness=1)
        section_card.grid(row=0, column=col, sticky='nsew', padx=10, pady=10)
        section_card.grid_rowconfigure(1, weight=1)  # Make files container expand
        
        # Section header
        header_frame = tk.Frame(section_card, bg=self.colors['primary_blue'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(header_frame, text=category, 
                font=("Segoe UI", 18, "bold"),
                bg=self.colors['primary_blue'],
                fg=self.colors.get('button_text', 'white')).pack(side='left', padx=15, pady=10)
        
        # Upload button
        upload_btn = tk.Button(header_frame, text="+ Upload File",
                              font=("Segoe UI", 10, "bold"),
                              bg=self.colors.get('success', '#10B981'),
                              fg='white',
                              relief='flat', cursor='hand2',
                              padx=15, pady=8,
                              command=lambda: self.upload_file(category))
        upload_btn.pack(side='right', padx=15, pady=10)
        
        # Files container with scrollbar
        files_container = tk.Frame(section_card, bg=card_bg)
        files_container.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Canvas and scrollbar
        canvas = tk.Canvas(files_container, bg=card_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(files_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=card_bg)
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # Store references
        setattr(self, f'{category.lower()}_canvas', canvas)
        setattr(self, f'{category.lower()}_scrollable_frame', scrollable_frame)
        
        # Mouse wheel binding
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        return section_card
    
    def upload_file(self, category):
        """Upload a Word file for the specified category"""
        # Select file
        file_path = filedialog.askopenfilename(
            title=f"Select Word File for {category}",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Check if it's a .docx file
        if not file_path.lower().endswith('.docx'):
            messagebox.showwarning("Invalid File", "Please select a Word document (.docx file)")
            return
        
        # Get title from user
        # Get the actual window (Toplevel or Tk root) for dialog parent
        parent_window = self.root
        if not isinstance(parent_window, tk.Toplevel) and not isinstance(parent_window, tk.Tk):
            # If it's a Frame, get its root window
            parent_window = parent_window.winfo_toplevel()
        
        dialog = tk.Toplevel(parent_window)
        dialog.title(f"Upload {category} File")
        dialog.configure(bg=self.colors['background'])
        dialog.geometry("400x150")
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 150) // 2
        dialog.geometry(f"400x150+{x}+{y}")
        
        container = tk.Frame(dialog, bg=self.colors.get('white', '#FFFFFF'))
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Enter Title:", 
                font=("Segoe UI", 11, "bold"),
                bg=self.colors.get('white', '#FFFFFF')).pack(anchor='w', pady=(0, 5))
        
        title_var = tk.StringVar()
        title_entry = tk.Entry(container, textvariable=title_var,
                              font=("Segoe UI", 11),
                              width=40)
        title_entry.pack(fill='x', pady=(0, 15))
        title_entry.focus()
        
        def save_file():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Validation", "Please enter a title")
                return
            
            try:
                # Upload to Supabase Storage
                file_name = os.path.basename(file_path)
                storage_path = f"letterhead-files/{category.lower()}/{self.user_id if self.user_id else 'anonymous'}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
                
                # Read file content
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Upload to storage
                if self.db and self.db.supabase:
                    try:
                        # Check if bucket exists, create if not
                        bucket_name = 'letterhead-files'
                        try:
                            self.db.supabase.storage.from_(bucket_name).list()
                            print(f"Bucket '{bucket_name}' exists")
                        except Exception:
                            # Bucket doesn't exist, try to create it
                            try:
                                self.db.supabase.storage.create_bucket(bucket_name, {'public': True})
                                print(f"Created bucket '{bucket_name}'")
                            except Exception as bucket_error:
                                print(f"Could not create bucket: {bucket_error}")
                                raise Exception(f"Storage bucket does not exist and could not be created. Please create it in Supabase Dashboard.")
                        
                        # Upload file using correct syntax (match photo upload pattern)
                        print(f"Uploading file to: {storage_path}")
                        upload_result = self.db.supabase.storage.from_(bucket_name).upload(
                            path=storage_path,
                            file=file_content,
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                        )
                        print(f"Upload successful: {upload_result}")
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Error uploading to storage: {error_msg}")
                        # Fallback: save locally
                        local_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter", "letterhead-files", category.lower())
                        os.makedirs(local_dir, exist_ok=True)
                        local_path = os.path.join(local_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}")
                        shutil.copy2(file_path, local_path)
                        storage_path = local_path
                        print(f"Saved locally to: {local_path}")
                
                # Save to database (or locally if no user_id/db)
                file_data = {
                    'category': category,
                    'title': title,
                    'file_name': file_name,
                    'file_path': storage_path,
                    'uploaded_by_username': self.username or 'Unknown'
                }
                
                if self.db and self.user_id:
                    print(f"Saving file metadata to database: {file_data}")
                    file_id = self.db.save_letterhead_file(self.user_id, file_data)
                    print(f"File saved with ID: {file_id}")
                else:
                    # Save to local cache if database/user_id not available
                    all_files = self.load_from_cache()
                    file_data['id'] = len(all_files) + 1
                    file_data['created_at'] = datetime.now().isoformat()
                    all_files.append(file_data)
                    self.save_to_cache(all_files)
                    print(f"File saved locally (database not available)")
                
                # If database upload succeeded, refresh from database to update cache
                if self.db and self.user_id:
                    # Cache will be updated when reloading
                    pass
                
                dialog.destroy()
                messagebox.showinfo("Success", f"File uploaded successfully!")
                # Reload files (will update cache automatically)
                self.load_files_async()
                
            except Exception as e:
                error_msg = str(e)
                print(f"Upload error details: {error_msg}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to upload file:\n\n{error_msg}\n\nCheck console for details.")
        
        button_frame = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(fill='x')
        
        tk.Button(button_frame, text="Upload",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors['primary_blue'],
                 fg='white',
                 relief='flat', cursor='hand2',
                 padx=20, pady=8,
                 command=save_file).pack(side='right', padx=(10, 0))
        
        tk.Button(button_frame, text="Cancel",
                 font=("Segoe UI", 10),
                 bg=self.colors.get('text_secondary', '#6B7280'),
                 fg='white',
                 relief='flat', cursor='hand2',
                 padx=20, pady=8,
                 command=dialog.destroy).pack(side='right')
        
        title_entry.bind('<Return>', lambda e: save_file())
    
    def download_file(self, file_data):
        """Download a file"""
        try:
            file_path = file_data.get('file_path')
            file_name = file_data.get('file_name', 'document.docx')
            
            # Ask where to save
            save_path = filedialog.asksaveasfilename(
                title="Save File As",
                defaultextension=".docx",
                filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
                initialfile=file_name
            )
            
            if not save_path:
                return
            
            # Download from Supabase Storage or local
            if file_path.startswith('letterhead-files/'):
                # Download from Supabase Storage
                if self.db and self.db.supabase:
                    try:
                        file_content = self.db.supabase.storage.from_('letterhead-files').download(file_path)
                        with open(save_path, 'wb') as f:
                            f.write(file_content)
                        messagebox.showinfo("Success", f"File downloaded to:\n{save_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to download file: {e}")
            else:
                # Copy from local path
                if os.path.exists(file_path):
                    shutil.copy2(file_path, save_path)
                    messagebox.showinfo("Success", f"File downloaded to:\n{save_path}")
                else:
                    messagebox.showerror("Error", "File not found")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {e}")
    
    def delete_file(self, file_data):
        """Delete a file"""
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete this file?\n\nTitle: {file_data.get('title')}\nFile: {file_data.get('file_name')}"):
            return
        
        try:
            file_id = file_data.get('id')
            file_path = file_data.get('file_path')
            
            # Delete from database
            if self.db and file_id:
                self.db.delete_letterhead_file(file_id, self.user_id)
            
            # Delete from storage
            if file_path.startswith('letterhead-files/') and self.db and self.db.supabase:
                try:
                    self.db.supabase.storage.from_('letterhead-files').remove([file_path])
                except Exception as e:
                    print(f"Error deleting from storage: {e}")
            elif os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting local file: {e}")
            
            messagebox.showinfo("Success", "File deleted successfully!")
            # Reload files (will update cache automatically)
            self.load_files_async()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {e}")
    
    def create_file_card(self, parent, file_data):
        """Create a square card for a file with Word icon"""
        card_bg = self.colors.get('white', '#FFFFFF')
        card_border = self.colors.get('gray_light', '#E5E7EB')
        
        # Card frame - taller to accommodate larger download button
        card = tk.Frame(parent, bg=card_bg,
                        relief='solid', bd=1,
                        highlightbackground=card_border, highlightthickness=1,
                        width=200, height=250)
        card.pack(side='left', padx=10, pady=10, fill='none', anchor='nw')
        card.pack_propagate(False)
        
        # Word icon (📄 emoji or text)
        icon_frame = tk.Frame(card, bg=card_bg)
        icon_frame.pack(fill='x', pady=(15, 5))
        
        tk.Label(icon_frame, text="📄",
                font=("Segoe UI", 48),
                bg=card_bg).pack()
        
        # Title (truncated if too long)
        title = file_data.get('title', 'Untitled')
        if len(title) > 20:
            title = title[:17] + "..."
        
        title_label = tk.Label(card, text=title,
                               font=("Segoe UI", 11, "bold"),
                               bg=card_bg,
                               fg=self.colors.get('text_primary', '#1F2937'),
                               wraplength=180,
                               justify='center')
        title_label.pack(pady=(0, 5))
        
        # Uploader username
        uploader = file_data.get('uploaded_by_username', 'Unknown')
        tk.Label(card, text=f"By: {uploader}",
                font=("Segoe UI", 9),
                bg=card_bg,
                fg=self.colors.get('text_secondary', '#6B7280')).pack(pady=(0, 10))
        
        # Buttons frame
        buttons_frame = tk.Frame(card, bg=card_bg)
        buttons_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Download button - large and highly visible
        download_btn = tk.Button(buttons_frame, text="⬇️ Download",
                                font=("Segoe UI", 12, "bold"),
                                bg=self.colors['primary_blue'],
                                fg='white',
                                relief='flat', cursor='hand2',
                                padx=15, pady=10,
                                command=lambda: self.download_file(file_data))
        download_btn.pack(fill='x', expand=True)
        
        # Delete button (small, in corner)
        delete_btn = tk.Button(card, text="✕",
                              font=("Segoe UI", 8, "bold"),
                              bg='#DC3545',
                              fg='white',
                              relief='flat', cursor='hand2',
                              width=2, height=1,
                              command=lambda: self.delete_file(file_data))
        delete_btn.place(x=180, y=5)
    
    def load_files_async(self):
        """Load files asynchronously to prevent UI blocking"""
        # Show loading message
        self.show_loading_message()
        
        def load_in_thread():
            estimate_files = []
            invoice_files = []
            
            # Try to load from database first
            if self.db:
                try:
                    print("Loading letterhead files from database...")
                    # Load all files at once, then filter
                    all_files = self.db.get_letterhead_files(None)  # None = all categories
                    if all_files:
                        estimate_files = [f for f in all_files if f.get('category') == 'Estimate']
                        invoice_files = [f for f in all_files if f.get('category') == 'Invoice']
                        print(f"Found {len(estimate_files)} Estimate and {len(invoice_files)} Invoice files in database")
                        
                        # Save to cache after successful load
                        self.save_to_cache(all_files)
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error loading files from database: {error_msg}")
                    # Fall back to cache
                    all_files = self.load_from_cache()
                    if all_files:
                        estimate_files = [f for f in all_files if f.get('category') == 'Estimate']
                        invoice_files = [f for f in all_files if f.get('category') == 'Invoice']
                        print(f"Loaded {len(estimate_files)} Estimate and {len(invoice_files)} Invoice files from cache (offline mode)")
            
            # If no database, try local cache
            if not estimate_files and not invoice_files:
                all_files = self.load_from_cache()
                if all_files:
                    estimate_files = [f for f in all_files if f.get('category') == 'Estimate']
                    invoice_files = [f for f in all_files if f.get('category') == 'Invoice']
                    print(f"Loaded {len(estimate_files)} Estimate and {len(invoice_files)} Invoice files from local cache")
            
            # Update UI in main thread
            def update_ui():
                self.hide_loading_message()
                self.display_files(estimate_files, invoice_files)
            
            self.root.after(0, update_ui)
        
        # Start loading in background thread
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def show_loading_message(self):
        """Show loading message in both sections"""
        loading_text = "Loading files..."
        if hasattr(self, 'estimate_scrollable_frame'):
            loading_label = tk.Label(self.estimate_scrollable_frame, 
                                    text=loading_text,
                                    font=("Segoe UI", 12),
                                    bg=self.colors.get('white', '#FFFFFF'),
                                    fg=self.colors.get('text_secondary', '#6B7280'))
            loading_label.pack(pady=20)
            self.estimate_loading_label = loading_label
        
        if hasattr(self, 'invoice_scrollable_frame'):
            loading_label = tk.Label(self.invoice_scrollable_frame, 
                                    text=loading_text,
                                    font=("Segoe UI", 12),
                                    bg=self.colors.get('white', '#FFFFFF'),
                                    fg=self.colors.get('text_secondary', '#6B7280'))
            loading_label.pack(pady=20)
            self.invoice_loading_label = loading_label
    
    def hide_loading_message(self):
        """Hide loading message"""
        if hasattr(self, 'estimate_loading_label'):
            try:
                self.estimate_loading_label.destroy()
            except:
                pass
        if hasattr(self, 'invoice_loading_label'):
            try:
                self.invoice_loading_label.destroy()
            except:
                pass
    
    def display_files(self, estimate_files, invoice_files):
        """Display files in the UI"""
        # Clear existing files
        if hasattr(self, 'estimate_scrollable_frame'):
            for widget in self.estimate_scrollable_frame.winfo_children():
                widget.destroy()
        
        if hasattr(self, 'invoice_scrollable_frame'):
            for widget in self.invoice_scrollable_frame.winfo_children():
                widget.destroy()
        
        # Display Estimate files
        if hasattr(self, 'estimate_scrollable_frame'):
            if estimate_files:
                for file_data in estimate_files:
                    self.create_file_card(self.estimate_scrollable_frame, file_data)
            else:
                empty_label = tk.Label(self.estimate_scrollable_frame,
                                      text="No Estimate files yet.\nClick '+ Upload File' to add one.",
                                      font=("Segoe UI", 11),
                                      bg=self.colors.get('white', '#FFFFFF'),
                                      fg=self.colors.get('text_secondary', '#6B7280'),
                                      justify='center')
                empty_label.pack(pady=20)
        
        # Display Invoice files
        if hasattr(self, 'invoice_scrollable_frame'):
            if invoice_files:
                for file_data in invoice_files:
                    self.create_file_card(self.invoice_scrollable_frame, file_data)
            else:
                empty_label = tk.Label(self.invoice_scrollable_frame,
                                      text="No Invoice files yet.\nClick '+ Upload File' to add one.",
                                      font=("Segoe UI", 11),
                                      bg=self.colors.get('white', '#FFFFFF'),
                                      fg=self.colors.get('text_secondary', '#6B7280'),
                                      justify='center')
                empty_label.pack(pady=20)
    
    def save_to_cache(self, files):
        """Save files to local cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(files, f, indent=2)
            print(f"Saved {len(files)} files to cache")
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def load_from_cache(self):
        """Load files from local cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    files = json.load(f)
                    print(f"Loaded {len(files)} files from cache")
                    return files
        except Exception as e:
            print(f"Error loading from cache: {e}")
        return []
    
    def load_files(self):
        """Legacy method for theme changes - now calls async version"""
        self.load_files_async()

if __name__ == "__main__":
    root = tk.Tk()
    app = LetterheadBidModule(root, username="TestUser", user_id=1)
    root.mainloop()
