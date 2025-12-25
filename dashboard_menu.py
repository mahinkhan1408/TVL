# dashboard_menu.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from bid_writer_module import BidWriterApp
from notice_board_module import NoticeBoardModule
from vendor_price_module import VendorPriceModule
from gc_roof_ce_module import GCRoofCEModule
from todo_module import ModernToDoApp
from letterhead_bid_module import LetterheadBidModule
from approval_module import ApprovalModule
from wo_inspection_module import WOInspectionModule
from theme_manager import theme_manager
import sys
import os
import importlib.util
# Import Photo Viewer - handle the space in filename
photo_viewer_path = os.path.join(os.path.dirname(__file__), "Photo Viewer.py")
if os.path.exists(photo_viewer_path):
    spec = importlib.util.spec_from_file_location("photo_viewer", photo_viewer_path)
    photo_viewer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(photo_viewer_module)
    FastImageViewer = photo_viewer_module.FastImageViewer
else:
    FastImageViewer = None
import time
import re
import threading
from datetime import datetime
import json
import shutil

class DashboardMenu:
    def __init__(self, root, username):
        self.root = root
        self.root.title("Techvengers Universal App - Dashboard")
        
        self.username = username
        self.current_module_instance = None
        self.cached_modules = {}  # Cache module instances for faster switching
        
        # Use theme manager for colors (must be before database init)
        self.colors = theme_manager.get_current_colors()
        
        # Initialize Supabase database (optional - for data storage, not login)
        # Initialize asynchronously to prevent blocking UI
        self.db = None
        self.user_id = None
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
        
        self.root.update_idletasks()
        width = int(self.root.winfo_screenwidth() * 0.9)
        height = int(self.root.winfo_screenheight() * 0.9)
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.configure(bg=self.colors['background'])
        
        # Initialize database after UI is set up and main loop is running
        self.root.after(100, lambda: self._init_database_async(username))
        # Full-page content (no left sidebar)
        self.main_content_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.main_content_frame.pack(fill='both', expand=True)
        
        # Simple top navigation row
        top_nav = tk.Frame(self.main_content_frame, bg=self.colors['background'])
        top_nav.pack(fill='x', padx=16, pady=(12, 0))
        
        nav_buttons = [
            ("Dashboard", self.show_dashboard_content),
            ("Bid Writer", self.show_bid_writer_dashboard),
            ("To-Do", self.open_todo),
            ("Letterhead Bid", self.open_letterhead_bid),
            ("Notice Board", self.open_notice_board),
            ("Vendor Price", self.open_vendor_price),
            ("GC/Roof CE", self.open_gc_roof_ce),
            ("Settings", self.show_settings),
        ]
        self.nav_btn_refs = {}
        for text, cmd in nav_buttons:
            b = tk.Button(top_nav, text=text, font=("Segoe UI", 10), bg=self.colors['primary_blue'],
                          fg=self.colors['button_text'], relief='flat', cursor='hand2', padx=10, pady=4,
                          command=lambda c=cmd, t=text: self._nav_click_fullpage(c, t))
            b.pack(side='left', padx=(0, 6))
            self.nav_btn_refs[text] = b
        
        # Initial view
        self._nav_click_fullpage(self.show_dashboard_content, "Dashboard")
        
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
    
    def _init_database_async(self, username):
        """Initialize database asynchronously to prevent blocking UI."""
        def init_in_thread():
            try:
                from database_online import OnlineDatabaseManager
                db = OnlineDatabaseManager()
                # Get user_id from database if user exists
                user = db.get_user(username)
                user_id = user['id'] if user else None
                
                # Update in main thread - use after_idle to ensure main loop is running
                def update_db():
                    try:
                        self.db = db
                        self.user_id = user_id
                    except Exception as e:
                        print(f"Error updating database reference: {e}")
                
                # Use after_idle instead of after(0) to ensure main loop is ready
                try:
                    self.root.after_idle(update_db)
                except:
                    # Fallback: try after with a small delay
                    self.root.after(100, update_db)
            except Exception as e:
                print(f"Warning: Could not initialize database: {e}")
                def set_none():
                    try:
                        self.db = None
                        self.user_id = None
                    except Exception as e:
                        print(f"Error setting database to None: {e}")
                
                try:
                    self.root.after_idle(set_none)
                except:
                    self.root.after(100, set_none)
        
        # Start initialization in background thread
        thread = threading.Thread(target=init_in_thread, daemon=True)
        thread.start()

    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        self.apply_theme_to_dashboard()

    def apply_theme_to_dashboard(self):
        """Apply the current theme to all dashboard elements."""
        # Update root and main frames
        self.root.configure(bg=self.colors['background'])
        self.main_content_frame.configure(bg=self.colors['background'])
        # Update top nav button colors
        for btn in getattr(self, 'nav_btn_refs', {}).values():
            btn.configure(bg=self.colors['primary_blue'], fg=self.colors['button_text'])
        
        # Update any other UI elements that might be visible
        self.refresh_current_view()

    def refresh_current_view(self):
        """Refresh the current view to apply theme changes."""
        # Find which navigation button is currently active and refresh that view
        for btn_text, btn in self.nav_btn_refs.items():
            if btn.cget('bg') == self.colors['nav_hover']:
                # Re-trigger the current view
                if btn_text == "Dashboard":
                    self.show_dashboard_content()
                elif btn_text == "Bid Writer":
                    self.show_bid_writer_dashboard()
                elif btn_text == "Settings":
                    self.show_settings()
                break

    def _nav_click_fullpage(self, command, label):
        # Visual feedback for active nav (outline on hover spec also handled per card)
        for name, btn in self.nav_btn_refs.items():
            btn.configure(relief='flat', highlightthickness=0)
        if label in self.nav_btn_refs:
            self.nav_btn_refs[label].configure(relief='groove', highlightthickness=1,
                                               highlightbackground=self.colors.get('nav_hover', self.colors['primary_blue']))
        command()

    def show_placeholder(self, title):
        self.clear_content_frame()
        container = tk.Frame(self.main_content_frame, bg=self.colors['background'])
        container.pack(fill='both', expand=True)
        self._add_back_bar(container, title)
        tk.Label(container, text=f"Content for {title} (Coming Soon)", 
                 font=("Arial", 18, "bold"), fg=self.colors['primary_blue'],
                 bg=self.colors['background']).pack(expand=True)

    def clear_content_frame(self):
        """Clear content frame efficiently."""
        # Use update_idletasks to batch widget operations
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        # Force update to prevent visual lag
        self.root.update_idletasks()

    def show_dashboard_content(self):
        self.clear_content_frame()
        root_bg = self.colors['background']
        self.main_content_frame.config(bg=root_bg)

        # --- Hero header (two-tone) ---
        hero = tk.Frame(self.main_content_frame, bg=root_bg)
        hero.pack(fill='x', padx=20, pady=(20, 10))

        hero_wrap = tk.Frame(hero, bg=root_bg)
        hero_wrap.pack(fill='x')

        left_bg = self.colors.get('nav_hover', self.colors['primary_blue'])
        right_bg = self.colors['primary_blue']

        left = tk.Frame(hero_wrap, bg=left_bg, height=120)
        left.pack(side='left', fill='x', expand=True)
        left.pack_propagate(False)

        right = tk.Frame(hero_wrap, bg=right_bg, height=120)
        right.pack(side='left', fill='x', expand=True)
        right.pack_propagate(False)

        # Left: app title / logo
        tk.Label(left, text="📄  BidWrite Pro", font=("Segoe UI", 20, "bold"),
                 bg=left_bg, fg=self.colors['button_text']).pack(anchor='w', padx=20, pady=(25, 0))
        tk.Label(left, text="Craft winning bids with ease", font=("Segoe UI", 11),
                 bg=left_bg, fg=self.colors['button_text']).pack(anchor='w', padx=20, pady=(6, 0))

        # Right: welcome
        tk.Label(right, text=f"Welcome Back, {self.username}!", font=("Segoe UI", 18, "bold"),
                 bg=right_bg, fg=self.colors['button_text']).pack(anchor='w', padx=20, pady=(25, 0))
        tk.Label(right, text="Let's get started on your next winning bid.", font=("Segoe UI", 11),
                 bg=right_bg, fg=self.colors['button_text']).pack(anchor='w', padx=20, pady=(6, 0))

        # --- Cards grid ---
        cards_wrap = tk.Frame(self.main_content_frame, bg=root_bg)
        cards_wrap.pack(fill='both', expand=True, padx=20, pady=(5, 20))

        # Grid container
        grid = tk.Frame(cards_wrap, bg=root_bg)
        grid.pack(fill='both', expand=True)
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1, uniform='col')

        # Card definitions in requested serial
        # New bid, Open project, Templates, GC/Roof CE, Vendor Price, Letterheads,
        # Notice Boards, To-Do, Photo Viewer, Approval, WO Inspection, Settings
        cards = [
            ("New Bid", "Create a new bid", "🆕", self.create_new_bid),
            ("Open Project", "Continue your saved work", "📂", self.show_bid_writer_dashboard),
            ("Templates", "Bid templates", "📄", lambda: self.show_placeholder("Templates")),
            ("GC/Roof CE", "GC/Roof change orders", "🏗️", self.open_gc_roof_ce),
            ("Vendor Price", "Vendor pricing", "💲", self.open_vendor_price),
            ("Letterheads", "Letterhead bids", "📝", self.open_letterhead_bid),
            ("Notice Boards", "Announcements", "📢", self.open_notice_board),
            ("To-Do", "Tasks & reminders", "✅", self.open_todo),
            ("Photo Viewer", "View and edit images", "🖼️", self.open_photo_viewer),
            ("Approval", "Approval workflow", "✔️", self.open_approval),
            ("WO Inspection", "Work order inspections", "🔍", self.open_wo_inspection),
            ("Settings", "Preferences", "⚙️", self.show_settings),
        ]

        # Create cards in a neat grid (up to 4 columns per row)
        row, col = 0, 0
        for title, subtitle, icon, cmd in cards:
            self._create_dashboard_card(grid, row, col, icon, title, subtitle, cmd)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def show_bid_writer_dashboard(self):
        self.clear_content_frame()

        bid_writer_dashboard = tk.Frame(self.main_content_frame, bg=self.colors['background'], padx=20, pady=20)
        bid_writer_dashboard.pack(fill="both", expand=True)

        # Back to Dashboard bar
        self._add_back_bar(bid_writer_dashboard, "Bid Writer")

        header_frame = tk.Frame(bid_writer_dashboard, bg=self.colors['background'])
        header_frame.pack(fill='x', pady=(0, 20))

        tk.Label(header_frame, text="Bid Writer", font=("Arial", 24, "bold"), fg=self.colors['primary_blue'], bg=self.colors['background']).pack(side='left')

        # Create New Bid Section
        new_frame = tk.Frame(bid_writer_dashboard, bg=self.colors['gray_light'], relief="solid", bd=1, padx=15, pady=15)
        new_frame.pack(fill='x', pady=(0, 20))
        tk.Label(new_frame, text="Create New Bid", font=("Arial", 14, "bold"), bg=self.colors['gray_light'], fg=self.colors['primary_blue']).pack(anchor='w', pady=(0, 10))
        new_bid_button = tk.Button(new_frame, text="New Bid", font=("Arial", 12), bg=self.colors['light_blue'], fg="white", relief="solid", bd=1, cursor="hand2", command=self.create_new_bid)
        new_bid_button.pack(anchor='w', padx=5, pady=5)
        
        # Recent Bids Section
        recent_frame = tk.Frame(bid_writer_dashboard, bg=self.colors['gray_light'], relief="solid", bd=1, padx=15, pady=15)
        recent_frame.pack(fill='both', expand=True)
        recent_header_frame = tk.Frame(recent_frame, bg=self.colors['gray_light'])
        recent_header_frame.pack(fill='x')
        
        # Left side: Title and Bulk Delete button
        title_action_frame = tk.Frame(recent_header_frame, bg=self.colors['gray_light'])
        title_action_frame.pack(side='left', anchor='w', pady=(0, 10), fill='x', expand=False)
        
        tk.Label(title_action_frame, text="Recent Projects", font=("Arial", 14, "bold"), bg=self.colors['gray_light'], fg=self.colors['primary_blue'], anchor='w', justify='left').pack(side='left', anchor='w', padx=(0, 0))
        
        # Bulk Delete button
        self.bulk_delete_button = tk.Button(title_action_frame, text="Delete Selected", command=self.delete_selected_bids, font=("Arial", 10, "bold"), bg='#dc3545', fg='white', relief='flat', cursor="hand2", state='disabled', padx=10, pady=5)
        self.bulk_delete_button.pack(side='left', padx=(15, 0))
        
        # Dictionary to store selected checkboxes {wo_number: checkbox_var}
        self.selected_bids = {}
        
        # Search bar with filter dropdown
        search_frame = tk.Frame(recent_header_frame, bg=self.colors['gray_light'])
        search_frame.pack(side='right', pady=(0, 10))
        
        search_label = tk.Label(search_frame, text="Search:", font=("Arial", 10), bg=self.colors['gray_light'])
        search_label.pack(side='left', padx=(0, 5))
        
        self.search_filter = tk.StringVar(value="all")
        filter_menu = tk.OptionMenu(search_frame, self.search_filter, "all", "work_order", "property_address")
        filter_menu.config(font=("Arial", 9), bg=self.colors['white'])
        filter_menu.pack(side='left', padx=(0, 5))
        
        self.search_entry = tk.Entry(search_frame, width=25, font=("Arial", 11), relief="solid", bd=1)
        self.search_entry.pack(side='left', padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.load_recent_bids())

        search_button = tk.Button(search_frame, text="Search", command=lambda: self.load_recent_bids(), font=("Arial", 10), bg=self.colors['light_blue'], fg="white", relief="flat", cursor="hand2")
        search_button.pack(side='left', padx=(0, 5))
        
        clear_search_button = tk.Button(search_frame, text="Clear", command=lambda: [self.search_entry.delete(0, tk.END), self.search_filter.set("all"), self.load_recent_bids()], font=("Arial", 10), bg=self.colors['gray_medium'], fg="white", relief="flat", cursor="hand2")
        clear_search_button.pack(side='left')


        # Scrollable list for recent bids
        recent_canvas = tk.Canvas(recent_frame, bg=self.colors['white'], highlightthickness=0)
        recent_scrollbar = tk.Scrollbar(recent_frame, orient="vertical", command=recent_canvas.yview)
        recent_scrollable_frame = tk.Frame(recent_canvas, bg=self.colors['white'])

        recent_scrollable_frame.bind(
            "<Configure>",
            lambda e: recent_canvas.configure(scrollregion=recent_canvas.bbox("all"))
        )

        def update_canvas_width(event):
            """Update canvas window width to match canvas width for full-width table"""
            canvas_width = event.width
            recent_canvas.itemconfig(recent_canvas.find_all()[0], width=canvas_width)
        
        recent_canvas.create_window((0, 0), window=recent_scrollable_frame, anchor="nw")
        recent_canvas.configure(yscrollcommand=recent_scrollbar.set)
        recent_canvas.bind('<Configure>', update_canvas_width)
        
        recent_scrollbar.pack(side="right", fill="y")
        recent_canvas.pack(side="left", fill="both", expand=True)
        
        self.recent_bids_list = recent_scrollable_frame
        
        # Initial load of bids
        self.load_recent_bids()

    def load_recent_bids(self, search_term=None):
        for widget in self.recent_bids_list.winfo_children():
            widget.destroy()
        
        # Clear selected bids when reloading
        self.selected_bids = {}
        if hasattr(self, 'bulk_delete_button'):
            self.bulk_delete_button.config(state='disabled')
        if hasattr(self, 'select_all_var'):
            self.select_all_var.set(False)

        # Create table headers with consistent grid layout
        header_frame = tk.Frame(self.recent_bids_list, bg=self.colors['primary_blue'])
        header_frame.pack(fill='x')
        
        headers = ['Select', 'Work Order', 'Property Address', 'Client Code', 'WO Type', 'Bid Count', 'Created By', 'Last Modified', 'Delete', 'Export']
        
        # Column configuration: added Select column at the beginning
        # Weights: Select (1), Work Order (2), Property Address (4), Client Code (2), WO Type (2), Bid Count (1), Created By (2), Last Modified (2), Delete (1), Export (1)
        column_weights = [1, 2, 4, 2, 2, 1, 2, 2, 1, 1]
        column_minsizes = [50, 120, 180, 100, 120, 80, 120, 140, 70, 70]
        
        # Configure grid columns with weights and minimum sizes
        for i, (weight, minsize) in enumerate(zip(column_weights, column_minsizes)):
            header_frame.grid_columnconfigure(i, weight=weight, minsize=minsize)

        # Select All checkbox in header
        self.select_all_var = tk.BooleanVar()
        select_all_cb = tk.Checkbutton(header_frame, variable=self.select_all_var, command=self.toggle_select_all, bg=self.colors['primary_blue'], activebackground=self.colors['primary_blue'], highlightthickness=0, selectcolor=self.colors['primary_blue'])
        select_all_cb.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        
        for i, header in enumerate(headers[1:], start=1):  # Start from 1 to skip Select header
            tk.Label(header_frame, text=header, font=("Arial", 11, "bold"), fg='white', bg=self.colors['primary_blue'], padx=8, pady=8, anchor='w', justify='left').grid(row=0, column=i, sticky='nsw')

        try:
            if self.db and self.user_id:
                # Get search term from entry if not provided
                if search_term is None:
                    search_term = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
                filter_type = self.search_filter.get() if hasattr(self, 'search_filter') else "all"
                
                # Load from Supabase with search - show all projects from all users
                if search_term:
                    if filter_type == "work_order":
                        bids = self.db.search_bids_by_wo_number(self.user_id, search_term, all_bids=True)
                    elif filter_type == "property_address":
                        bids = self.db.search_bids_by_property_address(self.user_id, search_term, all_bids=True)
                    else:  # "all"
                        # Search both
                        wo_bids = self.db.search_bids_by_wo_number(self.user_id, search_term, all_bids=True)
                        addr_bids = self.db.search_bids_by_property_address(self.user_id, search_term, all_bids=True)
                        # Combine and deduplicate by wo_number
                        bids_dict = {}
                        for bid in wo_bids + addr_bids:
                            bids_dict[bid['wo_number']] = bid
                        bids = list(bids_dict.values())
                else:
                    bids = self.db.get_user_bids(self.user_id, all_bids=True)
                
                # Sort by updated_at descending
                bids.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
                
                if not bids:
                    tk.Label(self.recent_bids_list, text="No matching projects found." if search_term else "No projects found.", bg=self.colors['white'], fg=self.colors['gray_dark'], font=("Arial", 10, "italic")).pack(padx=10, pady=10)
                    return
                
                for bid in bids:
                    wo_number = bid['wo_number']
                    
                    # Load full bid data to get all fields including property_address, client_code, wo_type
                    bid_data = self.db.load_bid(wo_number, self.user_id, all_users=True)
                    
                    # Get data from full bid_data first, then fallback to summary bid
                    property_address = ''
                    client_code = ''
                    wo_type = ''
                    
                    if bid_data:
                        property_address = bid_data.get('property_address') or ''
                        client_code = bid_data.get('client_code') or ''
                        wo_type = bid_data.get('wo_type') or ''
                    
                    # Fallback to summary bid if not found in full bid_data
                    if not property_address:
                        property_address = bid.get('property_address') or ''
                    if not client_code:
                        client_code = bid.get('client_code') or ''
                    if not wo_type:
                        wo_type = bid.get('wo_type') or ''
                    
                    # Parse updated_at timestamp - format to human-readable
                    updated_at = bid.get('updated_at', '')
                    modified_time = ''
                    if updated_at:
                        try:
                            # Try parsing ISO format timestamp
                            if 'T' in updated_at:
                                # ISO format: 2024-01-01T12:00:00+00:00
                                date_str = updated_at.split('T')[0]
                                # Parse date and format as "Dec 24, 2025"
                                dt = datetime.strptime(date_str, '%Y-%m-%d')
                                modified_time = dt.strftime('%b %d, %Y')
                            else:
                                # Try other formats
                                try:
                                    dt = datetime.strptime(updated_at[:10], '%Y-%m-%d')
                                    modified_time = dt.strftime('%b %d, %Y')
                                except:
                                    modified_time = updated_at[:10] if len(updated_at) >= 10 else updated_at
                        except Exception as e:
                            print(f"Error parsing date: {e}")
                            modified_time = updated_at[:10] if len(updated_at) >= 10 else updated_at
                    
                    # Get bid count from loaded bid_data
                    bid_count = 0
                    if bid_data and 'selected_items' in bid_data:
                        for category in bid_data['selected_items']:
                            bid_count += len(bid_data['selected_items'][category])
                    
                    # Create row with proper grid layout - must match header configuration
                    row_frame = tk.Frame(self.recent_bids_list, bg=self.colors['white'])
                    
                    # Use same column configuration as header for perfect alignment
                    column_weights = [1, 2, 4, 2, 2, 1, 2, 2, 1, 1]
                    column_minsizes = [50, 120, 180, 100, 120, 80, 120, 140, 70, 70]
                    
                    for i, (weight, minsize) in enumerate(zip(column_weights, column_minsizes)):
                        row_frame.grid_columnconfigure(i, weight=weight, minsize=minsize)
                    
                    # Get created_by username
                    created_by = bid.get('created_by_username') or ''
                    if not created_by or created_by == '':
                        # Try to get username from user_id if created_by_username is missing
                        bid_user_id = bid.get('user_id')
                        if bid_user_id and self.db:
                            try:
                                user = self.db.get_user_by_id(bid_user_id)
                                if user:
                                    created_by = user.get('username', 'N/A')
                                else:
                                    created_by = 'N/A'
                            except Exception as e:
                                print(f"Error fetching username for user_id {bid_user_id}: {e}")
                                created_by = 'N/A'
                        else:
                            created_by = 'N/A'
                    
                    # Ensure all values are strings and handle empty/None values
                    property_address = str(property_address).strip() if property_address and property_address != 'N/A' else ''
                    client_code = str(client_code).strip() if client_code and client_code != 'N/A' else ''
                    wo_type = str(wo_type).strip() if wo_type and wo_type != 'N/A' else ''
                    bid_count = str(bid_count) if bid_count else '0'
                    created_by = str(created_by).strip() if created_by and created_by != 'N/A' else ''
                    modified_time = str(modified_time).strip() if modified_time and modified_time != 'N/A' else ''
                    
                    # Make all labels clickable
                    def make_label_click_handler(wo):
                        return lambda e: self.open_existing_bid(wo)
                    
                    # Checkbox for selection
                    checkbox_var = tk.BooleanVar()
                    self.selected_bids[wo_number] = checkbox_var
                    checkbox = tk.Checkbutton(row_frame, variable=checkbox_var, command=self.update_bulk_delete_button_state, bg=self.colors['white'], activebackground=self.colors['white'], highlightthickness=0, selectcolor=self.colors['white'])
                    checkbox.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
                    
                    # Create all cells with consistent styling and proper padding
                    wo_label = tk.Label(row_frame, text=wo_number, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['primary_blue'], anchor='w', cursor="hand2", padx=8, pady=8)
                    wo_label.grid(row=0, column=1, sticky='nsew')
                    wo_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    addr_label = tk.Label(row_frame, text=property_address, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    addr_label.grid(row=0, column=2, sticky='nsew')
                    addr_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    client_label = tk.Label(row_frame, text=client_code, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    client_label.grid(row=0, column=3, sticky='nsew')
                    client_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    wo_type_label = tk.Label(row_frame, text=wo_type, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    wo_type_label.grid(row=0, column=4, sticky='nsew')
                    wo_type_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    count_label = tk.Label(row_frame, text=bid_count, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    count_label.grid(row=0, column=5, sticky='nsew')
                    count_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    created_by_label = tk.Label(row_frame, text=created_by, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['primary_blue'], anchor='w', cursor="hand2", padx=8, pady=8)
                    created_by_label.grid(row=0, column=6, sticky='nsew')
                    created_by_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    time_label = tk.Label(row_frame, text=modified_time, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    time_label.grid(row=0, column=7, sticky='nsew')
                    time_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    # Delete button
                    delete_button = tk.Button(row_frame, text="Delete", command=lambda wo=wo_number: self.delete_bid_state(wo), font=("Arial", 9), bg='#dc3545', fg='white', relief='flat', padx=8, pady=5)
                    delete_button.grid(row=0, column=8, sticky='nsew')

                    # Export button
                    export_button = tk.Button(row_frame, text="Export", command=lambda wo=wo_number: self.export_bid_state(wo), font=("Arial", 9), bg=self.colors['primary_blue'], fg='white', relief='flat', padx=8, pady=5)
                    export_button.grid(row=0, column=9, sticky='nsew')
                    
                    # Bind the entire row to open the bid
                    def make_open_handler(wo):
                        return lambda e: self.open_existing_bid(wo)
                    row_frame.bind("<Button-1>", make_open_handler(wo_number))
                    
                    # Pack the row frame
                    row_frame.pack(fill='x', pady=1)
            else:
                # Fallback to local JSON files if database not available
                files = [f for f in os.listdir(self.app_data_dir) if f.startswith("WO_") and f.endswith(".json")]

                # Filter files based on search term
                if search_term:
                    files = [f for f in files if search_term.lower() in f.lower()]

                files.sort(key=lambda f: os.path.getmtime(os.path.join(self.app_data_dir, f)), reverse=True)
                
                if not files:
                    tk.Label(self.recent_bids_list, text="No matching projects found.", bg=self.colors['white'], fg=self.colors['gray_dark'], font=("Arial", 10, "italic")).pack(padx=10, pady=10)
                    return

                for i, file in enumerate(files):
                    wo_number = file.replace("WO_", "").replace(".json", "")
                    file_path = os.path.join(self.app_data_dir, file)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')

                    # Load the JSON to get bid count
                    bid_count = 0
                    try:
                        with open(file_path, 'r') as f:
                            state = json.load(f)
                            if 'selected_items' in state:
                                for category in state['selected_items']:
                                    bid_count += len(state['selected_items'][category])
                    except Exception as e:
                        print(f"Error loading bid count for {file}: {e}")
                        bid_count = "N/A"

                    row_frame = tk.Frame(self.recent_bids_list, bg=self.colors['white'])
                    row_frame.pack(fill='x', pady=1)
                    
                    # Use same column configuration as header for perfect alignment
                    column_weights = [1, 2, 4, 2, 2, 1, 2, 2, 1, 1]
                    column_minsizes = [50, 120, 180, 100, 120, 80, 120, 140, 70, 70]
                    
                    for i, (weight, minsize) in enumerate(zip(column_weights, column_minsizes)):
                        row_frame.grid_columnconfigure(i, weight=weight, minsize=minsize)
                    
                    # Checkbox for selection
                    checkbox_var = tk.BooleanVar()
                    self.selected_bids[wo_number] = checkbox_var
                    checkbox = tk.Checkbutton(row_frame, variable=checkbox_var, command=self.update_bulk_delete_button_state, bg=self.colors['white'], activebackground=self.colors['white'], highlightthickness=0, selectcolor=self.colors['white'])
                    checkbox.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
                    
                    # Bind the entire row to open the bid - use default parameter to capture wo_number correctly
                    def make_open_handler(wo):
                        return lambda e: self.open_existing_bid(wo)
                    row_frame.bind("<Button-1>", make_open_handler(wo_number))

                    # Make all labels clickable
                    def make_label_click_handler(wo):
                        return lambda e: self.open_existing_bid(wo)
                    
                    wo_label = tk.Label(row_frame, text=wo_number, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['primary_blue'], anchor='w', cursor="hand2", padx=8, pady=8)
                    wo_label.grid(row=0, column=1, sticky='nsew')
                    wo_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    # Empty cells for columns that don't exist in local file mode
                    addr_label = tk.Label(row_frame, text="", font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', padx=8, pady=8)
                    addr_label.grid(row=0, column=2, sticky='nsew')
                    
                    client_label = tk.Label(row_frame, text="", font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', padx=8, pady=8)
                    client_label.grid(row=0, column=3, sticky='nsew')
                    
                    wo_type_label = tk.Label(row_frame, text="", font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', padx=8, pady=8)
                    wo_type_label.grid(row=0, column=4, sticky='nsew')
                    
                    count_label = tk.Label(row_frame, text=str(bid_count), font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    count_label.grid(row=0, column=5, sticky='nsew')
                    count_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    created_by_label = tk.Label(row_frame, text="", font=("Arial", 10), bg=self.colors['white'], fg=self.colors['primary_blue'], anchor='w', padx=8, pady=8)
                    created_by_label.grid(row=0, column=6, sticky='nsew')
                    
                    time_label = tk.Label(row_frame, text=modified_time, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2", padx=8, pady=8)
                    time_label.grid(row=0, column=7, sticky='nsew')
                    time_label.bind("<Button-1>", make_label_click_handler(wo_number))
                    
                    # Delete button
                    delete_button = tk.Button(row_frame, text="Delete", command=lambda wo=wo_number: self.delete_bid_state(wo), font=("Arial", 9), bg='#dc3545', fg='white', relief='flat', padx=8, pady=5)
                    delete_button.grid(row=0, column=8, sticky='nsew')

                    # Export button
                    export_button = tk.Button(row_frame, text="Export", command=lambda wo=wo_number: self.export_bid_state(wo), font=("Arial", 9), bg=self.colors['primary_blue'], fg='white', relief='flat', padx=8, pady=5)
                    export_button.grid(row=0, column=9, sticky='nsew')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recent projects: {e}")

    # --- Dashboard Card Helper ---
    def _create_dashboard_card(self, parent, row, col, icon, title, subtitle, command):
        card_bg = self.colors['white'] if 'white' in self.colors else '#FFFFFF'
        shadow_color = self.colors.get('shadow_gray', self.colors.get('gray_light', '#D0D0D0'))

        # Container cell (uses grid) to keep shape
        cell = tk.Frame(parent, bg=self.colors['background'])
        cell.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        parent.grid_rowconfigure(row, weight=1)
        cell.grid_propagate(True)

        # Shadow (hidden initially)
        shadow = tk.Frame(cell, bg=shadow_color, bd=0, relief='flat')
        shadow.place_forget()

        # Card on top
        card = tk.Frame(cell, bg=card_bg, relief='flat', bd=0,
                        highlightthickness=1, highlightbackground=self.colors['gray_light'])
        card.place(relx=0, rely=0, relwidth=1, relheight=1)

        inner = tk.Frame(card, bg=card_bg)
        inner.pack(fill='both', expand=True, padx=16, pady=14)

        # Icon
        tk.Label(inner, text=icon, font=("Segoe UI", 22), bg=card_bg).pack(anchor='w')
        # Title
        tk.Label(inner, text=title, font=("Segoe UI", 12, "bold"),
                 bg=card_bg, fg=self.colors['primary_blue']).pack(anchor='w', pady=(6, 2))
        # Subtitle
        tk.Label(inner, text=subtitle, font=("Segoe UI", 10),
                 bg=card_bg, fg=self.colors['gray_dark']).pack(anchor='w')

        # Hover effects (outline + shadow) across the whole section
        def on_enter(_e=None):
            # Outline
            card.configure(highlightbackground=self.colors.get('nav_hover', self.colors['primary_blue']),
                           highlightthickness=2)
            # Shadow slightly offset
            try:
                shadow.place(relx=0, rely=0, relwidth=1, relheight=1, x=3, y=3)
                shadow.lift()  # make sure shadow draws under card
                card.lift()
            except Exception:
                pass

        def on_leave(_e=None):
            card.configure(highlightbackground=self.colors['gray_light'], highlightthickness=1)
            try:
                shadow.place_forget()
            except Exception:
                pass

        # Click handler for all card area
        def handle_click(_e=None):
            try:
                command()
            except Exception as ex:
                messagebox.showerror("Action", f"Failed to open: {ex}")

        # Bind recursively so hovering anywhere triggers effects smoothly
        def bind_recursive(widget):
            widget.bind('<Enter>', lambda e: on_enter())
            widget.bind('<Leave>', lambda e: on_leave())
            widget.bind('<Button-1>', handle_click)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(cell)

    def toggle_select_all(self):
        """Toggle selection of all checkboxes"""
        select_all = self.select_all_var.get()
        for checkbox_var in self.selected_bids.values():
            checkbox_var.set(select_all)
        self.update_bulk_delete_button_state()
    
    def update_bulk_delete_button_state(self):
        """Update the bulk delete button state based on selected items"""
        if hasattr(self, 'bulk_delete_button'):
            selected_count = sum(1 for var in self.selected_bids.values() if var.get())
            if selected_count > 0:
                self.bulk_delete_button.config(state='normal', text=f"Delete Selected ({selected_count})")
            else:
                self.bulk_delete_button.config(state='disabled', text="Delete Selected")
    
    def delete_selected_bids(self):
        """Delete all selected bids"""
        selected_wo_numbers = [wo_number for wo_number, var in self.selected_bids.items() if var.get()]
        
        if not selected_wo_numbers:
            messagebox.showwarning("No Selection", "Please select at least one project to delete.")
            return
        
        count = len(selected_wo_numbers)
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete {count} selected project(s)?"):
            return
        
        deleted_count = 0
        failed_count = 0
        failed_items = []
        
        try:
            for wo_number in selected_wo_numbers:
                try:
                    if self.db and self.user_id:
                        # Delete from Supabase
                        self.db.delete_bid(wo_number, self.user_id)
                        deleted_count += 1
                    else:
                        # Fallback to local file deletion
                        file_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_count += 1
                        else:
                            failed_count += 1
                            failed_items.append(wo_number)
                except Exception as e:
                    failed_count += 1
                    failed_items.append(wo_number)
                    print(f"Error deleting bid {wo_number}: {e}")
            
            # Show result message
            if deleted_count == count:
                messagebox.showinfo("Success", f"Successfully deleted {deleted_count} project(s).")
            elif deleted_count > 0:
                messagebox.showwarning("Partial Success", f"Deleted {deleted_count} project(s). Failed to delete {failed_count} project(s): {', '.join(failed_items)}")
            else:
                messagebox.showerror("Error", f"Failed to delete all selected projects.")
            
            # Reload the list
            self.load_recent_bids()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete selected bids: {e}")
    
    def delete_bid_state(self, wo_number):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete the bid for WO# {wo_number}?"):
            try:
                if self.db and self.user_id:
                    # Delete from Supabase
                    self.db.delete_bid(wo_number, self.user_id)
                    messagebox.showinfo("Success", f"Bid for WO# {wo_number} has been deleted.")
                else:
                    # Fallback to local file deletion
                    file_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        messagebox.showinfo("Success", f"Bid for WO# {wo_number} has been deleted.")
                    else:
                        messagebox.showerror("Error", f"File not found for WO# {wo_number}.")
                self.load_recent_bids()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete bid: {e}")

    def export_bid_state(self, wo_number):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("All Files", "*.*")],
            initialfile=f"WO_{wo_number}.json",
            title="Export Bid State"
        )
        
        if file_path:
            try:
                if self.db and self.user_id:
                    # Load from Supabase and save to file
                    bid_data = self.db.load_bid(wo_number, self.user_id)
                    if bid_data:
                        with open(file_path, 'w') as f:
                            json.dump(bid_data, f, indent=4)
                        messagebox.showinfo("Success", f"Bid for WO# {wo_number} exported successfully to:\n{file_path}")
                    else:
                        messagebox.showerror("Error", f"Bid for WO# {wo_number} not found in database.")
                else:
                    # Fallback to local file
                    source_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
                    if os.path.exists(source_path):
                        shutil.copyfile(source_path, file_path)
                        messagebox.showinfo("Success", f"Bid for WO# {wo_number} exported successfully to:\n{file_path}")
                    else:
                        messagebox.showerror("Error", f"File for WO# {wo_number} not found.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export file: {e}")

    def create_new_bid(self):
        """Show dialog to get Work Order, Property Address, Client Code, and WO Type, then open bid writer"""
        from tkinter import ttk
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Bid")
        dialog.geometry("580x560")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (580 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"580x600+{x}+{y}")
        
        # Header frame with title (blue background)
        header_frame = tk.Frame(dialog, bg=self.colors['primary_blue'], height=65)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Create New Bid", 
                              font=("Segoe UI", 20, "bold"), 
                              bg=self.colors['primary_blue'], fg='white')
        title_label.pack(expand=True, pady=18)
        
        # Form frame with better padding and spacing
        form_frame = tk.Frame(dialog, bg=self.colors['background'])
        form_frame.pack(pady=25, padx=40, fill='both', expand=False)
        
        # Work Order
        wo_label = tk.Label(form_frame, text="Work Order:", 
                           font=("Segoe UI", 11, "bold"),
                           bg=self.colors['background'], 
                           fg=self.colors['text_primary'], anchor='w')
        wo_label.pack(fill='x', pady=(0, 8))
        wo_entry = tk.Entry(form_frame, font=("Segoe UI", 11), 
                           relief="solid", bd=1, 
                           highlightthickness=1,
                           highlightcolor=self.colors['primary_blue'],
                           highlightbackground='#CCCCCC',
                           bg=self.colors['white'], 
                           fg=self.colors['text_primary'])
        wo_entry.pack(fill='x', ipady=8, pady=(0, 18))
        wo_entry.focus()
        
        # Property Address
        address_label = tk.Label(form_frame, text="Property Address:", 
                                font=("Segoe UI", 11, "bold"),
                                bg=self.colors['background'], 
                                fg=self.colors['text_primary'], anchor='w')
        address_label.pack(fill='x', pady=(0, 8))
        address_entry = tk.Entry(form_frame, font=("Segoe UI", 11), 
                                relief="solid", bd=1,
                                highlightthickness=1,
                                highlightcolor=self.colors['primary_blue'],
                                highlightbackground='#CCCCCC',
                                bg=self.colors['white'], 
                                fg=self.colors['text_primary'])
        address_entry.pack(fill='x', ipady=8, pady=(0, 18))
        
        # Client Code
        client_label = tk.Label(form_frame, text="Client Code:", 
                               font=("Segoe UI", 11, "bold"),
                               bg=self.colors['background'], 
                               fg=self.colors['text_primary'], anchor='w')
        client_label.pack(fill='x', pady=(0, 8))
        client_entry = tk.Entry(form_frame, font=("Segoe UI", 11), 
                               relief="solid", bd=1,
                               highlightthickness=1,
                               highlightcolor=self.colors['primary_blue'],
                               highlightbackground='#CCCCCC',
                               bg=self.colors['white'], 
                               fg=self.colors['text_primary'])
        client_entry.pack(fill='x', ipady=8, pady=(0, 18))
        
        # WO Type dropdown
        wo_type_label = tk.Label(form_frame, text="WO Type:", 
                                font=("Segoe UI", 11, "bold"),
                                bg=self.colors['background'], 
                                fg=self.colors['text_primary'], anchor='w')
        wo_type_label.pack(fill='x', pady=(0, 8))
        
        wo_type_options = [
            "Initial REO Service",
            "Initial Sales Clean",
            "Initial Secure",
            "Initial Services",
            "Inspection",
            "Initial Grass Cut",
            "Final Secure",
            "Eviction",
            "Bid Request (VRFY)",
            "Bid Request",
            "Bid Approval"
        ]
        
        wo_type_var = tk.StringVar()
        wo_type_combo = ttk.Combobox(form_frame, textvariable=wo_type_var, 
                                     values=wo_type_options, font=("Segoe UI", 11),
                                     state="readonly")
        wo_type_combo.pack(fill='x', ipady=8, pady=(0, 30))
        wo_type_combo.current(0)  # Set default to first option
        
        # Style the combobox for better appearance
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', 
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=8)
        style.map('TCombobox',
                 fieldbackground=[('readonly', 'white')],
                 bordercolor=[('focus', self.colors['primary_blue']), ('!focus', '#CCCCCC')])
        
        # Buttons frame with better spacing - ensure it's visible
        buttons_frame = tk.Frame(dialog, bg=self.colors['background'])
        buttons_frame.pack(pady=(20, 25), fill='x', padx=40)
        
        def create_bid():
            wo_number = wo_entry.get().strip()
            property_address = address_entry.get().strip()
            client_code = client_entry.get().strip()
            wo_type = wo_type_var.get().strip()
            
            if not wo_number:
                messagebox.showwarning("Warning", "Please enter a Work Order Number")
                wo_entry.focus()
                return
            
            if not property_address:
                messagebox.showwarning("Warning", "Please enter a Property Address")
                address_entry.focus()
                return
            
            # Create new project in database with all fields
            if self.db and self.user_id:
                try:
                    # Create initial project entry with all 4 fields
                    self.db.create_project(wo_number, self.user_id, property_address, 
                                         client_code, wo_type, self.username)
                except Exception as e:
                    print(f"Warning: Could not create project in database: {e}")
                    # Continue anyway - project will be created when first saved
            
            dialog.destroy()
            new_window = tk.Toplevel(self.root)
            BidWriterApp(new_window, self.username, wo_number_to_load=wo_number, 
                        property_address=property_address, user_id=self.user_id, 
                        client_code=client_code, wo_type=wo_type,
                        on_save_callback=self.load_recent_bids)
        
        def cancel():
            dialog.destroy()
        
        # Cancel button (improved styling)
        cancel_btn = tk.Button(buttons_frame, text="Cancel", 
                              font=("Segoe UI", 11, "bold"),
                              bg=self.colors['gray_medium'], fg='white', 
                              relief="flat",
                              cursor="hand2", 
                              padx=25, pady=10, 
                              command=cancel,
                              activebackground='#999999')
        cancel_btn.pack(side='left', padx=5)
        
        # Create button (improved styling)
        create_btn = tk.Button(buttons_frame, text="Create New Project", 
                              font=("Segoe UI", 11, "bold"),
                              bg=self.colors['primary_blue'], fg='white', 
                              relief="flat",
                              cursor="hand2", 
                              padx=25, pady=10, 
                              command=create_bid,
                              activebackground=self.colors.get('nav_hover', self.colors['primary_blue']))
        create_btn.pack(side='left', padx=5)
        
        # Bind Enter key navigation
        wo_entry.bind("<Return>", lambda e: address_entry.focus())
        address_entry.bind("<Return>", lambda e: client_entry.focus())
        client_entry.bind("<Return>", lambda e: wo_type_combo.focus())
        wo_type_combo.bind("<Return>", lambda e: create_bid())
        dialog.bind("<Escape>", lambda e: cancel())
        
    def open_existing_bid(self, wo_number):
        """Open existing bid and load all project fields if available - can open from any user"""
        property_address = None
        client_code = None
        wo_type = None
        bid_user_id = self.user_id
        
        if self.db:
            try:
                # Load bid from any user (all_users=True)
                bid_data = self.db.load_bid(wo_number, self.user_id, all_users=True)
                if bid_data:
                    property_address = bid_data.get('property_address')
                    client_code = bid_data.get('client_code')
                    wo_type = bid_data.get('wo_type')
                    # Use the bid's user_id if available, otherwise use current user_id
                    bid_user_id = bid_data.get('user_id', self.user_id)
                else:
                    # Bid not found - show error
                    messagebox.showerror("Error", f"Could not find project with Work Order: {wo_number}")
                    return
            except Exception as e:
                error_msg = str(e)
                print(f"Could not load project data: {e}")
                messagebox.showerror("Error", f"Failed to load project:\n{error_msg}")
                return
        
        try:
            new_window = tk.Toplevel(self.root)
            BidWriterApp(new_window, self.username, wo_number, property_address=property_address, 
                        user_id=bid_user_id, client_code=client_code, wo_type=wo_type,
                        on_save_callback=self.load_recent_bids)
        except Exception as e:
            error_msg = str(e)
            print(f"Error opening bid writer: {e}")
            messagebox.showerror("Error", f"Failed to open project:\n{error_msg}")

    def open_letterhead_bid(self): 
        new_window = tk.Toplevel(self.root)
        LetterheadBidModule(new_window)

    def open_notice_board(self):
        new_window = tk.Toplevel(self.root)
        NoticeBoardModule(new_window)

    def open_vendor_price(self):
        new_window = tk.Toplevel(self.root)
        VendorPriceModule(new_window)

    def open_gc_roof_ce(self):
        new_window = tk.Toplevel(self.root)
        GCRoofCEModule(new_window)

    def open_photo_viewer(self):
        if FastImageViewer is None:
            messagebox.showerror("Error", "Photo Viewer module not found.")
            return
        new_window = tk.Toplevel(self.root)
        FastImageViewer(new_window)

    def open_todo(self):
        new_window = tk.Toplevel(self.root)
        ModernToDoApp(new_window, user_id=self.user_id if hasattr(self, 'user_id') else None)
    
    def open_approval(self):
        self.clear_content_frame()
        approval_frame = tk.Frame(self.main_content_frame, bg=self.colors['background'], padx=20, pady=20)
        approval_frame.pack(fill="both", expand=True)
        
        # Back to Dashboard bar
        self._add_back_bar(approval_frame, "Approval Tracking")
        
        # Create ApprovalModule in the frame
        ApprovalModule(approval_frame, username=self.username, user_id=self.user_id if hasattr(self, 'user_id') else None)
    
    def open_wo_inspection(self):
        self.clear_content_frame()
        wo_inspection_frame = tk.Frame(self.main_content_frame, bg=self.colors['background'], padx=20, pady=20)
        wo_inspection_frame.pack(fill="both", expand=True)
        
        # Back to Dashboard bar
        self._add_back_bar(wo_inspection_frame, "WO Inspection")
        
        # Create WOInspectionModule in the frame
        WOInspectionModule(wo_inspection_frame, username=self.username, user_id=self.user_id if hasattr(self, 'user_id') else None)

    def show_settings(self):
        """Show the settings page with theme options."""
        self.clear_content_frame()
        self.main_content_frame.config(bg=self.colors['background'])
        self._add_back_bar(self.main_content_frame, "Settings")
        
        # Settings header
        header_frame = tk.Frame(self.main_content_frame, bg=self.colors['background'])
        header_frame.pack(pady=20, fill='x', padx=40)
        
        tk.Label(header_frame, text="Settings", 
                font=("Arial", 24, "bold"), 
                fg=self.colors['primary_blue'], 
                bg=self.colors['background']).pack(anchor='w')
        
        # Settings content container
        settings_container = tk.Frame(self.main_content_frame, bg=self.colors['background'])
        settings_container.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Theme settings section
        theme_section = tk.Frame(settings_container, bg=self.colors['white'], relief="solid", bd=1)
        theme_section.pack(fill='x', pady=(0, 20))
        
        # Theme section header
        theme_header = tk.Frame(theme_section, bg=self.colors['primary_blue'], height=50)
        theme_header.pack(fill='x')
        theme_header.pack_propagate(False)
        
        tk.Label(theme_header, text="Appearance", 
                font=("Arial", 16, "bold"), 
                fg=self.colors['button_text'], 
                bg=self.colors['primary_blue']).pack(side='left', padx=20, pady=15)
        
        # Theme content
        theme_content = tk.Frame(theme_section, bg=self.colors['white'])
        theme_content.pack(fill='x', padx=30, pady=20)
        
        tk.Label(theme_content, text="Theme:", 
                font=("Arial", 12, "bold"), 
                fg=self.colors['text_primary'], 
                bg=self.colors['white']).pack(anchor='w', pady=(0, 10))
        
        # Theme selection frame
        theme_selection_frame = tk.Frame(theme_content, bg=self.colors['white'])
        theme_selection_frame.pack(fill='x')
        
        # Radio buttons for theme selection
        self.theme_var = tk.StringVar(value=theme_manager.current_theme)
        
        light_frame = tk.Frame(theme_selection_frame, bg=self.colors['white'])
        light_frame.pack(fill='x', pady=5)
        
        light_radio = tk.Radiobutton(light_frame, text="Light Mode", 
                                    variable=self.theme_var, value="light",
                                    font=("Arial", 11), 
                                    bg=self.colors['white'], 
                                    fg=self.colors['text_primary'],
                                    selectcolor=self.colors['white'],
                                    activebackground=self.colors['white'],
                                    command=lambda: self.change_theme("light"))
        light_radio.pack(side='left')
        
        tk.Label(light_frame, text="Perfect for bright environments and daytime use", 
                font=("Arial", 9), 
                fg=self.colors['text_secondary'], 
                bg=self.colors['white']).pack(side='left', padx=(10, 0))
        
        dark_frame = tk.Frame(theme_selection_frame, bg=self.colors['white'])
        dark_frame.pack(fill='x', pady=5)
        
        dark_radio = tk.Radiobutton(dark_frame, text="Dark Mode", 
                                   variable=self.theme_var, value="dark",
                                   font=("Arial", 11), 
                                   bg=self.colors['white'], 
                                   fg=self.colors['text_primary'],
                                   selectcolor=self.colors['white'],
                                   activebackground=self.colors['white'],
                                   command=lambda: self.change_theme("dark"))
        dark_radio.pack(side='left')
        
        tk.Label(dark_frame, text="Easier on the eyes for low-light environments", 
                font=("Arial", 9), 
                fg=self.colors['text_secondary'], 
                bg=self.colors['white']).pack(side='left', padx=(10, 0))
        
        # Additional settings sections can be added here
        # For example: Language, Notifications, etc.
        
        # Info section
        info_section = tk.Frame(settings_container, bg=self.colors['white'], relief="solid", bd=1)
        info_section.pack(fill='x', pady=(0, 20))
        
        info_header = tk.Frame(info_section, bg=self.colors['primary_blue'], height=50)
        info_header.pack(fill='x')
        info_header.pack_propagate(False)
        
        tk.Label(info_header, text="Information", 
                font=("Arial", 16, "bold"), 
                fg=self.colors['button_text'], 
                bg=self.colors['primary_blue']).pack(side='left', padx=20, pady=15)
        
        info_content = tk.Frame(info_section, bg=self.colors['white'])
        info_content.pack(fill='x', padx=30, pady=20)
        
        tk.Label(info_content, text="Techvengers Universal App", 
                font=("Arial", 12, "bold"), 
                fg=self.colors['text_primary'], 
                bg=self.colors['white']).pack(anchor='w')
        
        tk.Label(info_content, text="Version 1.0", 
                font=("Arial", 10), 
                fg=self.colors['text_secondary'], 
                bg=self.colors['white']).pack(anchor='w', pady=(5, 10))
        
        tk.Label(info_content, text="© 2024 Techvengers LTD. All rights reserved.", 
                font=("Arial", 9), 
                fg=self.colors['text_secondary'], 
                bg=self.colors['white']).pack(anchor='w')

    # --- Helper: Back bar for in-page sections ---
    def _add_back_bar(self, parent, title_text=""):
        bar = tk.Frame(parent, bg=self.colors['background'])
        bar.pack(fill='x', padx=10, pady=(0, 10))
        back_btn = tk.Button(bar, text="← Back", font=("Segoe UI", 10),
                             bg=self.colors['primary_blue'], fg=self.colors['button_text'],
                             relief='flat', cursor='hand2', padx=10, pady=4,
                             command=self.show_dashboard_content)
        back_btn.pack(side='left')
        back_btn.bind('<Enter>', lambda e: back_btn.configure(bg=self.colors.get('nav_hover', self.colors['primary_blue'])))
        back_btn.bind('<Leave>', lambda e: back_btn.configure(bg=self.colors['primary_blue']))
        if title_text:
            tk.Label(bar, text=title_text, font=("Segoe UI", 12, "bold"),
                     bg=self.colors['background'], fg=self.colors['primary_blue']).pack(side='left', padx=10)
        return bar

    def change_theme(self, theme_name):
        """Change the application theme."""
        theme_manager.switch_theme(theme_name)
        messagebox.showinfo("Theme Changed", 
                           f"Theme changed to {theme_name.title()} Mode.\n"
                           f"The new theme has been applied to all open windows.")