# special_contractor_price_module.py
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from datetime import datetime
from theme_manager import theme_manager
import os
import json
import copy

class SpecialContractorPriceModule:
    def __init__(self, parent_frame, username=None, user_id=None, colors=None, db=None):
        self.parent_frame = parent_frame
        self.username = username
        self.user_id = user_id
        self.colors = colors or theme_manager.get_current_colors()
        self.db = db
        
        # Initialize database if not provided
        if not self.db:
            try:
                from database_online import OnlineDatabaseManager
                self.db = OnlineDatabaseManager()
            except Exception as e:
                print(f"Warning: Could not initialize database: {e}")
                self.db = None
        
        # Load contractors data
        self.contractors_data = {}  # {contractor_name: {'id': int, 'line_items': [...], 'updated_by': int, 'updated_at': str}}
        self.all_contractors_data = {}  # Store all contractors for filtering
        
        # Local cache file path
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = os.path.join(cache_dir, 'special_contractors_cache.json')
        
        # Setup UI first for fast opening
        self.setup_ui()
        
        # Load contractors after UI is ready (non-blocking)
        self.parent_frame.after(10, self.load_contractors)
    
    def setup_ui(self):
        """Setup the UI for Special Contractor Price module."""
        # Clear parent frame
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Main container - fill entire window
        main_container = tk.Frame(self.parent_frame, bg=self.colors['background'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header with Add button
        header_frame = tk.Frame(main_container, bg=self.colors['background'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="Special Contractor Prices", 
                              font=("Arial", 20, "bold"),
                              bg=self.colors['background'],
                              fg='#333333')
        title_label.pack(side='left')
        
        add_button = tk.Button(header_frame, text="+ Add Contractor", 
                              font=("Arial", 11),
                              bg='#2196F3',
                              fg='white',
                              relief='flat',
                              cursor='hand2',
                              padx=15, pady=8,
                              command=self.add_contractor_dialog)
        add_button.pack(side='right')
        
        # Search bar - centered and focused
        search_container = tk.Frame(main_container, bg=self.colors['background'])
        search_container.pack(fill='x', pady=(0, 20))
        
        # Center the search bar with a fixed width container
        search_wrapper = tk.Frame(search_container, bg=self.colors['background'])
        search_wrapper.pack(expand=True)
        
        search_inner_frame = tk.Frame(search_wrapper, bg='#ffffff', 
                                     relief='solid', bd=1,
                                     highlightbackground='#e0e0e0',
                                     highlightthickness=1)
        search_inner_frame.pack(padx=10, pady=5)
        
        search_label = tk.Label(search_inner_frame, text="Search", 
                               font=("Arial", 10, "bold"),
                               bg='#ffffff',
                               fg='#333333')
        search_label.pack(side='left', padx=(15, 10), pady=10)
        
        self.search_var = tk.StringVar()
        # Debounce search to avoid refreshing on every keystroke
        self.search_debounce_timer = None
        self.search_var.trace('w', lambda *args: self._debounced_filter())
        search_entry = tk.Entry(search_inner_frame, textvariable=self.search_var,
                               font=("Arial", 11),
                               bg='#ffffff',
                               fg='#333333',
                               relief='flat',
                               bd=0,
                               width=50)
        search_entry.pack(side='left', padx=(0, 10), pady=10)
        search_entry.insert(0, "Type contractor name...")
        search_entry.config(fg='#999999')
        
        def on_search_focus_in(event):
            if search_entry.get() == "Type contractor name...":
                search_entry.delete(0, tk.END)
                search_entry.config(fg='#333333')
        
        def on_search_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, "Type contractor name...")
                search_entry.config(fg='#999999')
        
        search_entry.bind('<FocusIn>', on_search_focus_in)
        search_entry.bind('<FocusOut>', on_search_focus_out)
        
        clear_search_btn = tk.Button(search_inner_frame, text="Clear", 
                                    font=("Arial", 10),
                                    bg='#757575',
                                    fg='white',
                                    relief='flat',
                                    cursor='hand2',
                                    padx=12, pady=6,
                                    command=lambda: [self.search_var.set(''), 
                                                    search_entry.delete(0, tk.END),
                                                    search_entry.insert(0, "Type contractor name..."),
                                                    search_entry.config(fg='#999999')])
        clear_search_btn.pack(side='left', padx=(0, 15), pady=10)
        
        # Store search entry for focus management
        self.search_entry = search_entry
        
        # Set up global key binding to route typing to search when no field has focus
        def route_to_search(event):
            # Check if focus is on a text entry field
            focused_widget = self.parent_frame.focus_get()
            if focused_widget:
                # If focus is on Text or Entry widget, let it handle the input
                if isinstance(focused_widget, (tk.Text, tk.Entry)):
                    return  # Let the widget handle it
            
            # Otherwise, route to search
            if hasattr(self, 'search_entry'):
                self.search_entry.focus_set()
                # Insert the typed character
                if event.char and event.char.isprintable():
                    current_text = self.search_entry.get()
                    if current_text == "Type contractor name...":
                        self.search_entry.delete(0, tk.END)
                        self.search_entry.config(fg='#333333')
                    self.search_entry.insert(tk.INSERT, event.char)
                return "break"
        
        # Bind key events to parent frame
        self.parent_frame.bind('<KeyPress>', route_to_search)
        
        # Scrollable content area
        canvas_frame = tk.Frame(main_container, bg=self.colors['background'])
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.colors['background'], highlightthickness=0)
        # Enable smooth scrolling with fine increments
        canvas.configure(yscrollincrement=1)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_content = tk.Frame(canvas, bg=self.colors['background'])
        
        scrollable_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def configure_canvas_width(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        canvas.bind('<Configure>', configure_canvas_width)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Ultra-fast mouse wheel scrolling - maximum speed for quick navigation
        def on_canvas_scroll(event):
            # Check if mouse is over a Text widget - if so, don't scroll the page
            widget_under_mouse = event.widget.winfo_containing(event.x_root, event.y_root)
            if widget_under_mouse:
                current = widget_under_mouse
                while current:
                    if isinstance(current, tk.Text):
                        return  # Don't scroll page if over Text widget
                    current = current.master if hasattr(current, 'master') else None
            
            if canvas.winfo_containing(event.x_root, event.y_root):
                # Ultra-fast scrolling - very large scroll amount for maximum speed
                # Small scroll will move very large amount of page
                scroll_amount = max(30, min(100, abs(event.delta) // 4))
                if event.delta > 0:
                    canvas.yview_scroll(-scroll_amount, "units")
                else:
                    canvas.yview_scroll(scroll_amount, "units")
        
        def on_content_scroll(event):
            # Check if mouse is over a Text widget - if so, don't scroll the page
            widget_under_mouse = event.widget.winfo_containing(event.x_root, event.y_root)
            if widget_under_mouse:
                current = widget_under_mouse
                while current:
                    if isinstance(current, tk.Text):
                        return  # Don't scroll page if over Text widget
                    current = current.master if hasattr(current, 'master') else None
            
            # Ultra-fast scrolling - very large scroll amount for maximum speed
            # Small scroll will move very large amount of page
            scroll_amount = max(30, min(100, abs(event.delta) // 4))
            if event.delta > 0:
                canvas.yview_scroll(-scroll_amount, "units")
            else:
                canvas.yview_scroll(scroll_amount, "units")
        
        # Bind mouse wheel events
        canvas.bind("<MouseWheel>", on_canvas_scroll)
        scrollable_content.bind("<MouseWheel>", on_content_scroll)
        
        # Also bind to all child widgets, but skip Text widgets
        def bind_scroll_to_widgets(widget):
            # Don't bind scroll to Text widgets - they handle their own scrolling
            if not isinstance(widget, tk.Text):
                widget.bind("<MouseWheel>", on_content_scroll)
            for child in widget.winfo_children():
                bind_scroll_to_widgets(child)
        
        self.scrollable_content = scrollable_content
        self.canvas = canvas
        self.bind_scroll_to_widgets = bind_scroll_to_widgets
    
    def load_contractors(self):
        """Load all contractors from database, with fallback to local cache."""
        # Show loading state
        if hasattr(self, 'scrollable_content'):
            for widget in self.scrollable_content.winfo_children():
                widget.destroy()
            loading_label = tk.Label(self.scrollable_content, 
                                    text="Loading contractors...",
                                    font=("Arial", 12),
                                    bg=self.colors['background'],
                                    fg=self.colors['gray_medium'])
            loading_label.pack(pady=50)
            self.scrollable_content.update_idletasks()
        
        # Try to load from database first
        db_success = False
        if self.db:
            try:
                # Load contractors from database
                contractors = self.db.get_all_special_contractors()
                self.contractors_data = {}
                
                # Load in batches for better performance
                for contractor in contractors:
                    contractor_id = contractor['id']
                    contractor_name = contractor['contractor_name']
                    # Load line items
                    line_items = self.db.get_contractor_line_items(contractor_id)
                    
                    self.contractors_data[contractor_name] = {
                        'id': contractor_id,
                        'line_items': line_items,
                        'updated_by': contractor.get('updated_by'),
                        'updated_at': contractor.get('updated_at')
                    }
                
                # Store all contractors for filtering (deep copy to avoid shared references)
                self.all_contractors_data = copy.deepcopy(self.contractors_data)
                
                # Save to local cache after successful database load
                self.save_to_cache()
                db_success = True
                
            except Exception as e:
                print(f"Error loading contractors from database: {e}")
                db_success = False
        
        # If database load failed, try to load from local cache
        cache_data = None
        if not db_success:
            cache_data = self.load_from_cache()
            if cache_data:
                self.contractors_data = cache_data
                self.all_contractors_data = copy.deepcopy(self.contractors_data)
            else:
                # No cache available, show empty state
                self.contractors_data = {}
                self.all_contractors_data = {}
        
        # Display contractors
        self.display_contractors()
        
        # Show notification if using cached data
        if not db_success and cache_data:
            messagebox.showinfo("Offline Mode", 
                              "No internet connection. Showing last saved data from local cache.")
    
    def save_to_cache(self):
        """Save contractors data to local cache file."""
        try:
            cache_data = {
                'contractors_data': self.contractors_data,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to local cache: {self.cache_file}")
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def load_from_cache(self):
        """Load contractors data from local cache file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    contractors_data = cache_data.get('contractors_data', {})
                    saved_at = cache_data.get('saved_at', 'Unknown')
                    print(f"Loaded data from local cache (saved at: {saved_at})")
                    return contractors_data
            return None
        except Exception as e:
            print(f"Error loading from cache: {e}")
            return None
    
    def display_contractors(self):
        """Display all contractors in the UI."""
        # Check if scrollable_content exists
        if not hasattr(self, 'scrollable_content'):
            return
        
        # Save scroll position before clearing
        scroll_position = 0
        if hasattr(self, 'canvas'):
            try:
                scroll_position = self.canvas.yview()[0]
            except:
                pass
        
        # Clear existing content
        for widget in self.scrollable_content.winfo_children():
            widget.destroy()
        
        # Update canvas to clear any old content
        self.canvas.update_idletasks()
        
        if not self.contractors_data:
            no_data_label = tk.Label(self.scrollable_content, 
                                    text="No contractors added yet. Click 'Add Contractor' to get started.",
                                    font=("Arial", 12),
                                    bg=self.colors['background'],
                                    fg=self.colors['gray_medium'])
            no_data_label.pack(pady=50)
            # Bind scroll to the label
            if hasattr(self, 'bind_scroll_to_widgets'):
                self.bind_scroll_to_widgets(no_data_label)
            return
        
        # Display each contractor
        for contractor_name, contractor_info in sorted(self.contractors_data.items()):
            self.create_contractor_section(contractor_name, contractor_info)
        
        # Bind scroll to all widgets
        if hasattr(self, 'bind_scroll_to_widgets'):
            self.bind_scroll_to_widgets(self.scrollable_content)
        
        # Restore scroll position after update
        if hasattr(self, 'canvas') and scroll_position > 0:
            self.canvas.update_idletasks()
            try:
                self.canvas.yview_moveto(scroll_position)
            except:
                pass
        
        # Update canvas scroll region
        if hasattr(self, 'canvas'):
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def create_contractor_section(self, contractor_name, contractor_info):
        """Create a section for a contractor with its line items."""
        # Contractor header frame - professional gray
        header_frame = tk.Frame(self.scrollable_content, bg='#f5f5f5', height=50, relief='solid', bd=1)
        header_frame.pack(fill='x', pady=(10, 0))
        header_frame.pack_propagate(False)
        
        # Contractor name (centered)
        name_label = tk.Label(header_frame, text=contractor_name.title(),
                             font=("Arial", 14, "bold"),
                             bg='#f5f5f5',
                             fg='#333333')
        name_label.pack(expand=True, pady=15)
        
        # Updated by info (right)
        updated_info = self.get_updated_info(contractor_info.get('updated_by'), 
                                            contractor_info.get('updated_at'))
        updated_label = tk.Label(header_frame, text=updated_info,
                                font=("Arial", 10),
                                bg='#f5f5f5',
                                fg='#666666')
        updated_label.pack(side='right', padx=15, pady=15)
        
        # Table frame - simple border
        table_frame = tk.Frame(self.scrollable_content, bg='#ffffff', relief='solid', bd=1)
        table_frame.pack(fill='x', padx=0, pady=(0, 0))
        
        # Table header - subtle gray background
        header_row = tk.Frame(table_frame, bg='#f8f8f8', height=40, relief='solid', bd=0)
        header_row.pack(fill='x')
        header_row.pack_propagate(False)
        
        line_item_header = tk.Label(header_row, text="Line Item",
                                    font=("Arial", 11, "bold"),
                                    bg='#f8f8f8',
                                    fg='#333333')
        line_item_header.pack(side='left', padx=15, pady=10, fill='x', expand=True)
        
        price_header = tk.Label(header_row, text="Price",
                                font=("Arial", 11, "bold"),
                                bg='#f8f8f8',
                                fg='#333333',
                                width=15)
        price_header.pack(side='left', padx=10, pady=10)
        
        actions_header = tk.Label(header_row, text="Actions",
                                 font=("Arial", 11, "bold"),
                                 bg='#f8f8f8',
                                 fg='#333333',
                                 width=10)
        actions_header.pack(side='left', padx=10, pady=10)
        
        # Line items
        line_items = contractor_info.get('line_items', [])
        if not line_items:
            # Empty state - improved styling
            empty_container = tk.Frame(table_frame, bg=self.colors['white'])
            empty_container.pack(fill='both', expand=True, pady=40, padx=20)
            
            # Empty state icon/text
            empty_label = tk.Label(empty_container, 
                                  text="No line items added yet",
                                  font=("Arial", 11),
                                  bg='#ffffff',
                                  fg='#999999',
                                  pady=20)
            empty_label.pack()
        else:
            for idx, item in enumerate(line_items):
                # Add divider before each row except the first
                if idx > 0:
                    divider = tk.Frame(table_frame, bg='#e0e0e0', height=1)
                    divider.pack(fill='x', padx=0, pady=0)
                # Create row for each line item
                self.create_line_item_row(table_frame, contractor_name, item)
        
        # Action buttons frame - moved outside table for better visibility
        buttons_frame = tk.Frame(self.scrollable_content, bg=self.colors['background'])
        buttons_frame.pack(fill='x', padx=0, pady=(0, 10))
        
        # Add line item button - professional styling
        add_line_item_btn = tk.Button(buttons_frame, text="+ Add Line Item",
                                     font=("Arial", 10),
                                     bg='#2196F3',
                                     fg='white',
                                     relief='flat',
                                     cursor='hand2',
                                     padx=12, pady=6,
                                     command=lambda name=contractor_name: self.add_line_item_dialog(name))
        add_line_item_btn.pack(side='left', padx=(0, 10))
        
        # Delete contractor button - professional styling
        delete_contractor_btn = tk.Button(buttons_frame, text="Delete Contractor",
                                          font=("Arial", 10),
                                          bg='#757575',
                                          fg='white',
                                          relief='flat',
                                          cursor='hand2',
                                          padx=12, pady=6,
                                          command=lambda name=contractor_name, cid=contractor_info['id']: 
                                          self.delete_contractor(name, cid))
        delete_contractor_btn.pack(side='right')
    
    def create_line_item_row(self, parent_frame, contractor_name, item):
        """Create a row for a line item."""
        row_frame = tk.Frame(parent_frame, bg='#ffffff')
        row_frame.pack(fill='x', padx=0, pady=0)
        
        # Line item (editable with text wrapping) - slightly reduced width, dynamic height
        line_item_text = tk.Text(row_frame, 
                                font=("Arial", 13),
                                bg='#ffffff',
                                fg='#333333',
                                   relief='flat',
                                bd=0,
                                wrap=tk.WORD,
                                width=36,  # Reduced by ~10% from 40
                                padx=5,
                                pady=5)
        initial_content = item.get('line_item', '')
        line_item_text.insert('1.0', initial_content)
        
        # Auto-resize height based on content
        def update_height(event=None):
            # Get the number of lines in the text widget
            line_count = int(line_item_text.index('end-1c').split('.')[0])
            if line_count < 1:
                line_count = 1
            # Set height to match content
            line_item_text.config(height=line_count)
            # Update canvas scroll region
            if hasattr(self, 'canvas'):
                self.canvas.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        line_item_text.bind('<KeyRelease>', update_height)
        line_item_text.bind('<FocusIn>', update_height)
        update_height()  # Initial height calculation
        
        # Prevent page scrolling when scrolling inside Text widget
        def on_text_scroll(event):
            # Allow Text widget to scroll, but prevent event from bubbling up
            if event.delta:
                line_item_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"  # Stop event propagation
        
        line_item_text.bind("<MouseWheel>", on_text_scroll)
        
        # Ensure text field takes focus when clicked and updates height
        def on_text_click(event):
            line_item_text.focus_set()
            update_height(event)
            return None  # Allow default behavior
        
        line_item_text.bind('<Button-1>', on_text_click)
        
        line_item_text.pack(side='left', padx=15, pady=10, fill='x', expand=True)
        
        # Price (editable) - slightly increased width
        price_var = tk.StringVar(value=f"${item.get('price', 0):.2f}")
        price_entry = tk.Entry(row_frame, textvariable=price_var,
                              font=("Arial", 13),
                              bg='#ffffff',
                              fg='#333333',
                              relief='flat',
                              bd=0,
                              width=15)
        # Ensure price field takes focus when clicked
        def on_price_click(event):
            price_entry.focus_set()
        price_entry.bind('<Button-1>', on_price_click)
        # Ensure price field takes focus when clicked
        def on_price_click(event):
            price_entry.focus_set()
            return None  # Allow default behavior
        price_entry.bind('<Button-1>', on_price_click)
        
        price_entry.pack(side='left', padx=10, pady=10)
        
        # Actions - formal classic buttons stacked vertically
        actions_frame = tk.Frame(row_frame, bg='#ffffff')
        actions_frame.pack(side='left', padx=10, pady=10)
        
        # Update button - formal classic style with update icon
        save_btn = tk.Button(actions_frame, text="✎",
                            font=("Arial", 12),
                            bg='#5a5a5a',
                            fg='white',
                            relief='raised',
                            bd=1,
                            cursor='hand2',
                            padx=6, pady=3,
                            width=3,
                            command=lambda: self.save_line_item(
                                item['id'], 
                                line_item_text.get('1.0', tk.END).strip(), 
                                price_var.get(),
                                contractor_name
                            ))
        save_btn.pack(side='top', padx=2, pady=2)
        
        # Delete button - formal classic style with delete icon
        delete_btn = tk.Button(actions_frame, text="🗑",
                               font=("Arial", 10),
                               bg='#5a5a5a',
                               fg='white',
                               relief='raised',
                               bd=1,
                               cursor='hand2',
                               padx=6, pady=3,
                               width=3,
                               command=lambda: self.delete_line_item(item['id'], contractor_name))
        delete_btn.pack(side='top', padx=2, pady=2)
    
    def get_updated_info(self, updated_by_user_id, updated_at_str):
        """Get formatted 'Updated by' information."""
        if not updated_by_user_id or not updated_at_str:
            return "Updated by: Unknown"
        
        try:
            # Get username
            if self.db:
                user = self.db.get_user_by_id(updated_by_user_id)
                username = user.get('username', 'Unknown') if user else 'Unknown'
            else:
                username = 'Unknown'
            
            # Format date
            if updated_at_str:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                    date_str = dt.strftime('%m/%d/%Y')
                except:
                    date_str = updated_at_str[:10] if len(updated_at_str) >= 10 else updated_at_str
            else:
                date_str = 'Unknown'
            
            return f"{username}, {date_str}"
        except Exception as e:
            print(f"Error getting updated info: {e}")
            return "Updated by: Unknown"
    
    def add_contractor_dialog(self):
        """Dialog to add a new contractor - custom professional UI."""
        # Create custom dialog window
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add Contractor")
        dialog.geometry("450x200")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Make dialog modal
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Header section
        header_frame = tk.Frame(dialog, bg='#f5f5f5', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Add New Contractor",
                              font=("Arial", 16, "bold"),
                              bg='#f5f5f5',
                              fg='#333333')
        title_label.pack(pady=20)
        
        # Content section
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Label
        label = tk.Label(content_frame, text="Contractor Name:",
                        font=("Arial", 11),
                        bg='#ffffff',
                        fg='#333333',
                        anchor='w')
        label.pack(fill='x', pady=(0, 8))
        
        # Input field
        entry_var = tk.StringVar()
        entry = tk.Entry(content_frame, textvariable=entry_var,
                        font=("Arial", 12),
                        bg='#ffffff',
                        fg='#333333',
                        relief='solid',
                        bd=1,
                        highlightthickness=1,
                        highlightcolor='#2196F3',
                        highlightbackground='#e0e0e0',
                        width=40)
        entry.pack(fill='x', pady=(0, 20))
        entry.focus_set()
        
        # Buttons section
        buttons_frame = tk.Frame(content_frame, bg='#ffffff')
        buttons_frame.pack(fill='x')
        
        result = {'value': None}
        
        def on_ok():
            name = entry_var.get().strip()
            if name:
                result['value'] = name
                dialog.destroy()
            else:
                entry.config(highlightcolor='#f44336', highlightbackground='#f44336')
                dialog.after(500, lambda: entry.config(highlightcolor='#2196F3', highlightbackground='#e0e0e0'))
        
        def on_cancel():
            dialog.destroy()
        
        def on_enter(event):
            on_ok()
        
        entry.bind('<Return>', on_enter)
        entry.bind('<Escape>', lambda e: on_cancel())
        
        # OK button
        ok_btn = tk.Button(buttons_frame, text="Add Contractor",
                          font=("Arial", 11, "bold"),
                          bg='#2196F3',
                          fg='white',
                          relief='flat',
                          cursor='hand2',
                          padx=20, pady=8,
                          command=on_ok)
        ok_btn.pack(side='right', padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(buttons_frame, text="Cancel",
                              font=("Arial", 11),
                              bg='#f5f5f5',
                              fg='#666666',
                              relief='flat',
                              cursor='hand2',
                              padx=20, pady=8,
                              command=on_cancel)
        cancel_btn.pack(side='right')
        
        # Wait for dialog to close
        dialog.wait_window()
        
        contractor_name = result['value']
        if not contractor_name:
            return
        
        contractor_name = contractor_name.strip()
        
        # Check if contractor already exists in database
        if self.db:
            existing = self.db.get_special_contractor(contractor_name)
            if existing:
                messagebox.showinfo("Contractor Exists", 
                                 f"Contractor '{contractor_name}' already exists. You can add line items to it.")
                # Refresh to show existing contractor
                self.load_contractors()
                return
        
        # Create contractor in database
        if self.db and self.user_id:
            try:
                contractor = self.db.create_special_contractor(contractor_name, self.user_id)
                if contractor:
                    new_contractor = {
                        'id': contractor['id'],
                        'line_items': [],
                        'updated_by': self.user_id,
                        'updated_at': datetime.now().isoformat()
                    }
                    self.contractors_data[contractor_name] = new_contractor
                    self.all_contractors_data[contractor_name] = copy.deepcopy(new_contractor)
                    self.save_to_cache()  # Save to local cache
                    self.display_contractors()
                else:
                    messagebox.showerror("Error", "Failed to create contractor.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add contractor: {e}")
        else:
            # Local storage fallback
            if contractor_name not in self.contractors_data:
                new_contractor = {
                    'id': None,
                    'line_items': [],
                    'updated_by': self.user_id,
                    'updated_at': datetime.now().isoformat()
                }
                self.contractors_data[contractor_name] = new_contractor
                self.all_contractors_data[contractor_name] = new_contractor
                self.display_contractors()
    
    def add_line_item_dialog(self, contractor_name):
        """Dialog to add a new line item to a contractor - custom professional UI."""
        if contractor_name not in self.contractors_data:
            return
        
        # Create custom dialog window
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add Line Item")
        dialog.geometry("520x380")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Make dialog modal
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Header section
        header_frame = tk.Frame(dialog, bg='#f5f5f5', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Add Line Item",
                              font=("Arial", 16, "bold"),
                              bg='#f5f5f5',
                              fg='#333333')
        title_label.pack(pady=20)
        
        # Content section with better spacing
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=35, pady=20)
        
        result = {'line_item': None, 'price': None}
        
        # Line Item field with better spacing
        line_item_label = tk.Label(content_frame, text="Line Item Description:",
                                  font=("Arial", 11, "bold"),
                                  bg='#ffffff',
                                  fg='#333333',
                                  anchor='w')
        line_item_label.pack(fill='x', pady=(0, 10))
        
        line_item_var = tk.StringVar()
        line_item_entry = tk.Text(content_frame,
                                  font=("Arial", 11),
                                  bg='#ffffff',
                                  fg='#333333',
                                  relief='solid',
                                  bd=1,
                                  highlightthickness=1,
                                  highlightcolor='#2196F3',
                                  highlightbackground='#e0e0e0',
                                  width=45,
                                  height=4,
                                  wrap=tk.WORD,
                                  padx=8,
                                  pady=8)
        line_item_entry.pack(fill='x', pady=(0, 15))
        line_item_entry.focus_set()
        
        # Price field with dollar sign - better layout
        price_label = tk.Label(content_frame, text="Price:",
                              font=("Arial", 11, "bold"),
                              bg='#ffffff',
                              fg='#333333',
                              anchor='w')
        price_label.pack(fill='x', pady=(0, 10))
        
        # Price input frame with dollar sign prefix
        price_frame = tk.Frame(content_frame, bg='#ffffff')
        price_frame.pack(fill='x', pady=(0, 20))
        
        # Dollar sign prefix
        dollar_label = tk.Label(price_frame, text="$",
                               font=("Arial", 12, "bold"),
                               bg='#ffffff',
                               fg='#333333')
        dollar_label.pack(side='left', padx=(0, 8), pady=5)
        
        price_var = tk.StringVar()
        price_entry = tk.Entry(price_frame, textvariable=price_var,
                              font=("Arial", 11),
                              bg='#ffffff',
                              fg='#333333',
                              relief='solid',
                              bd=1,
                              highlightthickness=1,
                              highlightcolor='#2196F3',
                              highlightbackground='#e0e0e0',
                              width=35)
        price_entry.pack(side='left', fill='x', expand=True)
        price_entry.insert(0, "0.00")
        
        # Buttons section - better positioned
        buttons_frame = tk.Frame(content_frame, bg='#ffffff')
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        def on_ok():
            line_item = line_item_entry.get('1.0', tk.END).strip()
            price_str = price_var.get().strip()
            
            if not line_item:
                line_item_entry.config(highlightcolor='#f44336', highlightbackground='#f44336')
                dialog.after(500, lambda: line_item_entry.config(highlightcolor='#2196F3', highlightbackground='#e0e0e0'))
                return
            
            if not price_str:
                price_entry.config(highlightcolor='#f44336', highlightbackground='#f44336')
                dialog.after(500, lambda: price_entry.config(highlightcolor='#2196F3', highlightbackground='#e0e0e0'))
                return
            
            result['line_item'] = line_item
            result['price'] = price_str
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        def on_enter(event):
            on_ok()
        
        price_entry.bind('<Return>', on_enter)
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # Cancel button (left side)
        cancel_btn = tk.Button(buttons_frame, text="Cancel",
                              font=("Arial", 11),
                              bg='#f5f5f5',
                              fg='#666666',
                              relief='flat',
                              cursor='hand2',
                              padx=25, pady=10,
                              command=on_cancel)
        cancel_btn.pack(side='left')
        
        # OK button (right side)
        ok_btn = tk.Button(buttons_frame, text="Add Line Item",
                          font=("Arial", 11, "bold"),
                          bg='#2196F3',
                          fg='white',
                          relief='flat',
                          cursor='hand2',
                          padx=25, pady=10,
                          command=on_ok)
        ok_btn.pack(side='right')
        
        # Wait for dialog to close
        dialog.wait_window()
        
        line_item = result['line_item']
        price_str = result['price']
        
        if not line_item or not price_str:
            return
        
        try:
            price = float(price_str.replace('$', '').replace(',', ''))
        except ValueError:
            messagebox.showerror("Invalid Price", "Please enter a valid price.")
            return
        
        contractor_info = self.contractors_data.get(contractor_name)
        if not contractor_info:
            return
        
        contractor_id = contractor_info['id']
        
        if self.db and self.user_id and contractor_id:
            try:
                # Add new line item to database
                new_item = self.db.add_contractor_line_item(contractor_id, line_item.strip(), price, self.user_id)
                if new_item:
                    # Reload ALL line items from database to ensure we have complete, up-to-date data
                    updated_line_items = self.db.get_contractor_line_items(contractor_id)
                    
                    # Create fresh contractor info with updated line items
                    updated_contractor_info = {
                        'id': contractor_id,
                        'line_items': updated_line_items,
                        'updated_by': self.user_id,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Update both dictionaries with fresh data (no shared references)
                    import copy
                    self.contractors_data[contractor_name] = copy.deepcopy(updated_contractor_info)
                    self.all_contractors_data[contractor_name] = copy.deepcopy(updated_contractor_info)
                    
                    # Verify we have all items (debugging)
                    print(f"[DEBUG] Added line item. Total items for '{contractor_name}': {len(updated_line_items)}")
                    if updated_line_items:
                        for idx, item in enumerate(updated_line_items):
                            print(f"  Item {idx+1} (ID: {item.get('id')}): '{item.get('line_item', '')[:30]}...' - ${item.get('price', 0)}")
                    else:
                        print(f"  WARNING: No items found after adding!")
                    
                    # Save to local cache
                    self.save_to_cache()
                    # Refresh the display
                    self.display_contractors()
                else:
                    messagebox.showerror("Error", "Failed to add line item.")
            except Exception as e:
                print(f"Error adding line item: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to add line item: {e}")
        else:
            # Local storage fallback
            import copy
            new_item = {
                'id': None,
                'line_item': line_item.strip(),
                'price': price
            }
            # Create a new list with the appended item
            updated_line_items = contractor_info['line_items'].copy()
            updated_line_items.append(new_item)
            
            # Update both dictionaries
            contractor_info['line_items'] = updated_line_items
            self.contractors_data[contractor_name] = contractor_info.copy()
            
            # Update all_contractors_data
            self.all_contractors_data[contractor_name] = {
                'id': contractor_info.get('id'),
                'line_items': updated_line_items.copy(),
                'updated_by': contractor_info.get('updated_by'),
                'updated_at': contractor_info.get('updated_at')
            }
            
            # Save to local cache
            self.save_to_cache()
            self.display_contractors()
    
    def save_line_item(self, item_id, line_item, price_str, contractor_name):
        """Save changes to a line item."""
        if not line_item or not line_item.strip():
            messagebox.showerror("Error", "Line item cannot be empty.")
            return
        
        try:
            price = float(price_str.replace('$', '').replace(',', ''))
        except ValueError:
            messagebox.showerror("Invalid Price", "Please enter a valid price.")
            return
        
        if self.db and self.user_id and item_id:
            try:
                success = self.db.update_contractor_line_item(item_id, line_item.strip(), price, self.user_id)
                if success:
                    # Update local data
                    contractor_info = self.contractors_data[contractor_name]
                    for item in contractor_info['line_items']:
                        if item['id'] == item_id:
                            item['line_item'] = line_item.strip()
                            item['price'] = price
                            break
                    contractor_info['updated_by'] = self.user_id
                    contractor_info['updated_at'] = datetime.now().isoformat()
                    # Update all_contractors_data
                    if contractor_name in self.all_contractors_data:
                        self.all_contractors_data[contractor_name] = copy.deepcopy(contractor_info)
                    # Save to local cache
                    self.save_to_cache()
                    self.display_contractors()
                else:
                    messagebox.showerror("Error", "Failed to update line item.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update line item: {e}")
        else:
            # Local storage fallback
            contractor_info = self.contractors_data[contractor_name]
            for item in contractor_info['line_items']:
                if item.get('id') == item_id or (not item_id and item.get('line_item') == line_item):
                    item['line_item'] = line_item.strip()
                    item['price'] = price
                    break
            # Update all_contractors_data
            if contractor_name in self.all_contractors_data:
                self.all_contractors_data[contractor_name] = contractor_info
            self.display_contractors()
    
    def delete_line_item(self, item_id, contractor_name):
        """Delete a line item."""
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this line item?"):
            return
        
        if self.db and self.user_id and item_id:
            try:
                success = self.db.delete_contractor_line_item(item_id, self.user_id)
                if success:
                    contractor_info = self.contractors_data[contractor_name]
                    contractor_info['line_items'] = [item for item in contractor_info['line_items'] 
                                                    if item['id'] != item_id]
                    contractor_info['updated_by'] = self.user_id
                    contractor_info['updated_at'] = datetime.now().isoformat()
                    # Update all_contractors_data
                    if contractor_name in self.all_contractors_data:
                        self.all_contractors_data[contractor_name] = copy.deepcopy(contractor_info)
                    # Save to local cache
                    self.save_to_cache()
                    self.display_contractors()
                else:
                    messagebox.showerror("Error", "Failed to delete line item.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete line item: {e}")
        else:
            # Local storage fallback
            contractor_info = self.contractors_data[contractor_name]
            contractor_info['line_items'] = [item for item in contractor_info['line_items'] 
                                            if item.get('id') != item_id]
            # Update all_contractors_data
            if contractor_name in self.all_contractors_data:
                self.all_contractors_data[contractor_name] = contractor_info
            self.display_contractors()
    
    def delete_contractor(self, contractor_name, contractor_id):
        """Delete a contractor and all its line items."""
        if not messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete contractor '{contractor_name}' and all its line items?"):
            return
        
        if self.db and contractor_id:
            try:
                success = self.db.delete_special_contractor(contractor_id)
                if success:
                    del self.contractors_data[contractor_name]
                    if contractor_name in self.all_contractors_data:
                        del self.all_contractors_data[contractor_name]
                    # Save to local cache
                    self.save_to_cache()
                    self.display_contractors()
                else:
                    messagebox.showerror("Error", "Failed to delete contractor.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete contractor: {e}")
        else:
            # Local storage fallback
            del self.contractors_data[contractor_name]
            if contractor_name in self.all_contractors_data:
                del self.all_contractors_data[contractor_name]
            # Save to local cache
            self.save_to_cache()
            self.display_contractors()
    
    def _debounced_filter(self):
        """Debounced wrapper for filter_contractors to avoid refreshing on every keystroke."""
        # Cancel previous timer if exists
        if self.search_debounce_timer:
            self.parent_frame.after_cancel(self.search_debounce_timer)
        
        # Very responsive delay - smooth as butter
        self.search_debounce_timer = self.parent_frame.after(100, self.filter_contractors)
    
    def filter_contractors(self):
        """Filter contractors based on search query - optimized for performance."""
        # Check if scrollable_content exists before filtering
        if not hasattr(self, 'scrollable_content'):
            return
        
        search_query = self.search_var.get().lower().strip()
        
        # Ignore placeholder text
        if not search_query or search_query == "type contractor name...":
            # Show all contractors - avoid copying if already showing all
            if id(self.contractors_data) != id(self.all_contractors_data):
                self.contractors_data = self.all_contractors_data
        else:
            # Filter contractors - highly optimized for speed
            filtered_data = {}
            search_lower = search_query.lower()
            
            # Use generator for memory efficiency and speed
            for contractor_name, contractor_info in self.all_contractors_data.items():
                # Quick check: search in contractor name first (fastest path)
                if search_lower in contractor_name.lower():
                    filtered_data[contractor_name] = contractor_info
                    continue
                
                # Search in line items only if name doesn't match
                line_items = contractor_info.get('line_items', [])
                if line_items:  # Skip if no items
                    for item in line_items:
                        line_item_text = item.get('line_item', '')
                        # Early exit on match
                        if line_item_text and search_lower in line_item_text.lower():
                            filtered_data[contractor_name] = contractor_info
                            break
            
            self.contractors_data = filtered_data
        
        # Update display - use existing optimized method
        self.display_contractors()
    
    def go_back(self):
        """Close window if it's a Toplevel, otherwise navigate back."""
        # If parent is a Toplevel window, close it
        if isinstance(self.parent_frame, tk.Toplevel):
            self.parent_frame.destroy()
            return
        
        # Otherwise, clear and try to show dashboard
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Try to show dashboard if available
        try:
            parent = self.parent_frame.master
            while parent:
                if hasattr(parent, 'show_dashboard_content'):
                    parent.show_dashboard_content()
                    return
                parent = parent.master
        except:
            pass

