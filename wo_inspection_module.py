# wo_inspection_module.py
import tkinter as tk
from tkinter import messagebox
from theme_manager import theme_manager
import json
import os

class WOInspectionModule:
    """
    WO Inspection Module - Card-based interface for inspection types
    """
    
    # Inspection types as provided by user
    INSPECTION_TYPES = [
        ("Grass Cut", "🌱"),
        ("Initial Secure", "🔒"),
        ("Initial Services", "🛠️"),
        ("Verify ICC", "✅"),
        ("Meet and Greet", "👋"),
        ("Eviction", "🚪"),
        ("Winterization", "❄️"),
        ("Bid Approvals", "📋"),
        ("Snow Removal", "🌨️"),
        ("Securing", "🔐"),
        ("Bid Request(1st Time)", "📝"),
    ]
    
    # Checklist items for each inspection type
    CHECKLISTS = {
        "Winterization": [
            "Water shut off at curb + zip tied",
            "Breakers OFF (unless sump pump/dehumidifier → ON)",
            "All water systems drained (heater, softener, tanks, lines, fixtures)",
            "Boiler/radiator draining photos (if applicable)",
            "Heating system photos provided",
            "All faucets/valves opened + radiators pressure released",
            "Compressor connected and running to blow out lines",
            "Compressor photos included",
            "Well pump drained (if applicable)",
            "Proper pressure test (35 PSI, stand-alone gauge, 30-min rest, final reading photo)",
            "Antifreeze poured in all drains",
            "Toilets cleaned, water removed, antifreeze added",
            "Winterization stickers filled (name/date)",
            "Stickers applied to all fixtures + front door/window",
            "Securing sticker placed on front door/window"
        ],
        # Add empty checklists for other types (can be filled later)
        "Grass Cut": [],
        "Initial Secure": [],
        "Initial Services": [],
        "Verify ICC": [],
        "Meet and Greet": [],
        "Eviction": [],
        "Bid Approvals": [],
        "Snow Removal": [],
        "Securing": [],
        "Bid Request(1st Time)": [],
    }
    
    def __init__(self, parent_frame, username=None, user_id=None):
        self.parent_frame = parent_frame
        self.username = username
        self.user_id = user_id
        self.current_view = "cards"  # Track current view: "cards" or "checklist"
        self.current_inspection_type = None
        
        # Use theme manager for colors
        self.colors = theme_manager.get_current_colors()
        
        # Data storage
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.checklist_storage_path = os.path.join(self.app_data_dir, "wo_inspection_checklists.json")
        
        # Initialize Supabase database
        import sys
        sys.stdout.flush()
        print(f"\n{'='*60}", flush=True)
        print(f"[WOInspectionModule.__init__] Initializing database connection...", flush=True)
        print(f"{'='*60}", flush=True)
        self.db = None
        self.supabase_client = None
        
        try:
            print(f"[WOInspectionModule.__init__] Step 1: Importing database_online...", flush=True)
            from database_online import OnlineDatabaseManager
            print(f"[WOInspectionModule.__init__] ✅ Import successful", flush=True)
            
            print(f"[WOInspectionModule.__init__] Step 2: Creating OnlineDatabaseManager instance...", flush=True)
            self.db = OnlineDatabaseManager()
            print(f"[WOInspectionModule.__init__] ✅ Database manager created: {type(self.db).__name__}", flush=True)
            print(f"[WOInspectionModule.__init__] Database object: {self.db}", flush=True)
            
            # Store supabase client reference for direct queries if needed
            if self.db:
                print(f"[WOInspectionModule.__init__] Checking for supabase attribute...")
                print(f"   - hasattr(self.db, 'supabase'): {hasattr(self.db, 'supabase')}")
                
                if hasattr(self.db, 'supabase'):
                    self.supabase_client = self.db.supabase
                    print(f"[WOInspectionModule.__init__] ✅ Supabase client available")
                    print(f"   - Client type: {type(self.supabase_client)}")
                    print(f"   - Client is None: {self.supabase_client is None}")
                    
                    # Test the connection
                    if self.supabase_client:
                        try:
                            test_result = self.db.supabase.table('users').select('id').limit(1).execute()
                            print(f"[WOInspectionModule.__init__] ✅ Database connection verified successfully")
                            print(f"[WOInspectionModule.__init__] Test query returned: {len(test_result.data) if test_result.data else 0} rows")
                        except Exception as test_e:
                            print(f"[WOInspectionModule.__init__] ⚠️ Database connection test failed: {test_e}")
                            print(f"   This might indicate RLS or permission issues")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[WOInspectionModule.__init__] ⚠️ Supabase client is None")
                else:
                    print(f"[WOInspectionModule.__init__] ⚠️ Database object has no 'supabase' attribute")
                    print(f"   Available attributes: {[attr for attr in dir(self.db) if not attr.startswith('_')][:10]}")
            else:
                print(f"[WOInspectionModule.__init__] ❌ Database manager is None after initialization")
                
        except ImportError as import_e:
            error_msg = f"[WOInspectionModule.__init__] ❌ Import Error: Could not import database_online\n   Error: {import_e}\n   Make sure database_online.py exists and dependencies are installed"
            print(error_msg, flush=True)
            import traceback
            traceback.print_exc()
            self.db = None
            self.supabase_client = None
            # Show user-friendly error
            try:
                messagebox.showerror("Database Connection Failed", 
                                   f"Could not import database module.\n\nError: {import_e}\n\nPlease check:\n1. database_online.py exists\n2. Dependencies are installed (pip install supabase)")
            except:
                pass
        except ConnectionError as conn_e:
            error_msg = f"[WOInspectionModule.__init__] ❌ Connection Error: {conn_e}"
            print(error_msg, flush=True)
            import traceback
            traceback.print_exc()
            self.db = None
            self.supabase_client = None
            # Show user-friendly error
            try:
                error_detail = str(conn_e)
                if "Invalid API key" in error_detail:
                    messagebox.showerror("Database Connection Failed", 
                                       f"Invalid Supabase API key.\n\nPlease check your config.py file.\n\nError: {error_detail}")
                elif "Connection" in error_detail or "timeout" in error_detail:
                    messagebox.showerror("Database Connection Failed", 
                                       f"Could not connect to Supabase.\n\nPlease check your internet connection.\n\nError: {error_detail}")
                else:
                    messagebox.showerror("Database Connection Failed", 
                                       f"Failed to connect to database.\n\nError: {error_detail}")
            except:
                pass
        except Exception as e:
            error_msg = f"[WOInspectionModule.__init__] ❌ Unexpected ERROR: {type(e).__name__}: {e}"
            print(error_msg, flush=True)
            import traceback
            traceback.print_exc()
            self.db = None
            self.supabase_client = None
            # Show user-friendly error
            try:
                messagebox.showerror("Database Connection Failed", 
                                   f"Unexpected error connecting to database.\n\nError: {type(e).__name__}: {e}\n\nCheck console for details.")
            except:
                pass
        
        print(f"[WOInspectionModule.__init__] Final state:", flush=True)
        print(f"   - self.db: {self.db}", flush=True)
        print(f"   - self.supabase_client: {self.supabase_client}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        # Load checklist states
        self.checklist_states = self.load_checklist_states()
        
        # Initialize checklist items in database if needed
        self.initialize_checklist_items_in_db()
        
        # UI Components
        self.create_ui()
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
    
    def initialize_checklist_items_in_db(self):
        """Initialize checklist items in database if they don't exist"""
        if not self.db:
            return
        
        try:
            # Check if Winterization checklist exists
            existing_items = self.db.get_checklist_items("Winterization")
            if not existing_items and "Winterization" in self.CHECKLISTS:
                # Save Winterization checklist to database
                winterization_items = self.CHECKLISTS["Winterization"]
                if winterization_items:
                    self.db.save_checklist_items("Winterization", winterization_items)
            
            # Note: Initial Secure and other checklists are now managed in the database
            # They should be added via SQL script (add_initial_secure_checklist.sql)
        except Exception as e:
            print(f"Error initializing checklist items: {e}")
    
    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        # Rebuild UI with new theme
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        self.create_ui()
    
    def create_ui(self):
        """Create main user interface with card-based layout"""
        # Get theme-appropriate colors
        card_bg = self.colors.get('white', '#FFFFFF')
        container_bg = self.colors.get('background', '#F5F7FA')
        
        # Main container with theme background (no extra padding since parent already has it)
        main_container = tk.Frame(self.parent_frame, bg=container_bg)
        main_container.pack(fill='both', expand=True)
        
        # Header section
        self.create_header(main_container)
        
        # Cards grid
        self.create_cards_grid(main_container)
        
        # Store container reference for theme updates
        self.main_container = main_container
    
    def create_header(self, parent):
        """Create header section"""
        container_bg = self.colors.get('background', '#F5F7FA')
        header_frame = tk.Frame(parent, bg=container_bg)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title
        tk.Label(header_frame, text="🔍 WO Inspection", 
                font=("Segoe UI", 24, "bold"),
                bg=container_bg, 
                fg=self.colors.get('text_primary', '#1F2937')).pack(side='left')
        
        # Button container on the right
        button_container = tk.Frame(header_frame, bg=container_bg)
        button_container.pack(side='right')
        
        # Database connection status indicator
        db_connected = self.db is not None and hasattr(self.db, 'supabase') and self.db.supabase is not None
        db_status_text = "🟢 DB Connected" if db_connected else "🔴 DB Disconnected"
        db_status_color = '#28a745' if db_connected else '#dc3545'
        db_status_label = tk.Label(button_container, text=db_status_text,
                                   font=("Segoe UI", 9, "bold"),
                                   bg=container_bg,
                                   fg=db_status_color)
        db_status_label.pack(side='right', padx=5)
        
        # Refresh button
        refresh_btn = tk.Button(button_container, text="🔄 Refresh from DB", font=("Segoe UI", 10),
                               bg=self.colors.get('primary_blue', '#1e3a5f'), fg='white',
                               relief='flat', cursor='hand2', padx=12, pady=4,
                               command=self.refresh_all_checklists_from_db)
        refresh_btn.pack(side='right', padx=5)
        refresh_btn.bind('<Enter>', lambda e: refresh_btn.configure(bg=self.colors.get('nav_hover', self.colors['primary_blue'])))
        refresh_btn.bind('<Leave>', lambda e: refresh_btn.configure(bg=self.colors.get('primary_blue', '#1e3a5f')))
        
        if self.username:
            tk.Label(button_container, text=f"User: {self.username}", 
                    font=("Segoe UI", 12),
                    bg=container_bg, 
                    fg=self.colors.get('text_secondary', '#6B7280')).pack(side='right', padx=10)
    
    def create_cards_grid(self, parent):
        """Create grid of inspection type cards"""
        container_bg = self.colors.get('background', '#F5F7FA')
        
        # Create a simple frame container with scrollable area
        # Use a Frame with Scrollbar for better compatibility
        outer_frame = tk.Frame(parent, bg=container_bg)
        outer_frame.pack(fill='both', expand=True)
        
        # Create scrollable frame using Frame + Scrollbar (simpler than Canvas)
        scroll_frame = tk.Frame(outer_frame, bg=container_bg)
        scroll_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Grid container for cards (4 columns)
        grid_frame = tk.Frame(scroll_frame, bg=container_bg)
        grid_frame.pack(fill='both', expand=True)
        
        # Configure grid columns
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1, uniform='card_col')
        
        # Create cards for each inspection type
        row, col = 0, 0
        for inspection_name, icon in self.INSPECTION_TYPES:
            self._create_inspection_card(grid_frame, row, col, icon, inspection_name, 
                                       lambda name=inspection_name: self.open_inspection_page(name))
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        # Configure grid rows
        for i in range(row + 1):
            grid_frame.grid_rowconfigure(i, weight=1)
        
        # Store reference
        self.grid_frame = grid_frame
    
    def _create_inspection_card(self, parent, row, col, icon, title, command):
        """Create a small card for an inspection type"""
        card_bg = self.colors.get('white', '#FFFFFF')
        shadow_color = self.colors.get('shadow_gray', self.colors.get('gray_light', '#D0D0D0'))
        container_bg = self.colors.get('background', '#F5F7FA')
        
        # Container cell - use pack instead of grid for simpler layout
        cell = tk.Frame(parent, bg=container_bg, relief='flat')
        cell.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # Card frame with border
        card = tk.Frame(cell, bg=card_bg, relief='solid', bd=1,
                        highlightthickness=1, highlightbackground=self.colors.get('gray_light', '#E5E7EB'))
        card.pack(fill='both', expand=True)
        
        inner = tk.Frame(card, bg=card_bg)
        inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Icon
        icon_label = tk.Label(inner, text=icon, font=("Segoe UI", 24), bg=card_bg)
        icon_label.pack(pady=(5, 10))
        
        # Title (wrap text if needed)
        title_label = tk.Label(inner, text=title, font=("Segoe UI", 11, "bold"),
                               bg=card_bg, fg=self.colors.get('text_primary', '#1F2937'),
                               wraplength=140, justify='center')
        title_label.pack()
        
        # Hover effects
        def on_enter(_e=None):
            card.configure(highlightbackground=self.colors.get('nav_hover', self.colors['primary_blue']),
                          highlightthickness=2)
        
        def on_leave(_e=None):
            card.configure(highlightbackground=self.colors.get('gray_light', '#E5E7EB'), 
                          highlightthickness=1)
        
        def handle_click(_e=None):
            try:
                command()
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to open: {ex}")
        
        # Bind recursively for smooth hover effects
        def bind_recursive(widget):
            widget.bind('<Enter>', lambda e: on_enter())
            widget.bind('<Leave>', lambda e: on_leave())
            widget.bind('<Button-1>', handle_click)
            widget.configure(cursor='hand2')
            for child in widget.winfo_children():
                bind_recursive(child)
        
        bind_recursive(cell)
    
    def open_inspection_page(self, inspection_name):
        """Open checklist page for the selected inspection type in a new window"""
        # Get root window from parent_frame
        root_window = self.parent_frame.winfo_toplevel()
        
        # Pre-load checklist items before opening window
        print(f"\n{'='*60}")
        print(f"[open_inspection_page] Opening checklist for: {inspection_name}")
        print(f"{'='*60}")
        
        # Verify database connection first
        print(f"[open_inspection_page] Database check:")
        print(f"  - self.db: {self.db}")
        print(f"  - self.db type: {type(self.db) if self.db else 'None'}")
        
        # If database is None, try to reinitialize
        if self.db is None:
            print(f"[open_inspection_page] ⚠️ Database is None! Attempting re-initialization...")
            try:
                from database_online import OnlineDatabaseManager
                self.db = OnlineDatabaseManager()
                if self.db and hasattr(self.db, 'supabase'):
                    self.supabase_client = self.db.supabase
                    print(f"[open_inspection_page] ✅ Database re-initialized successfully!")
                else:
                    print(f"[open_inspection_page] ❌ Re-initialization failed: no supabase client")
            except Exception as reinit_e:
                print(f"[open_inspection_page] ❌ Re-initialization failed: {reinit_e}")
                import traceback
                traceback.print_exc()
        
        if self.db:
            print(f"  - has get_checklist_items: {hasattr(self.db, 'get_checklist_items')}")
            print(f"  - has supabase: {hasattr(self.db, 'supabase')}")
            if hasattr(self.db, 'supabase'):
                print(f"  - supabase client: {self.db.supabase}")
        
        checklist_items_preload = []
        if self.db:
            try:
                print(f"[open_inspection_page] Calling get_checklist_items('{inspection_name}')...")
                checklist_items_preload = self.db.get_checklist_items(inspection_name)
                print(f"[open_inspection_page] ✅ Pre-loaded {len(checklist_items_preload)} items")
                if checklist_items_preload:
                    print(f"[open_inspection_page] First item: {checklist_items_preload[0][:50]}...")
                    print(f"[open_inspection_page] Last item: {checklist_items_preload[-1][:50]}...")
                else:
                    print(f"[open_inspection_page] ⚠️ WARNING: Query returned empty list!")
            except Exception as e:
                print(f"[open_inspection_page] ❌ Pre-load error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[open_inspection_page] ❌ No database connection available!")
            print(f"[open_inspection_page] self.db is None - database was not initialized")
        
        # Create new toplevel window
        checklist_window = tk.Toplevel(root_window)
        checklist_window.title(f"{inspection_name} Checklist")
        checklist_window.geometry("900x700")
        
        # Center window
        checklist_window.update_idletasks()
        x = (checklist_window.winfo_screenwidth() - 900) // 2
        y = (checklist_window.winfo_screenheight() - 700) // 2
        checklist_window.geometry(f"900x700+{x}+{y}")
        
        # Create checklist view in the new window (pass preloaded items as hint)
        print(f"[open_inspection_page] Passing {len(checklist_items_preload)} preloaded items to show_checklist_view")
        self.show_checklist_view(checklist_window, inspection_name, preloaded_items=checklist_items_preload)
    
    def show_checklist_view(self, parent_window, inspection_name, preloaded_items=None):
        """Show checklist view for an inspection type in the given window"""
        container_bg = self.colors.get('background', '#F5F7FA')
        card_bg = self.colors.get('white', '#FFFFFF')
        
        # Configure window background
        parent_window.configure(bg=container_bg)
        
        # Main container
        main_container = tk.Frame(parent_window, bg=container_bg)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header with back button
        header_frame = tk.Frame(main_container, bg=container_bg)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Close button
        close_btn = tk.Button(header_frame, text="✕ Close", font=("Segoe UI", 10),
                             bg=self.colors['primary_blue'], fg=self.colors['button_text'],
                             relief='flat', cursor='hand2', padx=10, pady=4,
                             command=parent_window.destroy)
        close_btn.pack(side='left')
        close_btn.bind('<Enter>', lambda e: close_btn.configure(bg=self.colors.get('nav_hover', self.colors['primary_blue'])))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(bg=self.colors['primary_blue']))
        
        # Title
        title_label = tk.Label(header_frame, text=f"📋 {inspection_name} Checklist",
                              font=("Segoe UI", 20, "bold"),
                              bg=container_bg,
                              fg=self.colors.get('text_primary', '#1F2937'))
        title_label.pack(side='left', padx=15)
        
        # Clear button
        clear_btn = tk.Button(header_frame, text="🗑️ Clear All", font=("Segoe UI", 10),
                             bg=self.colors.get('gray_dark', '#6B7280'), fg='white',
                             relief='flat', cursor='hand2', padx=12, pady=4,
                             command=lambda: self.clear_all_checklist_items(inspection_name, checklist_container, card_bg))
        clear_btn.pack(side='right', padx=5)
        clear_btn.bind('<Enter>', lambda e: clear_btn.configure(bg=self.colors.get('text_secondary', '#495057')))
        clear_btn.bind('<Leave>', lambda e: clear_btn.configure(bg=self.colors.get('gray_dark', '#6B7280')))
        
        # Card container for checklist
        card_frame = tk.Frame(main_container, bg=card_bg, relief='solid', bd=1,
                             highlightbackground=self.colors.get('gray_light', '#E5E7EB'),
                             highlightthickness=1)
        card_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Scrollable checklist area
        canvas = tk.Canvas(card_frame, bg=card_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(card_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=card_bg)
        
        def update_scrollregion(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", update_scrollregion)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def configure_canvas_width(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
            update_scrollregion()
        
        canvas.bind('<Configure>', configure_canvas_width)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Get checklist items from database (always try database first)
        checklist_items = []
        
        # Use preloaded items if available
        if preloaded_items and len(preloaded_items) > 0:
            checklist_items = preloaded_items
            print(f"[show_checklist_view] Using {len(checklist_items)} preloaded items")
        elif self.db:
            try:
                print(f"\n{'='*60}")
                print(f"Loading checklist for: '{inspection_name}'")
                print(f"{'='*60}")
                
                # Try to get items
                checklist_items = self.db.get_checklist_items(inspection_name)
                
                print(f"\n✅ Query completed. Retrieved {len(checklist_items)} items")
                if checklist_items:
                    print(f"   First item preview: {checklist_items[0][:60]}...")
                else:
                    print(f"   ⚠️ WARNING: Query returned empty list!")
                    print(f"   Attempting fallback query...")
                    
                    # Last resort: try direct query
                    if hasattr(self.db, 'supabase') and self.db.supabase:
                        try:
                            direct_result = self.db.supabase.table('wo_inspection_checklist_items')\
                                .select('item_text, item_order')\
                                .eq('inspection_type', inspection_name)\
                                .order('item_order', desc=False)\
                                .execute()
                            
                            if direct_result and direct_result.data:
                                sorted_data = sorted(direct_result.data, key=lambda x: x.get('item_order', 0))
                                checklist_items = [item['item_text'] for item in sorted_data]
                                print(f"   ✅ Fallback query successful! Loaded {len(checklist_items)} items")
                        except Exception as fallback_e:
                            print(f"   ❌ Fallback query also failed: {fallback_e}")
                    
            except Exception as e:
                print(f"\n❌ EXCEPTION loading checklist from database: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to hardcoded list if database fails
                checklist_items = self.CHECKLISTS.get(inspection_name, [])
                print(f"   Using {len(checklist_items)} hardcoded items as fallback")
        else:
            print("⚠️ Database not available, using hardcoded checklist")
            # Fallback to hardcoded list if no database
            checklist_items = self.CHECKLISTS.get(inspection_name, [])
        
        # Force reload if empty (last resort)
        if not checklist_items and self.db and hasattr(self.db, 'supabase') and self.db.supabase:
            print(f"[FORCE RELOAD] Attempting force reload for '{inspection_name}'...")
            try:
                force_result = self.db.supabase.table('wo_inspection_checklist_items')\
                    .select('item_text, item_order')\
                    .eq('inspection_type', inspection_name)\
                    .order('item_order', desc=False)\
                    .execute()
                
                if force_result and force_result.data:
                    sorted_force = sorted(force_result.data, key=lambda x: x.get('item_order', 0))
                    checklist_items = [item['item_text'] for item in sorted_force]
                    print(f"[FORCE RELOAD] ✅ Successfully loaded {len(checklist_items)} items via force reload!")
            except Exception as force_e:
                print(f"[FORCE RELOAD] ❌ Failed: {force_e}")
        
        print(f"\nFinal checklist_items count: {len(checklist_items)}")
        if checklist_items:
            print(f"First item: {checklist_items[0][:50]}...")
            print(f"Last item: {checklist_items[-1][:50]}...")
        print(f"{'='*60}\n")
        
        # Get saved state for this inspection type
        inspection_key = f"{inspection_name}_{self.user_id if self.user_id else 'default'}"
        saved_state = self.checklist_states.get(inspection_key, {})
        
        # Create checklist items
        self.checklist_vars = {}
        self.checklist_widgets = {}  # Store widget references for clearing
        checklist_container = tk.Frame(scrollable_frame, bg=card_bg)
        checklist_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Debug: Print right before checking
        print(f"[UI RENDER] About to render checklist. Item count: {len(checklist_items)}")
        print(f"[UI RENDER] checklist_items is empty: {not checklist_items}")
        print(f"[UI RENDER] checklist_items type: {type(checklist_items)}")
        if checklist_items:
            print(f"[UI RENDER] First item in list: {checklist_items[0][:30]}...")
        
        if not checklist_items:
            # No checklist items defined yet - show error message with details
            error_frame = tk.Frame(checklist_container, bg=card_bg)
            error_frame.pack(fill='x', padx=20, pady=20)
            
            tk.Label(error_frame,
                    text="No checklist items found for this inspection type.",
                    font=("Segoe UI", 12, "bold"),
                    bg=card_bg,
                    fg='#dc3545').pack(pady=(0, 10))
            
            details_text = f"Inspection Type: '{inspection_name}'\n\n"
            if self.db:
                details_text += "The database query returned 0 items.\n\nPlease:\n"
                details_text += "1. Click '🔄 Refresh from DB' button on main page\n"
                details_text += "2. Check console output for error messages\n"
                details_text += "3. Verify SQL script was executed in Supabase\n"
                details_text += "4. Run: python test_checklist_query.py to test database"
            else:
                details_text += "Database connection not available."
            
            tk.Label(error_frame,
                    text=details_text,
                    font=("Segoe UI", 10),
                    bg=card_bg,
                    fg=self.colors.get('text_secondary', '#6B7280'),
                    justify='left').pack()
        else:
            print(f"[UI RENDER] Starting to create {len(checklist_items)} checklist items...")
            for idx, item_text in enumerate(checklist_items):
                if idx < 3:  # Only log first 3 to avoid spam
                    print(f"[UI RENDER] Creating item {idx}: {item_text[:50]}...")
                # Checkbox state
                var = tk.BooleanVar(value=saved_state.get(str(idx), False))
                self.checklist_vars[idx] = var
                
                # Determine background color based on checked state
                is_checked = var.get()
                row_bg = '#d4edda' if is_checked else card_bg  # Green shade for checked
                
                # Create a frame for each checklist item
                item_frame = tk.Frame(checklist_container, bg=row_bg, relief='flat')
                item_frame.pack(fill='x', pady=2, padx=5)
                
                # Checkbox (visual representation)
                checkbox_frame = tk.Frame(item_frame, bg=row_bg, width=30, height=30)
                checkbox_frame.pack(side='left', padx=(10, 15))
                checkbox_frame.pack_propagate(False)
                
                checkbox_label = tk.Label(checkbox_frame,
                                         text="☐" if not var.get() else "☑",
                                         font=("Segoe UI", 18),
                                         bg=row_bg,
                                         fg=self.colors.get('text_primary', '#1F2937'))
                checkbox_label.pack(expand=True)
                
                # Item text (clickable)
                item_label = tk.Label(item_frame,
                                     text=item_text,
                                     font=("Segoe UI", 11),
                                     bg=row_bg,
                                     fg=self.colors.get('text_primary', '#1F2937'),
                                     anchor='w',
                                     cursor='hand2',
                                     wraplength=800)
                item_label.pack(side='left', fill='x', expand=True)
                
                # Click handler for the entire row
                def toggle_item(item_idx=idx, checkbox_lbl=checkbox_label, var_ref=var, frame=item_frame, txt_label=item_label):
                    def handler(event=None):
                        new_value = not var_ref.get()
                        var_ref.set(new_value)
                        checkbox_lbl.config(text="☑" if new_value else "☐")
                        
                        # Update background color (green shade for checked)
                        new_bg = '#d4edda' if new_value else card_bg
                        frame.config(bg=new_bg)
                        checkbox_lbl.config(bg=new_bg)
                        txt_label.config(bg=new_bg)
                        checkbox_frame.config(bg=new_bg)
                        
                        # Save state
                        self.save_checklist_state(inspection_name)
                    return handler
                
                # Bind click to both checkbox and text
                for widget in [checkbox_frame, checkbox_label, item_frame, item_label]:
                    widget.bind('<Button-1>', toggle_item())
                    widget.configure(cursor='hand2')
                
                # Store widget references for clearing
                self.checklist_widgets[idx] = {
                    'var': var,
                    'checkbox_label': checkbox_label,
                    'item_frame': item_frame,
                    'item_label': item_label,
                    'checkbox_frame': checkbox_frame,
                    'card_bg': card_bg
                }
            
            print(f"[UI RENDER] ✅ Created {len(self.checklist_widgets)} checklist item widgets")
        
        # Update scroll region
        main_container.update_idletasks()
        update_scrollregion()
        print(f"[UI RENDER] Scroll region updated. Checklist container has {len(checklist_container.winfo_children())} children")
        
        # Store references
        self.main_container = main_container
        self.canvas = canvas
        self.scrollable_frame = scrollable_frame
    
    def show_cards_view(self):
        """Return to cards view"""
        self.current_view = "cards"
        self.current_inspection_type = None
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        self.create_ui()
    
    def load_checklist_states(self):
        """Load saved checklist states from file"""
        try:
            if os.path.exists(self.checklist_storage_path):
                with open(self.checklist_storage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading checklist states: {e}")
        return {}
    
    def save_checklist_state(self, inspection_name):
        """Save current checklist state"""
        inspection_key = f"{inspection_name}_{self.user_id if self.user_id else 'default'}"
        
        # Build state dictionary
        state = {}
        for idx, var in self.checklist_vars.items():
            state[str(idx)] = var.get()
        
        # Update saved states
        self.checklist_states[inspection_key] = state
        
        # Save to file
        try:
            with open(self.checklist_storage_path, 'w') as f:
                json.dump(self.checklist_states, f, indent=2)
            
            # Also save to database if available
            if self.db and self.user_id:
                try:
                    inspection_data = {
                        'inspection_type': inspection_name,
                        'work_order': '',  # Can be added later if needed
                        'inspection_data': state,
                        'status': 'in_progress' if any(state.values()) else 'pending'
                    }
                    self.db.save_wo_inspection(self.user_id, inspection_data)
                except Exception as e:
                    print(f"Error saving to database: {e}")
        except Exception as e:
            print(f"Error saving checklist state: {e}")
    
    def clear_all_checklist_items(self, inspection_name, checklist_container, card_bg):
        """Clear all checked items in the checklist"""
        # Uncheck all items and update visuals
        for idx, widget_info in self.checklist_widgets.items():
            widget_info['var'].set(False)
            widget_info['checkbox_label'].config(text="☐")
            
            # Reset background color to default
            widget_info['item_frame'].config(bg=card_bg)
            widget_info['checkbox_label'].config(bg=card_bg)
            widget_info['item_label'].config(bg=card_bg)
            widget_info['checkbox_frame'].config(bg=card_bg)
        
        # Save cleared state
        self.save_checklist_state(inspection_name)
    
    def refresh_all_checklists_from_db(self):
        """Refresh all checklist items from database and show status"""
        from tkinter import messagebox
        
        if not self.db:
            messagebox.showerror("Database Error", "Database connection not available. Cannot refresh from database.")
            return
        
        try:
            # Check all inspection types and see what's in the database
            inspection_status = {}
            
            for inspection_name, icon in self.INSPECTION_TYPES:
                checklist_items = self.db.get_checklist_items(inspection_name)
                inspection_status[inspection_name] = {
                    'count': len(checklist_items),
                    'items': checklist_items
                }
            
            # Build status message
            status_lines = ["Database Refresh Status:\n"]
            for inspection_name, status in inspection_status.items():
                count = status['count']
                if count > 0:
                    status_lines.append(f"✅ {inspection_name}: {count} items")
                else:
                    status_lines.append(f"❌ {inspection_name}: No items found")
            
            # Check specifically for Initial Secure
            initial_secure_items = inspection_status.get("Initial Secure", {}).get('items', [])
            if not initial_secure_items:
                status_lines.append("\n⚠️ Initial Secure Issue:")
                status_lines.append("   The inspection type name must match exactly.")
                status_lines.append("   Check database for inspection_type = 'Initial Secure'")
                status_lines.append("   (case-sensitive)")
            
            messagebox.showinfo("Refresh Status", "\n".join(status_lines))
            
            # Print detailed info to console
            print("\n=== Checklist Database Status ===")
            for inspection_name, status in inspection_status.items():
                print(f"{inspection_name}: {status['count']} items")
                if status['items']:
                    print(f"  First item: {status['items'][0][:50]}...")
            print("=" * 40)
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to refresh checklists:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            messagebox.showerror("Refresh Error", error_msg)
            print(error_msg)
