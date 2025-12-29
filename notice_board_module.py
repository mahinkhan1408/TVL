# notice_board_module.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import os
import json
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
try:
    from database_online import OnlineDatabaseManager
except ImportError:
    OnlineDatabaseManager = None

class NoticeBoardModule:
    def __init__(self, parent_frame, username=None, user_id=None, colors=None):
        self.parent_frame = parent_frame
        self.username = username
        self.user_id = user_id
        self.colors = colors or {
            'primary_blue': '#1e3a5f',
            'light_blue': '#3498db',
            'background': '#f8f9fa',
            'white': '#ffffff',
            'gray_light': '#e9ecef',
            'gray_medium': '#6c757d',
            'gray_dark': '#495057',
        }
        
        # Initialize database
        try:
            self.db = OnlineDatabaseManager() if OnlineDatabaseManager else None
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            self.db = None
        
        # Categories
        self.categories = ['ALL', 'Processing', 'Client Team', 'Accounting', 'Important']
        self.selected_category = tk.StringVar(value='ALL')
        
        # Track viewed notices (set of notice IDs that have been viewed)
        if not hasattr(self, 'viewed_notices'):
            self.viewed_notices = set()
        
        # Load viewed notices from local storage
        self.load_viewed_notices()
        
        # Top section: Categories and Add Notice button
        self.create_header()
        
        # Main content area: 3-column grid for notices
        self.create_notice_grid()
        
        # Load notices
        self.load_notices()
        
        # Start auto-refresh timer (20 minutes = 1200000 milliseconds)
        self.auto_refresh_interval = 20 * 60 * 1000  # 20 minutes in milliseconds
        self.start_auto_refresh()
    
    def create_header(self):
        """Create header with category filters and add notice button"""
        header_frame = tk.Frame(self.parent_frame, bg=self.colors['background'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Categories section
        categories_label = tk.Label(header_frame, text="Categories:", 
                                    font=("Arial", 12, "bold"), 
                                    bg=self.colors['background'], 
                                    fg=self.colors['gray_dark'])
        categories_label.pack(side='left', padx=(0, 10))
        
        # Category buttons
        categories_frame = tk.Frame(header_frame, bg=self.colors['background'])
        categories_frame.pack(side='left', fill='x', expand=True)
        
        for category in self.categories:
            btn = tk.Button(categories_frame, text=category,
                          font=("Arial", 10),
                          bg=self.colors['primary_blue'] if category == 'ALL' else self.colors['gray_light'],
                          fg='white' if category == 'ALL' else self.colors['gray_dark'],
                          relief='flat',
                          cursor='hand2',
                          padx=15, pady=8,
                          command=lambda c=category: self.filter_by_category(c))
            btn.pack(side='left', padx=5)
            setattr(self, f'category_btn_{category}', btn)
        
        # Add Notice button
        add_btn = tk.Button(header_frame, text="+ Add Notice",
                           font=("Arial", 11, "bold"),
                           bg=self.colors['light_blue'],
                           fg='white',
                           relief='flat',
                           cursor='hand2',
                           padx=20, pady=8,
                           command=self.show_add_notice_dialog)
        add_btn.pack(side='right')
    
    def filter_by_category(self, category):
        """Filter notices by category"""
        self.selected_category.set(category)
        
        # Update button styles
        for cat in self.categories:
            btn = getattr(self, f'category_btn_{cat}', None)
            if btn:
                if cat == category:
                    btn.config(bg=self.colors['primary_blue'], fg='white')
                else:
                    btn.config(bg=self.colors['gray_light'], fg=self.colors['gray_dark'])
        
        # Reload notices with filter
        self.load_notices()
    
    def create_notice_grid(self):
        """Create scrollable 2-column grid for notices"""
        # Canvas and scrollbar
        canvas_frame = tk.Frame(self.parent_frame, bg=self.colors['background'])
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['background'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def load_viewed_notices(self):
        """Load viewed notices from local file"""
        try:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            os.makedirs(app_data_dir, exist_ok=True)
            viewed_file = os.path.join(app_data_dir, "viewed_notices.json")
            
            if os.path.exists(viewed_file):
                with open(viewed_file, 'r') as f:
                    data = json.load(f)
                    self.viewed_notices = set(data.get('viewed_notices', []))
        except Exception as e:
            print(f"Error loading viewed notices: {e}")
            self.viewed_notices = set()
    
    def save_viewed_notices(self):
        """Save viewed notices to local file"""
        try:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            os.makedirs(app_data_dir, exist_ok=True)
            viewed_file = os.path.join(app_data_dir, "viewed_notices.json")
            
            with open(viewed_file, 'w') as f:
                json.dump({'viewed_notices': list(self.viewed_notices)}, f)
        except Exception as e:
            print(f"Error saving viewed notices: {e}")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer to check for new notices every 20 minutes"""
        if hasattr(self.parent_frame, 'winfo_toplevel'):
            root = self.parent_frame.winfo_toplevel()
            if root:
                root.after(self.auto_refresh_interval, self.auto_refresh_callback)
    
    def auto_refresh_callback(self):
        """Callback for auto-refresh - reload notices and check for new ones"""
        try:
            # Get current viewed notice IDs from local storage
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            viewed_file = os.path.join(app_data_dir, "viewed_notices.json")
            old_viewed_ids = set()
            if os.path.exists(viewed_file):
                try:
                    with open(viewed_file, 'r') as f:
                        data = json.load(f)
                        old_viewed_ids = set(data.get('viewed_notices', []))
                except:
                    old_viewed_ids = set()
            
            # Reload notices from database
            if self.db:
                notices = self.db.get_all_notices()
                current_notice_ids = {n.get('id') for n in notices if n.get('id')}
                
                # Check if there are new notices (notices that exist in DB but not in viewed)
                new_notice_ids = current_notice_ids - old_viewed_ids
                if new_notice_ids:
                    # Save indicator that new notices exist (for dashboard card)
                    self.save_new_notices_indicator(True)
                    print(f"New notices detected: {new_notice_ids}")
                else:
                    # No new notices
                    self.save_new_notices_indicator(False)
                
                # Reload the display
                self.load_notices()
            
            # Schedule next refresh
            self.start_auto_refresh()
        except Exception as e:
            print(f"Error in auto-refresh: {e}")
            # Still schedule next refresh even on error
            self.start_auto_refresh()
    
    def save_new_notices_indicator(self, has_new):
        """Save indicator that new notices exist (for dashboard card)"""
        try:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            os.makedirs(app_data_dir, exist_ok=True)
            indicator_file = os.path.join(app_data_dir, "new_notices_indicator.json")
            
            with open(indicator_file, 'w') as f:
                json.dump({'has_new_notices': has_new}, f)
        except Exception as e:
            print(f"Error saving new notices indicator: {e}")
    
    @staticmethod
    def check_for_new_notices():
        """Static method to check if there are new notices (for dashboard card)"""
        try:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            indicator_file = os.path.join(app_data_dir, "new_notices_indicator.json")
            
            if os.path.exists(indicator_file):
                with open(indicator_file, 'r') as f:
                    data = json.load(f)
                    return data.get('has_new_notices', False)
        except Exception as e:
            print(f"Error checking new notices indicator: {e}")
        return False
    
    @staticmethod
    def clear_new_notices_indicator():
        """Clear the new notices indicator (called when user views notice board)"""
        try:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
            indicator_file = os.path.join(app_data_dir, "new_notices_indicator.json")
            
            with open(indicator_file, 'w') as f:
                json.dump({'has_new_notices': False}, f)
        except Exception as e:
            print(f"Error clearing new notices indicator: {e}")
    
    def load_notices(self):
        """Load notices from database"""
        # Clear existing notices
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.db:
            tk.Label(self.scrollable_frame, text="Database not available", 
                    font=("Arial", 12), bg=self.colors['background'], 
                    fg=self.colors['gray_medium']).pack(pady=20)
            return
        
        try:
            notices = self.db.get_all_notices()
            
            # Filter by category
            category_filter = self.selected_category.get()
            if category_filter != 'ALL':
                notices = [n for n in notices if n.get('category') == category_filter]
            
            if not notices:
                tk.Label(self.scrollable_frame, text="No notices available", 
                        font=("Arial", 12), bg=self.colors['background'], 
                        fg=self.colors['gray_medium']).pack(pady=20)
                return
            
            # Create 3-column grid
            row = 0
            col = 0
            max_cols = 3
            
            for notice in notices:
                self.display_notice_card(notice, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load notices: {e}")
            tk.Label(self.scrollable_frame, text=f"Error loading notices: {e}", 
                    font=("Arial", 12), bg=self.colors['background'], 
                    fg='red').pack(pady=20)
    
    def display_notice_card(self, notice, row, col):
        """Display a notice card in the grid"""
        # Card frame (reduced width by 40%, increased height by 50%)
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=notice.get('card_color', '#ffffff'),
                             relief='solid',
                             bd=1,
                             padx=15,  # Reduced from 25 to 15 (40% reduction)
                             pady=27)  # Increased pady from 18 to 27 (50% increase)
        card_frame.grid(row=row, column=col, padx=7, pady=12, sticky='nsew')  # Reduced from 12 to 7 (40% reduction)
        
        # Configure grid weights for equal column widths (3 columns)
        self.scrollable_frame.grid_columnconfigure(0, weight=1, uniform='col')
        self.scrollable_frame.grid_columnconfigure(1, weight=1, uniform='col')
        self.scrollable_frame.grid_columnconfigure(2, weight=1, uniform='col')
        
        # Get notice ID for "New" badge
        notice_id = notice.get('id')
        is_new = notice_id not in self.viewed_notices
        
        # Top frame for title and "New" badge
        title_container = tk.Frame(card_frame, bg=notice.get('card_color', '#ffffff'))
        title_container.pack(fill='x', pady=(0, 10))
        
        # "New" indicator badge (top right corner of card)
        if is_new:
            new_badge = tk.Label(title_container,
                                text="NEW",
                                font=("Arial", 8, "bold"),
                                bg='#dc3545',
                                fg='white',
                                relief='flat',
                                padx=6,
                                pady=2)
            new_badge.pack(side='right', anchor='ne')
            
            # Mark as viewed when card is displayed (user has seen it)
            self.viewed_notices.add(notice_id)
            self.save_viewed_notices()
        
        # Title (big, colored) - selectable text widget
        title_color = notice.get('title_color', '#000000')
        title_text_widget = tk.Text(title_container,
                                    font=("Arial", 16, "bold"),
                                    bg=notice.get('card_color', '#ffffff'),
                                    fg=title_color,
                                    wrap='word',
                                    relief='flat',
                                    borderwidth=0,
                                    highlightthickness=0,
                                    height=1,
                                    padx=0,
                                    pady=0)
        title_text_widget.insert('1.0', notice.get('title', 'Untitled'))
        title_text_widget.config(state='disabled', width=25)  # Read-only but selectable, reduced width
        title_text_widget.pack(fill='x', side='left', expand=True)
        
        # Message frame with limited height and "See More" functionality
        message_frame = tk.Frame(card_frame, bg=notice.get('card_color', '#ffffff'))
        message_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Limit message height - show first ~200 characters, then "See More"
        message_content = notice.get('content', '')
        max_chars = 200
        
        # Use a unique key for each notice to track expansion state (notice_id already defined above)
        if not hasattr(self, 'notice_expanded_states'):
            self.notice_expanded_states = {}
        
        if notice_id not in self.notice_expanded_states:
            self.notice_expanded_states[notice_id] = tk.BooleanVar(value=len(message_content) <= max_chars)
        
        is_expanded = self.notice_expanded_states[notice_id].get()
        
        def toggle_message():
            """Toggle between short and full message"""
            self.notice_expanded_states[notice_id].set(not self.notice_expanded_states[notice_id].get())
            # Re-display the card with toggled state
            self.load_notices()
        
        if is_expanded:
            # Show full message
            message_text = message_content
        else:
            # Show truncated message
            message_text = message_content[:max_chars] + "..."
        
        # Use Text widget for selectable/copyable text (increased height by 50%, reduced width by 40%)
        message_text_widget = tk.Text(message_frame,
                                     font=("Arial", 11),
                                     bg=notice.get('card_color', '#ffffff'),
                                     fg=self.colors['gray_dark'],
                                     wrap='word',
                                     relief='flat',
                                     borderwidth=0,
                                     highlightthickness=0,
                                     height=6,  # Increased height by ~50% (from ~4 lines to 6 lines)
                                     width=25,  # Reduced width by 40% (from ~42 to 25 characters)
                                     padx=0,
                                     pady=0)
        message_text_widget.insert('1.0', message_text)
        message_text_widget.config(state='disabled')  # Make read-only but selectable
        message_text_widget.pack(fill='both', expand=True, anchor='nw')
        
        # "See More" / "See Less" button if message is long
        if len(message_content) > max_chars:
            see_more_btn = tk.Button(message_frame,
                                    text="See Less" if is_expanded else "See More",
                                    font=("Arial", 9, "underline"),
                                    bg=notice.get('card_color', '#ffffff'),
                                    fg=self.colors['primary_blue'],
                                    relief='flat',
                                    cursor='hand2',
                                    command=toggle_message)
            see_more_btn.pack(anchor='w', pady=(5, 0))
        
        # Provider Name
        provider_name = 'Unknown'
        if notice.get('users'):
            if isinstance(notice['users'], dict):
                provider_name = notice['users'].get('username', 'Unknown')
            else:
                provider_name = 'Unknown'
        
        provider_frame = tk.Frame(card_frame, bg=notice.get('card_color', '#ffffff'))
        provider_frame.pack(fill='x', pady=(0, 5))
        
        provider_label = tk.Label(provider_frame,
                                 text=f"By: {provider_name}",
                                 font=("Arial", 10, "italic"),
                                 bg=notice.get('card_color', '#ffffff'),
                                 fg=self.colors['primary_blue'])
        provider_label.pack(side='left')
        
        # Category and time
        info_frame = tk.Frame(card_frame, bg=notice.get('card_color', '#ffffff'))
        info_frame.pack(fill='x')
        
        category_text = notice.get('category', 'ALL')
        category_label = tk.Label(info_frame,
                                 text=f"Category: {category_text}",
                                 font=("Arial", 9, "italic"),
                                 bg=notice.get('card_color', '#ffffff'),
                                 fg=self.colors['gray_medium'])
        category_label.pack(side='left')
        
        # Time (converted to EST)
        created_at = notice.get('created_at', '')
        if created_at:
            try:
                # Parse the UTC timestamp
                if 'T' in created_at:
                    # Remove timezone info if present and parse
                    dt_str = created_at.split('+')[0].split('Z')[0]
                    if '.' in dt_str:
                        dt_str = dt_str.split('.')[0]
                    dt_utc = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    dt_utc = datetime.strptime(created_at[:19], '%Y-%m-%d %H:%M:%S')
                
                # Convert to EST (Eastern Time)
                if PYTZ_AVAILABLE:
                    utc_tz = pytz.UTC
                    est_tz = pytz.timezone('US/Eastern')
                    dt_utc = utc_tz.localize(dt_utc)
                    dt_est = dt_utc.astimezone(est_tz)
                    # Format as "Dec 25, 2025 3:45 PM EST"
                    time_str = dt_est.strftime('%b %d, %Y %I:%M %p EST')
                else:
                    # Fallback: calculate EST offset manually (UTC-5 or UTC-4 for DST)
                    # Simple approach: subtract 5 hours for EST
                    dt_est = dt_utc - timedelta(hours=5)
                    time_str = dt_est.strftime('%b %d, %Y %I:%M %p EST')
            except Exception as e:
                print(f"Error parsing date: {e}")
                time_str = created_at[:19] if len(created_at) >= 19 else created_at
        else:
            time_str = 'Unknown'
        
        time_label = tk.Label(info_frame,
                             text=time_str,
                             font=("Arial", 9, "italic"),
                             bg=notice.get('card_color', '#ffffff'),
                             fg=self.colors['gray_medium'])
        time_label.pack(side='right')
        
        # Edit and Delete buttons
        buttons_frame = tk.Frame(card_frame, bg=notice.get('card_color', '#ffffff'))
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        edit_btn = tk.Button(buttons_frame,
                            text="Edit",
                            font=("Arial", 9),
                            bg=self.colors['primary_blue'],
                            fg='white',
                            relief='flat',
                            cursor='hand2',
                            padx=10, pady=3,
                            command=lambda nid=notice.get('id'): self.edit_notice(nid, notice))
        edit_btn.pack(side='left', padx=(0, 5))
        
        delete_btn = tk.Button(buttons_frame,
                               text="Delete",
                               font=("Arial", 9),
                               bg='#dc3545',
                               fg='white',
                               relief='flat',
                               cursor='hand2',
                               padx=10, pady=3,
                               command=lambda nid=notice.get('id'): self.delete_notice(nid))
        delete_btn.pack(side='left')
    
    def edit_notice(self, notice_id, notice_data):
        """Edit an existing notice"""
        self.show_add_notice_dialog(notice_id, notice_data)
    
    def show_add_notice_dialog(self, notice_id=None, notice_data=None):
        """Show dialog to add or edit a notice"""
        if not self.user_id:
            messagebox.showerror("Error", "You must be logged in to add notices.")
            return
        
        is_editing = notice_id is not None
        
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Edit Notice" if is_editing else "Add Notice")
        dialog.geometry("550x700")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.parent_frame.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"550x700+{x}+{y}")
        
        # Title
        tk.Label(dialog, text="Edit Notice" if is_editing else "Add New Notice", 
                font=("Arial", 16, "bold"),
                bg=self.colors['background'],
                fg=self.colors['primary_blue']).pack(pady=20)
        
        # Title field
        tk.Label(dialog, text="Title:", 
                font=("Arial", 11, "bold"),
                bg=self.colors['background']).pack(anchor='w', padx=30, pady=(10, 5))
        
        title_entry = tk.Entry(dialog, font=("Arial", 12), width=50)
        title_entry.pack(padx=30, pady=(0, 15))
        title_entry.focus()
        
        # Pre-fill fields if editing
        if is_editing and notice_data:
            title_entry.insert(0, notice_data.get('title', ''))
        
        # Title Color and Category row
        title_color_category_frame = tk.Frame(dialog, bg=self.colors['background'])
        title_color_category_frame.pack(fill='x', padx=30, pady=(10, 15))
        
        # Title Color section
        title_color_left = tk.Frame(title_color_category_frame, bg=self.colors['background'])
        title_color_left.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        tk.Label(title_color_left, text="Title Color:", 
                font=("Arial", 11, "bold"),
                bg=self.colors['background']).pack(anchor='w', pady=(0, 5))
        
        title_color_var = tk.StringVar(value=notice_data.get('title_color', '#000000') if is_editing and notice_data else '#000000')
        title_color_frame = tk.Frame(title_color_left, bg=self.colors['background'])
        title_color_frame.pack(anchor='w')
        
        # Predefined color buttons for title
        color_options = [
            ('Black', '#000000'),
            ('Blue', '#1e3a5f'),
            ('Red', '#dc3545'),
            ('Green', '#28a745'),
            ('Orange', '#ff9800'),
            ('Purple', '#9c27b0'),
            ('Pink', '#e173a5'),
            ('Dark Gray', '#495057')
        ]
        
        for color_name, color_code in color_options:
            btn = tk.Button(title_color_frame, text="",
                           bg=color_code,
                           fg='white',
                           relief='solid',
                           bd=1,
                           width=3,
                           height=1,
                           cursor='hand2',
                           command=lambda c=color_code: title_color_var.set(c))
            btn.pack(side='left', padx=2)
        
        # Category section
        category_left = tk.Frame(title_color_category_frame, bg=self.colors['background'])
        category_left.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        tk.Label(category_left, text="Category:", 
                font=("Arial", 11, "bold"),
                bg=self.colors['background']).pack(anchor='w', pady=(0, 5))
        
        category_var = tk.StringVar(value=notice_data.get('category', 'ALL') if is_editing and notice_data else 'ALL')
        category_menu = tk.OptionMenu(category_left, category_var, *self.categories)
        category_menu.config(font=("Arial", 10), bg=self.colors['white'], width=20)
        category_menu.pack(anchor='w')
        
        # Message field
        tk.Label(dialog, text="Message:", 
                font=("Arial", 11, "bold"),
                bg=self.colors['background']).pack(anchor='w', padx=30, pady=(10, 5))
        
        message_text = tk.Text(dialog, font=("Arial", 11), width=50, height=8, wrap='word')
        message_text.pack(padx=30, pady=(0, 15))
        
        # Pre-fill message if editing
        if is_editing and notice_data:
            message_text.insert("1.0", notice_data.get('content', ''))
        
        # Card color
        tk.Label(dialog, text="Card Color:", 
                font=("Arial", 11, "bold"),
                bg=self.colors['background']).pack(anchor='w', padx=30, pady=(5, 5))
        
        card_color_frame = tk.Frame(dialog, bg=self.colors['background'])
        card_color_frame.pack(anchor='w', padx=30, pady=(0, 15))
        
        card_color_var = tk.StringVar(value=notice_data.get('card_color', '#ffffff') if is_editing and notice_data else '#ffffff')
        
        # Predefined color buttons for card
        card_color_options = [
            ('White', '#ffffff'),
            ('Light Blue', '#e3f2fd'),
            ('Light Green', '#e8f5e9'),
            ('Light Yellow', '#fffde7'),
            ('Light Pink', '#fce4ec'),
            ('Light Gray', '#f5f5f5'),
            ('Light Cyan', '#e0f7fa'),
            ('Light Orange', '#fff3e0')
        ]
        
        for color_name, color_code in card_color_options:
            btn = tk.Button(card_color_frame, text="",
                           bg=color_code,
                           fg='black',
                           relief='solid',
                           bd=1,
                           width=3,
                           height=1,
                           cursor='hand2',
                           command=lambda c=color_code: card_color_var.set(c))
            btn.pack(side='left', padx=2)
        
        # Buttons
        buttons_frame = tk.Frame(dialog, bg=self.colors['background'])
        buttons_frame.pack(pady=20)
        
        def save_notice():
            title = title_entry.get().strip()
            message = message_text.get("1.0", tk.END).strip()
            category = category_var.get()
            title_color = title_color_var.get()
            card_color = card_color_var.get()
            
            if not title:
                messagebox.showerror("Error", "Please enter a title.")
                return
            
            if not message:
                messagebox.showerror("Error", "Please enter a message.")
                return
            
            try:
                if self.db:
                    if is_editing:
                        # Update existing notice
                        self.db.update_notice(notice_id, title, message, category, title_color, card_color)
                        messagebox.showinfo("Success", "Notice updated successfully!")
                    else:
                        # Create new notice
                        self.db.save_notice(self.user_id, title, message, category, title_color, card_color)
                        messagebox.showinfo("Success", "Notice added successfully!")
                    dialog.destroy()
                    self.load_notices()
                else:
                    messagebox.showerror("Error", "Database not available.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save notice: {e}")
        
        tk.Button(buttons_frame, text="Save", 
                 command=save_notice,
                 font=("Arial", 11, "bold"),
                 bg=self.colors['primary_blue'],
                 fg='white',
                 relief='flat',
                 padx=25, pady=10,
                 cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(buttons_frame, text="Cancel", 
                 command=dialog.destroy,
                 font=("Arial", 11),
                 bg=self.colors['gray_medium'],
                 fg='white',
                 relief='flat',
                 padx=25, pady=10,
                 cursor='hand2').pack(side='left', padx=10)
    
    def delete_notice(self, notice_id):
        """Delete a notice (any user can delete)"""
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this notice?"):
            return
        
        try:
            if self.db:
                # Delete notice - any user can delete (user_id is optional)
                self.db.delete_notice(notice_id, self.user_id if self.user_id else None)
                messagebox.showinfo("Success", "Notice deleted successfully!")
                self.load_notices()
            else:
                messagebox.showerror("Error", "Database not available.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete notice: {e}")
