# approval_module.py
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import json
import os
from theme_manager import theme_manager
import calendar as _calendar
from calendar import month_name

class ApprovalModule:
    """
    Approval Tracking Module with Monthly View
    Tracks approvals per month with Excel-like interface
    """
    
    def __init__(self, parent_frame, username=None, user_id=None):
        self.parent_frame = parent_frame
        self.username = username
        self.user_id = user_id
        
        # Use theme manager for colors
        self.colors = theme_manager.get_current_colors()
        
        # Data initialization
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.local_storage_path = os.path.join(self.app_data_dir, "approvals.json")
        
        # Initialize Supabase database
        try:
            from database_online import OnlineDatabaseManager
            self.db = OnlineDatabaseManager()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            self.db = None
        
        # Current month/year view
        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year
        
        self.approvals = []
        
        # UI Components
        self.create_ui()
        
        # Load data for current month
        self.load_approvals()
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
    
    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        # Rebuild UI with new theme
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        self.create_ui()
        self.load_approvals()
    
    def create_ui(self):
        """Create main user interface with modern card layout"""
        # Get theme-appropriate colors
        card_bg = self.colors.get('white', '#FFFFFF')
        card_border = self.colors.get('gray_light', '#E5E7EB')
        container_bg = self.colors.get('background', '#F5F7FA')
        
        # Main container with theme background
        main_container = tk.Frame(self.parent_frame, bg=container_bg)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Card frame with theme colors
        card_frame = tk.Frame(main_container, bg=card_bg, 
                             relief='solid', bd=1,
                             highlightbackground=card_border, highlightthickness=1)
        card_frame.pack(fill='both', expand=True)
        
        # Card inner container with padding
        card_inner = tk.Frame(card_frame, bg=card_bg)
        card_inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Store container reference for theme updates
        self.main_container = main_container
        self.card_frame = card_frame
        
        # Header section inside card
        self.create_header(card_inner)
        
        # Month selector and action buttons inside card
        self.create_controls(card_inner)
        
        # Excel-like table inside card
        self.create_table(card_inner)
    
    def create_header(self, parent):
        """Create header section inside card"""
        card_bg = self.colors.get('white', '#FFFFFF')
        header_frame = tk.Frame(parent, bg=card_bg)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title and user info
        title_frame = tk.Frame(header_frame, bg=card_bg)
        title_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(title_frame, text="✔️ Approval Tracking", 
                font=("Segoe UI", 24, "bold"),
                bg=card_bg, 
                fg=self.colors.get('text_primary', '#1F2937')).pack(side='left')
        
        if self.username:
            tk.Label(title_frame, text=f"User: {self.username}", 
                    font=("Segoe UI", 12),
                    bg=card_bg, 
                    fg=self.colors.get('text_secondary', '#6B7280')).pack(side='right', padx=10)
    
    def create_controls(self, parent):
        """Create month selector and action buttons inside card"""
        card_bg = self.colors.get('white', '#FFFFFF')
        hover_bg = self.colors.get('gray_light', '#F3F4F6')
        text_color = self.colors.get('text_primary', '#1F2937')
        
        controls_frame = tk.Frame(parent, bg=card_bg)
        controls_frame.pack(fill='x', pady=(0, 15))
        
        # Modern centered date navigation (like calendar picker)
        nav_frame = tk.Frame(controls_frame, bg=card_bg)
        nav_frame.pack(side='left', expand=True)
        
        # Previous month button
        prev_month_btn = tk.Button(nav_frame, text='◀', font=("Segoe UI", 16),
                                  bg=card_bg, fg=text_color,
                                  relief='flat', cursor='hand2', 
                                  padx=15, pady=5,
                                  activebackground=hover_bg,
                                  borderwidth=0, highlightthickness=0,
                                  command=self.decrement_month)
        prev_month_btn.pack(side='left')
        
        # Hover effect for prev button
        def on_prev_enter(e):
            prev_month_btn.config(bg=hover_bg)
        def on_prev_leave(e):
            prev_month_btn.config(bg=card_bg)
        prev_month_btn.bind('<Enter>', on_prev_enter)
        prev_month_btn.bind('<Leave>', on_prev_leave)
        
        # Month/Year label - bold and large, centered
        self.month_year_label = tk.Label(nav_frame, 
                                         text=f"{month_name[self.current_month]} {self.current_year}",
                                         font=("Segoe UI", 16, "bold"),
                                         bg=card_bg,
                                         fg=text_color)
        self.month_year_label.pack(side='left', expand=True)
        
        # Next month button
        next_month_btn = tk.Button(nav_frame, text='▶', font=("Segoe UI", 16),
                                  bg=card_bg, fg=text_color,
                                  relief='flat', cursor='hand2',
                                  padx=15, pady=5,
                                  activebackground=hover_bg,
                                  borderwidth=0, highlightthickness=0,
                                  command=self.increment_month)
        next_month_btn.pack(side='right')
        
        # Hover effect for next button
        def on_next_enter(e):
            next_month_btn.config(bg=hover_bg)
        def on_next_leave(e):
            next_month_btn.config(bg=card_bg)
        next_month_btn.bind('<Enter>', on_next_enter)
        next_month_btn.bind('<Leave>', on_next_leave)
        
        # Right side - Action buttons
        actions_frame = tk.Frame(controls_frame, bg=card_bg)
        actions_frame.pack(side='right')
        
        add_btn = tk.Button(actions_frame, text="+ Add Approval", 
                           font=("Segoe UI", 11, "bold"),
                           bg=self.colors.get('success', '#10B981'),
                           fg=self.colors.get('button_text', 'white'),
                           relief='flat', cursor='hand2',
                           padx=20, pady=8,
                           command=self.open_add_approval_dialog)
        add_btn.pack(side='left', padx=5)
        
        refresh_btn = tk.Button(actions_frame, text="🔄 Refresh", 
                               font=("Segoe UI", 10),
                               bg=self.colors['primary_blue'], 
                               fg=self.colors.get('button_text', 'white'),
                               relief='flat', cursor='hand2',
                               padx=15, pady=8,
                               command=self.load_approvals)
        refresh_btn.pack(side='left', padx=5)
    
    def create_table(self, parent):
        """Create Excel-like table for approvals inside card"""
        card_bg = self.colors.get('white', '#FFFFFF')
        
        # Table container - no extra border since it's inside the card
        table_container = tk.Frame(parent, bg=card_bg)
        table_container.pack(fill='both', expand=True)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(table_container, bg=card_bg,
                          highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(table_container, orient='vertical', 
                                    command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(table_container, orient='horizontal', 
                                    command=canvas.xview)
        
        card_bg = self.colors.get('white', '#FFFFFF')
        self.table_frame = tk.Frame(canvas, bg=card_bg)
        
        self.table_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=self.table_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar_v.set, 
                        xscrollcommand=scrollbar_h.set)
        
        # Pack scrollbars and canvas
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')
        canvas.pack(side='left', fill='both', expand=True)
        
        self.table_canvas = canvas
        
        # Mouse wheel binding
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Render table headers and data
        self.render_table()
    
    def render_table(self):
        """Render the Excel-like table with headers and data"""
        # Clear existing widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Configure uniform column weights on the parent table_frame for all 7 columns
        # This ensures perfect alignment across header, data, and footer rows
        for col_idx in range(7):
            self.table_frame.grid_columnconfigure(col_idx, weight=1, uniform='table_col')
        
        # Define column headers (Source Work Order moved after Work Order)
        columns = [
            'Date',
            'Work Order',
            'Source Work Order',
            'Approval Amount',
            'Vendor Price',
            'Gross Profit',
            'Actions'
        ]
        
        # Create header row using grid
        header_row = tk.Frame(self.table_frame, bg=self.colors['primary_blue'])
        header_row.grid(row=0, column=0, columnspan=7, sticky='nsew', padx=0, pady=0)
        
        # Configure header row columns with same weights as parent
        for col_idx in range(7):
            header_row.grid_columnconfigure(col_idx, weight=1, uniform='table_col')
        
        # Create header cells
        for col_idx, col_name in enumerate(columns):
            cell = tk.Label(header_row, text=col_name, 
                          font=("Segoe UI", 11, "bold"),
                          bg=self.colors['primary_blue'],
                          fg=self.colors['button_text'],
                          anchor='w',
                          relief='solid', bd=1, padx=10, pady=10)
            cell.grid(row=0, column=col_idx, sticky='nsew')
        
        # Track current row index for grid positioning
        current_row = 1
        
        # Create data rows
        card_bg = self.colors.get('white', '#FFFFFF')
        row_alt_bg = self.colors.get('gray_light', '#F9FAFB')
        
        if not self.approvals:
            # Empty state - span all columns
            empty_row = tk.Frame(self.table_frame, bg=card_bg)
            empty_row.grid(row=current_row, column=0, columnspan=7, sticky='nsew', pady=50)
            
            empty_label = tk.Label(empty_row, 
                                  text="No approvals for this month. Click 'Add Approval' to get started.",
                                  font=("Segoe UI", 12),
                                  bg=card_bg,
                                  fg=self.colors.get('text_secondary', '#6B7280'))
            empty_label.pack(expand=True)
        else:
            total_approval = 0
            total_vendor = 0
            total_profit = 0
            
            for idx, approval in enumerate(self.approvals):
                row_frame = tk.Frame(self.table_frame, 
                                    bg=card_bg if idx % 2 == 0 
                                    else row_alt_bg)
                row_frame.grid(row=current_row, column=0, columnspan=7, sticky='nsew')
                
                # Configure row columns with same weights as parent
                for col_idx in range(7):
                    row_frame.grid_columnconfigure(col_idx, weight=1, uniform='table_col')
                
                # Format date
                try:
                    if isinstance(approval.get('approval_date'), str):
                        if 'T' in approval['approval_date']:
                            date_str = approval['approval_date'].split('T')[0]
                        else:
                            date_str = approval['approval_date']
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        date_display = date_obj.strftime('%Y-%m-%d')
                    else:
                        date_display = str(approval.get('approval_date', ''))
                except:
                    date_display = str(approval.get('approval_date', ''))
                
                # Format amounts
                approval_amount = float(approval.get('approval_amount', 0))
                vendor_price = float(approval.get('vendor_price', 0))
                gross_profit = float(approval.get('gross_profit', 0))
                
                total_approval += approval_amount
                total_vendor += vendor_price
                total_profit += gross_profit
                
                # Create cells (Source Work Order moved after Work Order)
                # Price columns are 3, 4, 5 (Approval Amount, Vendor Price, Gross Profit)
                cells_data = [
                    date_display,
                    str(approval.get('work_order', '')),
                    str(approval.get('source_work_order', '')),
                    f"${approval_amount:,.2f}",
                    f"${vendor_price:,.2f}",
                    f"${gross_profit:,.2f}",
                    ''  # Actions column
                ]
                
                for col_idx, cell_data in enumerate(cells_data):
                    if col_idx == 6:  # Actions column
                        actions_cell = tk.Frame(row_frame, 
                                              bg=row_frame.cget('bg'),
                                              relief='solid', bd=1)
                        actions_cell.grid(row=0, column=col_idx, sticky='nsew', padx=1, pady=1)
                        
                        edit_btn = tk.Button(actions_cell, text="✏️", 
                                           font=("Segoe UI", 10),
                                           bg=row_frame.cget('bg'),
                                           fg=self.colors['primary_blue'],
                                           relief='flat', cursor='hand2',
                                           padx=5, pady=3,
                                           command=lambda a=approval: self.edit_approval(a))
                        edit_btn.pack(side='left', padx=2)
                        
                        delete_btn = tk.Button(actions_cell, text="🗑️", 
                                              font=("Segoe UI", 10),
                                              bg=row_frame.cget('bg'),
                                              fg='#DC3545',
                                              relief='flat', cursor='hand2',
                                              padx=5, pady=3,
                                              command=lambda a=approval: self.delete_approval(a))
                        delete_btn.pack(side='left', padx=2)
                    else:
                        # Use larger font for price fields (columns 3, 4, 5)
                        is_price_col = col_idx in [3, 4, 5]
                        font_size = ("Segoe UI", 12, "bold") if is_price_col else ("Segoe UI", 10)
                        cell = tk.Label(row_frame, text=cell_data,
                                      font=font_size,
                                      bg=row_frame.cget('bg'),
                                      fg=self.colors.get('text_primary', '#1F2937'),
                                      anchor='w',
                                      relief='solid', bd=1, padx=10, pady=8)
                        cell.grid(row=0, column=col_idx, sticky='nsew', padx=1, pady=1)
                
                current_row += 1
            
            # Total row using grid
            total_row = tk.Frame(self.table_frame, 
                               bg=self.colors.get('nav_hover', '#2563EB'))
            total_row.grid(row=current_row, column=0, columnspan=7, sticky='nsew', pady=(5, 0))
            
            # Configure total row columns with same weights as parent
            for col_idx in range(7):
                total_row.grid_columnconfigure(col_idx, weight=1, uniform='table_col')
            
            total_cells = [
                'TOTAL',
                '',
                '',
                f"${total_approval:,.2f}",
                f"${total_vendor:,.2f}",
                f"${total_profit:,.2f}",
                ''
            ]
            
            for col_idx, cell_data in enumerate(total_cells):
                # Price columns (3, 4, 5) should have larger font
                is_price_col = col_idx in [3, 4, 5]
                font_size = ("Segoe UI", 13, "bold") if is_price_col else ("Segoe UI", 11, "bold")
                cell = tk.Label(total_row, text=cell_data,
                              font=font_size,
                              bg=self.colors.get('nav_hover', '#2563EB'),
                              fg='white',
                              anchor='w' if col_idx > 0 else 'center',
                              relief='solid', bd=1, padx=10, pady=10)
                cell.grid(row=0, column=col_idx, sticky='nsew', padx=1, pady=1)
        
    
    def decrement_month(self):
        """Decrement month (with year rollover)"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_month_year_label()
        self.load_approvals()
    
    def increment_month(self):
        """Increment month (with year rollover)"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_month_year_label()
        self.load_approvals()
    
    def update_month_year_label(self):
        """Update the month/year label in the navigation"""
        if hasattr(self, 'month_year_label'):
            self.month_year_label.config(text=f"{month_name[self.current_month]} {self.current_year}")
    
    def get_month_year_string(self):
        """Get month-year string in format YYYY-MM"""
        return f"{self.current_year}-{self.current_month:02d}"
    
    def open_date_picker(self, target_var):
        """Open calendar date picker dialog"""
        # Refresh colors to get latest theme
        self.colors = theme_manager.get_current_colors()
        # Get the root window from parent_frame
        root_window = self.parent_frame.winfo_toplevel()
        picker = tk.Toplevel(root_window)
        picker.title("Select Date")
        picker.configure(bg=self.colors.get('background', '#F5F7FA'))
        picker.geometry("400x450")
        picker.transient(root_window)
        picker.grab_set()
        
        # Center
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() - 400) // 2
        y = (picker.winfo_screenheight() - 450) // 2
        picker.geometry(f"400x450+{x}+{y}")
        
        # Container - ensure it expands
        container = tk.Frame(picker, bg=self.colors.get('white', '#FFFFFF'))
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Make picker resizable to ensure calendar is visible
        picker.resizable(False, False)
        
        # Title
        tk.Label(container, text="📅 Select Date",
                font=("Segoe UI", 14, "bold"),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors.get('text_primary', '#1F2937')).pack(pady=(0, 20))
        
        # Parse current date if exists
        current_date_obj = None
        try:
            if target_var.get() and target_var.get().strip():
                current_date_obj = datetime.strptime(target_var.get().strip(), '%Y-%m-%d')
                year_var = tk.IntVar(value=current_date_obj.year)
                month_var = tk.IntVar(value=current_date_obj.month)
                day_var = tk.IntVar(value=current_date_obj.day)
            else:
                now = datetime.now()
                current_date_obj = now
                year_var = tk.IntVar(value=now.year)
                month_var = tk.IntVar(value=now.month)
                day_var = tk.IntVar(value=now.day)
        except (ValueError, AttributeError):
            now = datetime.now()
            current_date_obj = now
            year_var = tk.IntVar(value=now.year)
            month_var = tk.IntVar(value=now.month)
            day_var = tk.IntVar(value=now.day)
        
        # Calendar header - modernized centered navigation
        cal_header = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        cal_header.pack(fill='x', pady=(0, 15))
        
        # Left arrow button (previous month)
        prev_btn = tk.Button(cal_header, text='◀', font=("Segoe UI", 16),
                            bg=self.colors.get('white', '#FFFFFF'),
                            fg=self.colors.get('text_primary', '#1F2937'),
                            relief='flat', cursor='hand2', 
                            padx=15, pady=5,
                            activebackground=self.colors.get('gray_light', '#F3F4F6'),
                            activeforeground=self.colors.get('text_primary', '#1F2937'),
                            borderwidth=0, highlightthickness=0)
        prev_btn.pack(side='left')
        
        # Hover effect for prev button
        def on_prev_enter(e):
            prev_btn.config(bg=self.colors.get('gray_light', '#F3F4F6'))
        def on_prev_leave(e):
            prev_btn.config(bg=self.colors.get('white', '#FFFFFF'))
        prev_btn.bind('<Enter>', on_prev_enter)
        prev_btn.bind('<Leave>', on_prev_leave)
        
        # Month/Year label - bold and large, centered
        month_label = tk.Label(cal_header, text="", 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.colors.get('white', '#FFFFFF'),
                              fg=self.colors.get('text_primary', '#1F2937'))
        month_label.pack(side='left', expand=True)
        
        # Right arrow button (next month)
        next_btn = tk.Button(cal_header, text='▶', font=("Segoe UI", 16),
                            bg=self.colors.get('white', '#FFFFFF'),
                            fg=self.colors.get('text_primary', '#1F2937'),
                            relief='flat', cursor='hand2',
                            padx=15, pady=5,
                            activebackground=self.colors.get('gray_light', '#F3F4F6'),
                            activeforeground=self.colors.get('text_primary', '#1F2937'),
                            borderwidth=0, highlightthickness=0)
        next_btn.pack(side='right')
        
        # Hover effect for next button
        def on_next_enter(e):
            next_btn.config(bg=self.colors.get('gray_light', '#F3F4F6'))
        def on_next_leave(e):
            next_btn.config(bg=self.colors.get('white', '#FFFFFF'))
        next_btn.bind('<Enter>', on_next_enter)
        next_btn.bind('<Leave>', on_next_leave)
        
        # Calendar grid - use pack with fill to ensure it expands
        cal_frame = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        cal_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Configure calendar grid columns for equal spacing
        for i in range(7):
            cal_frame.grid_columnconfigure(i, weight=1, uniform='cal_col')
        
        # Days of week headers
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, day in enumerate(days):
            tk.Label(cal_frame, text=day, font=("Segoe UI", 9, "bold"),
                    bg=self.colors.get('white', '#FFFFFF'),
                    fg=self.colors.get('text_secondary', '#6B7280'),
                    width=6).grid(row=0, column=i, padx=2, pady=3, sticky='nsew')
        
        day_buttons = []
        
        def update_calendar():
            for btn in day_buttons:
                btn.destroy()
            day_buttons.clear()
            
            month_label.config(text=f"{_calendar.month_name[month_var.get()]} {year_var.get()}")
            
            cal = _calendar.Calendar(firstweekday=0)
            month_days = cal.monthdayscalendar(year_var.get(), month_var.get())
            
            now = datetime.now()
            current_year = year_var.get()
            current_month = month_var.get()
            selected_day = day_var.get()
            
            row = 1
            for week in month_days:
                for col, day in enumerate(week):
                    if day == 0:
                        lbl = tk.Label(cal_frame, text="", width=6, height=2,
                                      bg=self.colors.get('white', '#FFFFFF'))
                        lbl.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
                        day_buttons.append(lbl)
                    else:
                        # Create handler function for each day button to avoid lambda closure issues
                        def make_handler(d):
                            def handler():
                                day_var.set(d)
                                update_calendar()
                            return handler
                        
                        btn_bg = self.colors.get('gray_light', '#F9FAFB')
                        btn_fg = self.colors.get('text_primary', '#1F2937')
                        btn_border = self.colors.get('gray_light', '#E5E7EB')
                        btn_hover = self.colors.get('primary_blue', '#E3F2FD')
                        if hasattr(self.colors, 'get') or 'primary_blue' in self.colors:
                            btn_hover = '#E3F2FD'  # Light blue hover for calendar buttons
                        
                        btn = tk.Button(cal_frame, text=str(day), width=6, height=2,
                                       font=("Segoe UI", 10, "bold"),
                                       bg=btn_bg,
                                       fg=btn_fg,
                                       relief='solid', 
                                       bd=1,
                                       highlightthickness=0,
                                       borderwidth=1,
                                       highlightbackground=btn_border,
                                       activebackground=btn_hover,
                                       activeforeground=btn_fg,
                                       cursor='hand2',
                                       command=make_handler(day))
                        btn.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
                        day_buttons.append(btn)
                        
                        # Highlight selected day
                        if day == selected_day and current_month == month_var.get() and current_year == year_var.get():
                            btn.config(bg=self.colors['primary_blue'], fg='white', relief='solid', bd=2)
                        # Highlight today (but not if it's the selected day)
                        elif (day == now.day and current_month == now.month and 
                              current_year == now.year):
                            if not (day == selected_day and current_month == month_var.get()):
                                btn.config(bg='#E3F2FD', fg='#1F2937', relief='solid', bd=1)
                # Increment row after processing all 7 days in the week
                row += 1
        
        def prev_month():
            m, y = month_var.get(), year_var.get()
            if m == 1:
                month_var.set(12)
                year_var.set(y - 1)
            else:
                month_var.set(m - 1)
            # Update selected day if it doesn't exist in the new month
            try:
                datetime(year_var.get(), month_var.get(), day_var.get())
            except ValueError:
                # Day doesn't exist in this month, set to last day of month
                import calendar
                last_day = calendar.monthrange(year_var.get(), month_var.get())[1]
                day_var.set(last_day)
            update_calendar()
        
        def next_month():
            m, y = month_var.get(), year_var.get()
            if m == 12:
                month_var.set(1)
                year_var.set(y + 1)
            else:
                month_var.set(m + 1)
            # Update selected day if it doesn't exist in the new month
            try:
                datetime(year_var.get(), month_var.get(), day_var.get())
            except ValueError:
                # Day doesn't exist in this month, set to last day of month
                import calendar
                last_day = calendar.monthrange(year_var.get(), month_var.get())[1]
                day_var.set(last_day)
            update_calendar()
        
        prev_btn.config(command=prev_month)
        next_btn.config(command=next_month)
        
        # Buttons
        btn_frame = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        btn_frame.pack(fill='x')
        
        def set_date():
            try:
                dt = datetime(year_var.get(), month_var.get(), day_var.get())
                target_var.set(dt.strftime("%Y-%m-%d"))
                picker.destroy()
            except ValueError:
                messagebox.showwarning("Invalid Date", "Please select a valid date.")
        
        save_btn = tk.Button(btn_frame, text="Set Date",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.colors['success'] if 'success' in self.colors else '#10B981',
                            fg='white',
                            relief='flat', cursor='hand2',
                            padx=20, pady=10, command=set_date)
        save_btn.pack(side='right')
        
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                              font=("Segoe UI", 10),
                              bg=self.colors.get('text_secondary', '#6B7280'),
                              fg='white',
                              relief='flat', cursor='hand2',
                              padx=20, pady=10, command=picker.destroy)
        cancel_btn.pack(side='right', padx=(0, 10))
        
        # Initial calendar render - call after all setup is complete
        update_calendar()
    
    def open_add_approval_dialog(self, approval=None):
        """Open dialog for adding/editing approval"""
        is_edit = approval is not None
        # Refresh colors to get latest theme
        self.colors = theme_manager.get_current_colors()
        # Get the root window from parent_frame
        root_window = self.parent_frame.winfo_toplevel()
        dialog = tk.Toplevel(root_window)
        dialog.title("Edit Approval" if is_edit else "Add Approval")
        dialog.configure(bg=self.colors['background'])
        dialog.geometry("1300x350")
        dialog.transient(root_window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 1300) // 2
        y = (dialog.winfo_screenheight() - 350) // 2
        dialog.geometry(f"1300x350+{x}+{y}")
        
        # Container
        container = tk.Frame(dialog, bg=self.colors.get('white', '#FFFFFF'))
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(container, text="📝 Approval Details",
                font=("Segoe UI", 18, "bold"),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors['text_primary']).pack(anchor='w', pady=(0, 25))
        
        # Single row with all fields - equal widths
        fields_row = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        fields_row.pack(fill='x', pady=(0, 20))
        
        # Helper function to create a field frame
        def create_field(parent, col, label_text, entry_var, is_readonly=False, is_price=False, picker_var=None):
            field_frame = tk.Frame(parent, bg=self.colors.get('white', '#FFFFFF'))
            field_frame.grid(row=0, column=col, sticky='ew', padx=8)
            tk.Label(field_frame, text=label_text, font=("Segoe UI", 10, "bold"),
                    bg=self.colors.get('white', '#FFFFFF'),
                    fg=self.colors['text_primary']).pack(anchor='w', pady=(0, 5))
            
            entry_frame = tk.Frame(field_frame, bg=self.colors.get('white', '#FFFFFF'))
            entry_frame.pack(fill='x')
            
            # For date field with picker, make it readonly and clickable
            if picker_var is not None:
                entry = tk.Entry(entry_frame, textvariable=entry_var,
                               font=("Segoe UI", 11),
                               bg=self.colors.get('gray_light', '#F3F4F6'),
                               fg=self.colors['text_primary'],
                               relief='solid', bd=1,
                               state='readonly',
                               cursor='hand2')
                entry.pack(side='left', fill='x', expand=True, ipady=8, ipadx=10)
                
                # Make entry clickable to open calendar
                def open_picker_on_click(event=None):
                    self.open_date_picker(picker_var)
                entry.bind('<Button-1>', open_picker_on_click)
                
                picker_btn = tk.Button(entry_frame, text="📅",
                                     font=("Segoe UI", 12),
                                     bg=self.colors['primary_blue'],
                                     fg='white',
                                     relief='flat', cursor='hand2',
                                     padx=10, pady=6,
                                     command=lambda: self.open_date_picker(picker_var))
                picker_btn.pack(side='left', padx=(5, 0))
            else:
                entry = tk.Entry(entry_frame, textvariable=entry_var,
                               font=("Segoe UI", 14, "bold") if is_price else ("Segoe UI", 11),
                               bg=self.colors.get('gray_light', '#F3F4F6') if is_readonly else self.colors.get('white', '#FFFFFF'),
                               fg=self.colors['text_primary'],
                               relief='solid', bd=1,
                               state='readonly' if is_readonly else 'normal')
                entry.pack(side='left', fill='x', expand=True, ipady=8, ipadx=10)
            
            return entry
        
        # Initialize variables
        date_var = tk.StringVar(value=approval.get('approval_date', '').split('T')[0] if approval and approval.get('approval_date') else datetime.now().strftime('%Y-%m-%d'))
        wo_var = tk.StringVar(value=approval.get('work_order', '') if approval else '')
        source_wo_var = tk.StringVar(value=approval.get('source_work_order', '') if approval else '')
        approval_amount_var = tk.StringVar(value=str(approval.get('approval_amount', '')) if approval else '')
        vendor_price_var = tk.StringVar(value=str(approval.get('vendor_price', '')) if approval else '')
        gross_profit_var = tk.StringVar()
        
        # Create all fields in one row
        date_entry = create_field(fields_row, 0, "Date *", date_var, picker_var=date_var)
        wo_entry = create_field(fields_row, 1, "Work Order *", wo_var)
        source_wo_entry = create_field(fields_row, 2, "Source Work Order", source_wo_var)
        approval_amount_entry = create_field(fields_row, 3, "Approval Amount *", approval_amount_var, is_price=True)
        vendor_price_entry = create_field(fields_row, 4, "Vendor Price *", vendor_price_var, is_price=True)
        gross_profit_entry = create_field(fields_row, 5, "Gross Profit", gross_profit_var, is_readonly=True, is_price=True)
        
        # Configure equal column weights
        for i in range(6):
            fields_row.grid_columnconfigure(i, weight=1, uniform='equal')
        
        def calculate_gross_profit(event=None):
            """Calculate and display gross profit"""
            try:
                approval_amt = float(approval_amount_var.get() or 0)
                vendor_pr = float(vendor_price_var.get() or 0)
                gross_profit = approval_amt - vendor_pr
                gross_profit_var.set(f"{gross_profit:,.2f}")
            except ValueError:
                gross_profit_var.set("0.00")
        
        approval_amount_entry.bind('<KeyRelease>', calculate_gross_profit)
        vendor_price_entry.bind('<KeyRelease>', calculate_gross_profit)
        calculate_gross_profit()  # Initial calculation
        
        # Buttons
        button_frame = tk.Frame(container, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(fill='x')
        
        def save_approval():
            """Save approval entry"""
            try:
                # Validate required fields
                if not date_var.get().strip():
                    messagebox.showwarning("Validation Error", "Please enter a date.")
                    return
                if not wo_var.get().strip():
                    messagebox.showwarning("Validation Error", "Please enter a Work Order.")
                    return
                if not approval_amount_var.get().strip():
                    messagebox.showwarning("Validation Error", "Please enter an Approval Amount.")
                    return
                if not vendor_price_var.get().strip():
                    messagebox.showwarning("Validation Error", "Please enter a Vendor Price.")
                    return
                
                # Validate date format
                try:
                    datetime.strptime(date_var.get().strip(), '%Y-%m-%d')
                except ValueError:
                    messagebox.showwarning("Validation Error", "Date format must be YYYY-MM-DD (e.g., 2024-01-15)")
                    return
                
                # Parse amounts
                approval_amt = float(approval_amount_var.get())
                vendor_pr = float(vendor_price_var.get())
                gross_profit = approval_amt - vendor_pr
                
                # Prepare approval data
                approval_data = {
                    'approval_date': date_var.get().strip(),
                    'work_order': wo_var.get().strip(),
                    'approval_amount': approval_amt,
                    'vendor_price': vendor_pr,
                    'gross_profit': gross_profit,
                    'source_work_order': source_wo_var.get().strip(),
                    'month_year': self.get_month_year_string()
                }
                
                if is_edit and approval:
                    approval_data['id'] = approval.get('id')
                
                # Save to database
                if self.db and self.user_id:
                    try:
                        approval_id = self.db.save_approval(self.user_id, approval_data)
                        approval_data['id'] = approval_id
                    except Exception as e:
                        messagebox.showerror("Database Error", f"Failed to save to database: {e}")
                        return
                else:
                    # Fallback to local storage
                    approval_data['id'] = approval.get('id') if approval else len(self.approvals) + 1
                
                if is_edit:
                    # Update existing
                    for idx, app in enumerate(self.approvals):
                        if app.get('id') == approval.get('id'):
                            self.approvals[idx] = approval_data
                            break
                else:
                    # Add new
                    self.approvals.append(approval_data)
                
                # Save to local storage
                self.save_approvals_local()
                
                # Refresh table
                self.render_table()
                
                dialog.destroy()
                messagebox.showinfo("Success", "Approval saved successfully!")
                
            except ValueError:
                messagebox.showerror("Validation Error", "Please enter valid numbers for amounts.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save approval: {e}")
        
        save_btn = tk.Button(button_frame, text="💾 Save",
                            font=("Segoe UI", 11, "bold"),
                            bg=self.colors['primary_blue'],
                            fg='white',
                            relief='flat', cursor='hand2',
                            padx=20, pady=10, command=save_approval)
        save_btn.pack(side='right')
        
        cancel_btn = tk.Button(button_frame, text="Cancel",
                              font=("Segoe UI", 10),
                              bg=self.colors.get('text_secondary', '#6B7280'),
                              fg='white',
                              relief='flat', cursor='hand2',
                              padx=20, pady=10, command=dialog.destroy)
        cancel_btn.pack(side='right', padx=(0, 10))
        
        # Keyboard shortcuts
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Control-Return>', lambda e: save_approval())
        
        # Focus on first field
        if not is_edit:
            date_entry.focus()
    
    def edit_approval(self, approval):
        """Edit an approval entry"""
        self.open_add_approval_dialog(approval)
    
    def delete_approval(self, approval):
        """Delete an approval entry"""
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete this approval entry?\n\nWork Order: {approval.get('work_order', '')}\nDate: {approval.get('approval_date', '')}"):
            try:
                # Delete from database
                if self.db and self.user_id and approval.get('id'):
                    try:
                        self.db.delete_approval(approval['id'], self.user_id)
                    except Exception as e:
                        print(f"Error deleting from database: {e}")
                
                # Remove from local list
                self.approvals = [a for a in self.approvals if a.get('id') != approval.get('id')]
                
                # Save to local storage
                self.save_approvals_local()
                
                # Refresh table
                self.render_table()
                
                messagebox.showinfo("Success", "Approval deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete approval: {e}")
    
    def load_approvals(self):
        """Load approvals for current month"""
        month_year_str = self.get_month_year_string()
        
        if self.db and self.user_id:
            try:
                self.approvals = self.db.get_user_approvals_by_month(self.user_id, month_year_str)
                # Convert database format to app format
                for approval in self.approvals:
                    if isinstance(approval.get('approval_date'), str) and 'T' in approval['approval_date']:
                        approval['approval_date'] = approval['approval_date'].split('T')[0]
                return
            except Exception as e:
                print(f"Error loading approvals from database: {e}")
                # Fall through to local load
        
        # Fallback to local storage
        if os.path.exists(self.local_storage_path):
            try:
                with open(self.local_storage_path, 'r', encoding='utf-8') as f:
                    all_approvals = json.load(f)
                    # Filter by month/year
                    self.approvals = [a for a in all_approvals 
                                    if a.get('month_year') == month_year_str]
            except Exception as e:
                print(f"Error loading local approvals: {e}")
                self.approvals = []
        else:
            self.approvals = []
        
        # Render table after loading
        self.render_table()
    
    def save_approvals_local(self):
        """Save approvals to local JSON file"""
        try:
            # Load all approvals
            all_approvals = []
            if os.path.exists(self.local_storage_path):
                try:
                    with open(self.local_storage_path, 'r', encoding='utf-8') as f:
                        all_approvals = json.load(f)
                except:
                    all_approvals = []
            
            # Update approvals for current month
            month_year_str = self.get_month_year_string()
            # Remove old entries for this month
            all_approvals = [a for a in all_approvals 
                           if a.get('month_year') != month_year_str]
            # Add current month's approvals
            all_approvals.extend(self.approvals)
            
            # Save back
            with open(self.local_storage_path, 'w', encoding='utf-8') as f:
                json.dump(all_approvals, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving local approvals: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ApprovalModule(root, username="TestUser", user_id=1)
    root.mainloop()

