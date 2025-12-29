import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import json
import os
import uuid
import calendar as _calendar

try:
    import winsound
except Exception:
    winsound = None

class ModernToDoApp:
    """
    Modern, Professional To-Do Application
    """

    STORAGE_FILENAME = "modern_todo_tasks.json"

    # Modern color palette
    COLORS = {
        'primary': '#5B7FFF',       # Primary blue
        'success': '#10B981',       # Green
        'warning': '#F59E0B',       # Amber
        'danger': '#EF4444',        # Red
        'surface': '#FFFFFF',       # White
        'background': '#F5F7FA',    # Light gray
        'text': '#1F2937',          # Dark gray
        'text_light': '#6B7280',    # Medium gray
        'border': '#E5E7EB',        # Light border
        'hover': '#F9FAFB',         # Hover state
        'shadow': 'rgba(0,0,0,0.05)',
        
        # Priority colors
        'high': '#EF4444',
        'medium': '#F59E0B',
        'low': '#10B981',
        
        # Status colors
        'todo': {
            'bg': '#FEF2F2',
            'border': '#FCA5A5',
            'text': '#991B1B'
        },
        'progress': {
            'bg': '#FEF3C7',
            'border': '#FCD34D',
            'text': '#92400E'
        },
        'done': {
            'bg': '#D1FAE5',
            'border': '#6EE7B7',
            'text': '#065F46'
        }
    }

    def __init__(self, root, user_id=None):
        self.root = root
        self.root.title("Modern To-Do App")
        
        # Window setup
        self.setup_window()
        
        # Data initialization
        self.user_id = user_id
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".modern_todo_app")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.storage_path = os.path.join(self.app_data_dir, self.STORAGE_FILENAME)
        
        # Initialize Supabase database
        try:
            from database_online import OnlineDatabaseManager
            self.db = OnlineDatabaseManager()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            self.db = None
        
        self.tasks = []
        self.filtered_tasks = []
        self.current_filter = 'all'  # all, today, week, priority
        self.search_query = ''
        self.selected_task_id = None
        self.task_id_map = {}  # Map local UUID strings to database integer IDs
        
        # Load data
        self.load_tasks()
        
        # UI Components
        self.create_ui()
        
        # Bind shortcuts
        self.bind_shortcuts()
        
        # Auto-save
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_auto_save()
        
        # Initial render
        self.apply_filters()
        self.update_stats()

    def setup_window(self):
        """Configure main window"""
        width = 1200
        height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg=self.COLORS['background'])
        self.root.minsize(900, 600)

    def create_ui(self):
        """Create main user interface"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.COLORS['background'])
        main_container.pack(fill='both', expand=True)
        
        # Left sidebar
        self.create_sidebar(main_container)
        
        # Right content area
        content_area = tk.Frame(main_container, bg=self.COLORS['background'])
        content_area.pack(side='right', fill='both', expand=True)
        
        # Top bar
        self.create_top_bar(content_area)
        
        # Stats bar
        self.create_stats_bar(content_area)
        
        # Task list
        self.create_task_list(content_area)

    def create_sidebar(self, parent):
        """Create left sidebar with navigation and quick add"""
        sidebar = tk.Frame(parent, bg=self.COLORS['surface'], width=300)
        sidebar.pack(side='left', fill='y', padx=(0, 0))
        sidebar.pack_propagate(False)
        
        # Header
        header = tk.Frame(sidebar, bg=self.COLORS['surface'])
        header.pack(fill='x', padx=20, pady=20)
        
        tk.Label(header, text="📋 My Tasks", 
                font=("Segoe UI", 20, "bold"),
                bg=self.COLORS['surface'], 
                fg=self.COLORS['text']).pack(anchor='w')
        
        # Separator
        tk.Frame(sidebar, bg=self.COLORS['border'], height=1).pack(fill='x', padx=20)
        
        # Quick Add Section
        self.create_quick_add(sidebar)
        
        # Separator
        tk.Frame(sidebar, bg=self.COLORS['border'], height=1).pack(fill='x', padx=20, pady=20)
        
        # Filters
        self.create_filters(sidebar)

    def create_quick_add(self, parent):
        """Create quick add task section"""
        quick_add = tk.Frame(parent, bg=self.COLORS['surface'])
        quick_add.pack(fill='x', padx=20, pady=20)
        
        tk.Label(quick_add, text="Quick Add", 
                font=("Segoe UI", 12, "bold"),
                bg=self.COLORS['surface'], 
                fg=self.COLORS['text']).pack(anchor='w', pady=(0, 12))
        
        # Task input - increased height
        self.quick_task_var = tk.StringVar()
        task_entry = tk.Entry(quick_add, textvariable=self.quick_task_var,
                             font=("Segoe UI", 12), bg=self.COLORS['surface'],
                             fg=self.COLORS['text'], relief='solid', bd=1,
                             highlightthickness=1, highlightcolor=self.COLORS['primary'])
        task_entry.pack(fill='x', pady=(0, 10), ipady=25, ipadx=10)  # Increased ipady to 25 for taller box
        task_entry.bind('<Return>', lambda e: self.quick_add_task())
        
        # Priority selector with colored buttons in a box
        tk.Label(quick_add, text="Priority:", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        # Priority container with border (box shape)
        priority_container = tk.Frame(quick_add, bg=self.COLORS['border'], 
                                     relief='solid', bd=1)
        priority_container.pack(fill='x', pady=(0, 10))
        
        priority_frame = tk.Frame(priority_container, bg=self.COLORS['surface'])
        priority_frame.pack(fill='x', padx=2, pady=2)
        
        self.quick_priority_var = tk.StringVar(value='medium')
        
        # Colored priority buttons (Red, Yellow, Green)
        priority_configs = [
            ('High', 'high', '#EF4444'),      # Red
            ('Medium', 'medium', '#F59E0B'),   # Yellow
            ('Low', 'low', '#10B981')          # Green
        ]
        
        priority_buttons = []
        for idx, (label, priority, color) in enumerate(priority_configs):
            # Create button frame with border when selected
            btn_frame = tk.Frame(priority_frame, bg=self.COLORS['surface'])
            btn_frame.pack(side='left', fill='both', expand=True, padx=2, pady=2)
            
            # Colored circle indicator
            indicator = tk.Canvas(btn_frame, width=22, height=22, 
                                 bg=self.COLORS['surface'], highlightthickness=0)
            indicator.pack(side='top', pady=(8, 5))
            
            # Draw colored circle
            def draw_circle(canvas, fill_color, is_selected=False):
                canvas.delete('all')
                canvas.config(bg=self.COLORS['surface'])
                if is_selected:
                    # Draw outer ring for selected
                    canvas.create_oval(1, 1, 21, 21, outline=fill_color, width=3, fill='')
                    canvas.create_oval(6, 6, 16, 16, outline='', fill=fill_color)
                else:
                    canvas.create_oval(6, 6, 16, 16, outline='', fill=fill_color)
            
            draw_circle(indicator, color, priority == 'medium')
            
            # Label text
            label_widget = tk.Label(btn_frame, text=label,
                                   font=("Segoe UI", 9, "bold"),
                                   bg=self.COLORS['surface'],
                                   fg=self.COLORS['text'])
            label_widget.pack(side='top', pady=(0, 8))
            
            # Radio button (hidden but functional for value tracking)
            rb = tk.Radiobutton(btn_frame, text="", value=priority,
                               variable=self.quick_priority_var,
                               bg=self.COLORS['surface'], 
                               fg=color,
                               selectcolor=self.COLORS['surface'], 
                               activebackground=self.COLORS['surface'],
                               indicatoron=False, 
                               relief='flat', cursor='hand2')
            rb.place(x=0, y=0, width=1, height=1)  # Hidden but functional
            
            # Make the entire button frame clickable
            def make_clickable(frame, radio_button):
                def on_click(e):
                    radio_button.invoke()
                frame.bind('<Button-1>', on_click)
                indicator.bind('<Button-1>', on_click)
                label_widget.bind('<Button-1>', on_click)
            
            make_clickable(btn_frame, rb)
            
            priority_buttons.append((rb, indicator, label_widget, btn_frame, color, priority))
        
        # Update indicators and button frames when selection changes
        def update_priority_indicators(*args):
            selected = self.quick_priority_var.get()
            for rb, indicator, label_widget, btn_frame, color, priority_value in priority_buttons:
                is_selected = priority_value == selected
                draw_circle(indicator, color, is_selected)
                
                if is_selected:
                    # Highlight selected button frame
                    btn_frame.config(bg=color, relief='solid', bd=2)
                    label_widget.config(bg=color, fg='white', font=("Segoe UI", 9, "bold"))
                    indicator.config(bg=color)
                    # Redraw circle with white outline on colored background
                    indicator.delete('all')
                    indicator.create_oval(1, 1, 21, 21, outline='white', width=2, fill='white')
                    indicator.create_oval(6, 6, 16, 16, outline='', fill=color)
                else:
                    # Reset unselected button frame
                    btn_frame.config(bg=self.COLORS['surface'], relief='flat', bd=0)
                    label_widget.config(bg=self.COLORS['surface'], fg=self.COLORS['text'], 
                                       font=("Segoe UI", 9, "bold"))
                    indicator.config(bg=self.COLORS['surface'])
                    draw_circle(indicator, color, False)
        
        self.quick_priority_var.trace('w', update_priority_indicators)
        update_priority_indicators()  # Initial update
        
        # Add button
        add_btn = tk.Button(quick_add, text="+ Add Task", 
                           font=("Segoe UI", 11, "bold"),
                           bg=self.COLORS['primary'], fg='white',
                           relief='flat', cursor='hand2', pady=10,
                           command=self.quick_add_task)
        add_btn.pack(fill='x')
        
        # Hover effect
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=self._darken_color(self.COLORS['primary'])))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=self.COLORS['primary']))

    def create_filters(self, parent):
        """Create filter buttons"""
        filters_frame = tk.Frame(parent, bg=self.COLORS['surface'])
        filters_frame.pack(fill='x', padx=20)
        
        tk.Label(filters_frame, text="Filters", 
                font=("Segoe UI", 12, "bold"),
                bg=self.COLORS['surface'], 
                fg=self.COLORS['text']).pack(anchor='w', pady=(0, 12))
        
        filters = [
            ('📝 All Tasks', 'all', None, None),
            ('📅 Today', 'today', None, None),
            ('📆 This Week', 'week', None, None),
            ('⚡ High Priority', 'priority', 'high', '#EF4444'),  # Red color
        ]
        
        self.filter_buttons = {}
        for label, filter_type, param, color in filters:
            btn = tk.Button(filters_frame, text=label, 
                           font=("Segoe UI", 10, "bold" if color else ""),
                           bg=self.COLORS['surface'], 
                           fg=color if color else self.COLORS['text'],
                           relief='flat', cursor='hand2', anchor='w',
                           padx=15, pady=8,
                           command=lambda f=filter_type, p=param: self.set_filter(f, p))
            btn.pack(fill='x', pady=2)
            
            # Hover effects
            if color:
                btn.bind('<Enter>', lambda e, b=btn, c=color: b.config(bg='#FEF2F2', fg=c))
                btn.bind('<Leave>', lambda e, b=btn, c=color: b.config(bg=self.COLORS['surface'], fg=c))
            else:
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.COLORS['hover']))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.COLORS['surface']))
            
            self.filter_buttons[filter_type] = btn
        
        # Highlight active filter
        self.filter_buttons['all'].config(bg=self.COLORS['hover'], 
                                         font=("Segoe UI", 10, "bold"))

    def create_top_bar(self, parent):
        """Create top bar with search and actions"""
        top_bar = tk.Frame(parent, bg=self.COLORS['background'])
        top_bar.pack(fill='x', padx=20, pady=20)
        
        # Search bar
        search_frame = tk.Frame(top_bar, bg=self.COLORS['surface'], 
                               relief='solid', bd=1)
        search_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(search_frame, text="🔍", font=("Segoe UI", 14),
                bg=self.COLORS['surface']).pack(side='left', padx=(10, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.on_search_change())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Segoe UI", 11), bg=self.COLORS['surface'],
                               fg=self.COLORS['text'], relief='flat', bd=0)
        search_entry.pack(side='left', fill='x', expand=True, ipady=8)
        
        # Action buttons
        actions_frame = tk.Frame(top_bar, bg=self.COLORS['background'])
        actions_frame.pack(side='right', padx=(10, 0))
        
        # Detailed add button
        detailed_btn = tk.Button(actions_frame, text="+ Detailed Task",
                                font=("Segoe UI", 10, "bold"),
                                bg=self.COLORS['success'], fg='white',
                                relief='flat', cursor='hand2',
                                padx=20, pady=10,
                                command=self.open_detailed_task_dialog)
        detailed_btn.pack(side='left', padx=5)
        
        detailed_btn.bind('<Enter>', lambda e: detailed_btn.config(bg=self._darken_color(self.COLORS['success'])))
        detailed_btn.bind('<Leave>', lambda e: detailed_btn.config(bg=self.COLORS['success']))

    def create_stats_bar(self, parent):
        """Create statistics bar"""
        stats_container = tk.Frame(parent, bg=self.COLORS['background'])
        stats_container.pack(fill='x', padx=20, pady=(0, 20))
        
        self.stat_widgets = {}
        
        stats = [
            ('total', 'Total', '📊', self.COLORS['primary']),
            ('todo', 'To Do', '📋', '#EF4444'),  # Red
            ('progress', 'In Progress', '⚡', '#F59E0B'),  # Yellow
            ('done', 'Completed', '✅', '#10B981'),  # Green
        ]
        
        for key, label, icon, color in stats:
            stat_card = tk.Frame(stats_container, bg=self.COLORS['surface'],
                                relief='solid', bd=1)
            stat_card.pack(side='left', fill='x', expand=True, padx=5)
            
            content = tk.Frame(stat_card, bg=self.COLORS['surface'])
            content.pack(padx=20, pady=15)
            
            tk.Label(content, text=icon, font=("Segoe UI", 20),
                    bg=self.COLORS['surface']).pack(side='left', padx=(0, 10))
            
            text_frame = tk.Frame(content, bg=self.COLORS['surface'])
            text_frame.pack(side='left')
            
            count_label = tk.Label(text_frame, text="0", 
                                  font=("Segoe UI", 24, "bold"),
                                  bg=self.COLORS['surface'], fg=color)
            count_label.pack(anchor='w')
            
            tk.Label(text_frame, text=label, font=("Segoe UI", 9),
                    bg=self.COLORS['surface'], 
                    fg=self.COLORS['text_light']).pack(anchor='w')
            
            self.stat_widgets[key] = count_label

    def create_task_list(self, parent):
        """Create scrollable task list"""
        # Container
        list_container = tk.Frame(parent, bg=self.COLORS['background'])
        list_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Canvas and scrollbar
        canvas = tk.Canvas(list_container, bg=self.COLORS['background'],
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient='vertical',
                                 command=canvas.yview)
        
        self.task_list_frame = tk.Frame(canvas, bg=self.COLORS['background'])
        
        self.task_list_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.task_list_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # Mouse wheel binding
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        self.task_canvas = canvas

    def render_tasks(self):
        """Render all filtered tasks"""
        # Clear existing
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_tasks:
            # Empty state
            empty_frame = tk.Frame(self.task_list_frame, bg=self.COLORS['background'])
            empty_frame.pack(expand=True, fill='both', pady=100)
            
            tk.Label(empty_frame, text="📭", font=("Segoe UI", 48),
                    bg=self.COLORS['background']).pack()
            tk.Label(empty_frame, text="No tasks found", 
                    font=("Segoe UI", 16),
                    bg=self.COLORS['background'], 
                    fg=self.COLORS['text_light']).pack(pady=10)
            tk.Label(empty_frame, text="Create a new task to get started!", 
                    font=("Segoe UI", 11),
                    bg=self.COLORS['background'], 
                    fg=self.COLORS['text_light']).pack()
            return
        
        # Group by status
        grouped_tasks = {
            'todo': [],
            'progress': [],
            'done': []
        }
        
        for task in self.filtered_tasks:
            status = task.get('status', 'todo')
            grouped_tasks[status].append(task)
        
        # Render each group
        for status, label in [('todo', 'To Do'), ('progress', 'In Progress'), ('done', 'Completed')]:
            if grouped_tasks[status]:
                # Section header
                header = tk.Frame(self.task_list_frame, bg=self.COLORS['background'])
                header.pack(fill='x', pady=(10, 5))
                
                tk.Label(header, text=label, font=("Segoe UI", 14, "bold"),
                        bg=self.COLORS['background'], 
                        fg=self.COLORS['text']).pack(side='left')
                
                tk.Label(header, text=f"{len(grouped_tasks[status])}", 
                        font=("Segoe UI", 11),
                        bg=self.COLORS['background'], 
                        fg=self.COLORS['text_light']).pack(side='left', padx=10)
                
                # Tasks
                for task in grouped_tasks[status]:
                    self.create_task_card(self.task_list_frame, task)

    def create_task_card(self, parent, task):
        """Create individual task card"""
        # Determine if task is completed
        status = task.get('status', 'todo')
        is_completed = status == 'done'
        
        # Card container - green background if completed
        card_bg = '#D1FAE5' if is_completed else self.COLORS['surface']  # Light green for completed
        card = tk.Frame(parent, bg=card_bg, 
                       relief='solid', bd=1, cursor='hand2')
        card.pack(fill='x', pady=5)
        
        # Content - green background if completed
        content = tk.Frame(card, bg=card_bg)
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Left side - checkbox and content
        left_frame = tk.Frame(content, bg=card_bg)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Top row - priority, title, badges
        top_row = tk.Frame(left_frame, bg=card_bg)
        top_row.pack(fill='x')
        
        # Priority indicator with colored dot
        priority = task.get('priority', 'medium')
        priority_color_map = {
            'high': ('#EF4444', 'Red', 'High'),
            'medium': ('#F59E0B', 'Yellow', 'Medium'),
            'low': ('#10B981', 'Green', 'Low')
        }
        priority_color, priority_name, priority_label = priority_color_map.get(priority, ('#6B7280', 'Gray', 'None'))
        
        # Create colored priority indicator
        priority_indicator = tk.Canvas(top_row, width=24, height=24, 
                                      bg=card_bg, highlightthickness=0)
        priority_indicator.pack(side='left', padx=(0, 10))
        priority_indicator.create_oval(4, 4, 20, 20, outline='', fill=priority_color)
        priority_indicator.create_oval(6, 6, 18, 18, outline='white', width=1)
        
        # Priority label
        priority_text = tk.Label(top_row, text=priority_label,
                               font=("Segoe UI", 9, "bold"),
                               bg=card_bg,
                               fg=priority_color)
        priority_text.pack(side='left', padx=(0, 10))
        
        # Title
        title_text = task.get('title', 'Untitled')
        if task.get('status') == 'done':
            title_text = f"~~{title_text}~~"
            title_fg = self.COLORS['text_light']
        else:
            title_fg = self.COLORS['text']
        
        title_label = tk.Label(top_row, text=title_text,
                              font=("Segoe UI", 12, "bold"),
                              bg=card_bg, fg=title_fg,
                              anchor='w')
        title_label.pack(side='left', fill='x', expand=True)
        
        # Status badge
        status_config = self.COLORS[status]
        
        status_labels = {'todo': 'To Do', 'progress': 'In Progress', 'done': 'Done'}
        status_badge = tk.Label(top_row, text=status_labels[status],
                               font=("Segoe UI", 8, "bold"),
                               bg=status_config['bg'], fg=status_config['text'],
                               padx=8, pady=3)
        status_badge.pack(side='right', padx=5)
        
        # Bottom row - description, deadline
        if task.get('description') or task.get('deadline'):
            bottom_row = tk.Frame(left_frame, bg=card_bg)
            bottom_row.pack(fill='x', pady=(8, 0))
            
            # Description
            if task.get('description'):
                desc = task['description']
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                
                tk.Label(bottom_row, text=desc,
                        font=("Segoe UI", 9), bg=card_bg,
                        fg=self.COLORS['text_light'], anchor='w').pack(side='left', fill='x')
            
            # Deadline
            if task.get('deadline'):
                deadline_str = task['deadline']
                try:
                    deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    
                    if deadline_dt < now:
                        deadline_color = '#EF4444'  # Red - overdue
                        deadline_prefix = "⚠️ "
                    elif deadline_dt < now + timedelta(days=1):
                        deadline_color = '#F59E0B'  # Yellow - due soon
                        deadline_prefix = "⚠️ "
                    else:
                        deadline_color = '#10B981'  # Green - on time
                        deadline_prefix = "📅 "
                    
                    deadline_display = deadline_dt.strftime("%b %d, %H:%M")
                    
                    deadline_label = tk.Label(bottom_row, 
                                            text=f"{deadline_prefix}{deadline_display}",
                                            font=("Segoe UI", 9, "bold"),
                                            bg=card_bg,
                                            fg=deadline_color)
                    deadline_label.pack(side='right', padx=(10, 0))
                except:
                    pass
        else:
            bottom_row = None
        
        # Right side - actions
        actions_frame = tk.Frame(content, bg=card_bg)
        actions_frame.pack(side='right', padx=(10, 0))
        
        # Action buttons
        action_buttons = []
        
        # Edit button
        edit_btn = tk.Label(actions_frame, text="✏️", font=("Segoe UI", 14),
                           bg=card_bg, cursor='hand2')
        edit_btn.pack(side='left', padx=5)
        edit_btn.bind('<Button-1>', lambda e: self.edit_task(task['id']))
        action_buttons.append(edit_btn)
        
        # Status change buttons
        if status == 'progress':
            # Show yellow icon when in progress
            progress_btn = tk.Label(actions_frame, text="⚡", font=("Segoe UI", 16),
                                   bg=card_bg, cursor='hand2', fg='#F59E0B')  # Yellow
            progress_btn.pack(side='left', padx=5)
            action_buttons.append(progress_btn)
        else:
            progress_btn = tk.Label(actions_frame, text="⚡", font=("Segoe UI", 14),
                                   bg=card_bg, cursor='hand2', fg='#F59E0B')  # Yellow
            progress_btn.pack(side='left', padx=5)
            progress_btn.bind('<Button-1>', lambda e: self.change_status(task['id'], 'progress'))
            action_buttons.append(progress_btn)
        
        # Done button - green if completed
        if status == 'done':
            done_btn = tk.Label(actions_frame, text="✅", font=("Segoe UI", 16),
                               bg=card_bg, cursor='hand2', fg='#10B981')  # Green checkmark
            done_btn.pack(side='left', padx=5)
            action_buttons.append(done_btn)
        else:
            done_btn = tk.Label(actions_frame, text="✅", font=("Segoe UI", 14),
                               bg=card_bg, cursor='hand2')
            done_btn.pack(side='left', padx=5)
            done_btn.bind('<Button-1>', lambda e: self.change_status(task['id'], 'done'))
            action_buttons.append(done_btn)
        
        # Delete button
        delete_btn = tk.Label(actions_frame, text="🗑️", font=("Segoe UI", 14),
                             bg=card_bg, cursor='hand2')
        delete_btn.pack(side='left', padx=5)
        delete_btn.bind('<Button-1>', lambda e: self.delete_task(task['id']))
        action_buttons.append(delete_btn)
        
        # Hover effects - lighter green for completed tasks
        hover_bg = '#E6FCF0' if is_completed else self.COLORS['hover']
        
        def on_enter(e):
            card.config(bg=hover_bg, relief='solid', bd=2,
                       highlightthickness=0)
            content.config(bg=hover_bg)
            left_frame.config(bg=hover_bg)
            top_row.config(bg=hover_bg)
            priority_indicator.config(bg=hover_bg)
            for widget in top_row.winfo_children():
                try:
                    if widget != status_badge:
                        widget.config(bg=hover_bg)
                except:
                    pass
            
            if bottom_row:
                bottom_row.config(bg=hover_bg)
                for widget in bottom_row.winfo_children():
                    try:
                        widget.config(bg=hover_bg)
                    except:
                        pass
            
            actions_frame.config(bg=hover_bg)
            for btn in action_buttons:
                btn.config(bg=hover_bg)
        
        def on_leave(e):
            card.config(bg=card_bg, relief='solid', bd=1)
            content.config(bg=card_bg)
            left_frame.config(bg=card_bg)
            top_row.config(bg=card_bg)
            priority_indicator.config(bg=card_bg)
            for widget in top_row.winfo_children():
                try:
                    if widget != status_badge:
                        widget.config(bg=card_bg)
                except:
                    pass
            
            try:
                if bottom_row:
                    bottom_row.config(bg=card_bg)
                    for widget in bottom_row.winfo_children():
                        try:
                            widget.config(bg=card_bg)
                        except:
                            pass
            except:
                pass
            
            actions_frame.config(bg=card_bg)
            for btn in action_buttons:
                btn.config(bg=card_bg)
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        # Click to open details
        card.bind('<Button-1>', lambda e: self.edit_task(task['id']))

    # Task management methods
    def quick_add_task(self):
        """Quick add task from sidebar"""
        title = self.quick_task_var.get().strip()
        if not title:
            return
        
        task = {
            'id': str(uuid.uuid4()),  # Temporary UUID until saved to DB
            'title': title,
            'description': '',
            'priority': self.quick_priority_var.get(),
            'status': 'todo',
            'deadline': None,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed_at': None
        }
        
        self.tasks.append(task)
        # Save immediately to database
        self.save_task_to_db(task)
        self.apply_filters()
        self.update_stats()
        
        # Clear input
        self.quick_task_var.set('')
        
        # Show feedback
        self.show_notification("✅ Task added successfully!", self.COLORS['success'])

    def open_detailed_task_dialog(self, task_id=None):
        """Open dialog for adding/editing detailed task"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Task Details" if task_id else "New Task")
        dialog.configure(bg=self.COLORS['background'])
        dialog.geometry("500x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 650) // 2
        dialog.geometry(f"500x650+{x}+{y}")
        
        # Get existing task data if editing
        task = None
        if task_id:
            task = next((t for t in self.tasks if t['id'] == task_id), None)
        
        # Container
        container = tk.Frame(dialog, bg=self.COLORS['surface'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(container, text="📝 Task Details",
                font=("Segoe UI", 18, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 20))
        
        # Task title
        tk.Label(container, text="Title*", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        title_var = tk.StringVar(value=task['title'] if task else '')
        title_entry = tk.Entry(container, textvariable=title_var,
                              font=("Segoe UI", 11), bg=self.COLORS['surface'],
                              fg=self.COLORS['text'], relief='solid', bd=1)
        title_entry.pack(fill='x', pady=(0, 15), ipady=8, ipadx=10)
        title_entry.focus()
        
        # Description
        tk.Label(container, text="Description", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        desc_text = tk.Text(container, height=6, wrap='word',
                           font=("Segoe UI", 10), bg=self.COLORS['surface'],
                           fg=self.COLORS['text'], relief='solid', bd=1,
                           padx=10, pady=8)
        desc_text.pack(fill='x', pady=(0, 15))
        if task and task.get('description'):
            desc_text.insert('1.0', task['description'])
        
        # Priority
        tk.Label(container, text="Priority", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        priority_frame = tk.Frame(container, bg=self.COLORS['surface'])
        priority_frame.pack(fill='x', pady=(0, 15))
        
        priority_var = tk.StringVar(value=task['priority'] if task else 'medium')
        
        # Colored priority options
        priority_options = [
            ('High', 'high', '#EF4444'),      # Red
            ('Medium', 'medium', '#F59E0B'),   # Yellow
            ('Low', 'low', '#10B981')          # Green
        ]
        
        priority_radio_buttons = []
        for label, value, color in priority_options:
            rb_frame = tk.Frame(priority_frame, bg=self.COLORS['surface'])
            rb_frame.pack(side='left', padx=(0, 20))
            
            # Colored indicator
            indicator = tk.Canvas(rb_frame, width=18, height=18,
                                 bg=self.COLORS['surface'], highlightthickness=0)
            indicator.pack(side='left', padx=(0, 6))
            indicator.create_oval(3, 3, 15, 15, outline='', fill=color)
            indicator.create_oval(5, 5, 13, 13, outline='white', width=1)
            
            rb = tk.Radiobutton(rb_frame, text=label, value=value,
                               variable=priority_var, bg=self.COLORS['surface'],
                               font=("Segoe UI", 10, "bold"),
                               fg=color,
                               selectcolor=self.COLORS['surface'],
                               activebackground=self.COLORS['surface'],
                               activeforeground=color)
            rb.pack(side='left')
            priority_radio_buttons.append((rb, indicator, value, color))
        
        # Update indicators when selection changes
        def update_detailed_priority_indicators(*args):
            selected = priority_var.get()
            for rb, indicator, value, color in priority_radio_buttons:
                is_selected = value == selected
                indicator.delete('all')
                if is_selected:
                    # Draw larger circle with ring for selected
                    indicator.create_oval(1, 1, 17, 17, outline=color, width=2, fill='')
                    indicator.create_oval(4, 4, 14, 14, outline='', fill=color)
                else:
                    indicator.create_oval(3, 3, 15, 15, outline='', fill=color)
                    indicator.create_oval(5, 5, 13, 13, outline='white', width=1)
                rb.config(fg=color if is_selected else self.COLORS['text'])
        
        priority_var.trace('w', update_detailed_priority_indicators)
        update_detailed_priority_indicators()  # Initial update
        
        # Status (only if editing)
        if task:
            tk.Label(container, text="Status", font=("Segoe UI", 10, "bold"),
                    bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
            
            status_frame = tk.Frame(container, bg=self.COLORS['surface'])
            status_frame.pack(fill='x', pady=(0, 15))
            
            status_var = tk.StringVar(value=task['status'])
            
            statuses = [
                ('📋 To Do', 'todo'),
                ('⚡ In Progress', 'progress'),
                ('✅ Done', 'done')
            ]
            
            for label, value in statuses:
                rb = tk.Radiobutton(status_frame, text=label, value=value,
                                   variable=status_var, bg=self.COLORS['surface'],
                                   font=("Segoe UI", 10), selectcolor=self.COLORS['surface'],
                                   activebackground=self.COLORS['surface'])
                rb.pack(side='left', padx=(0, 15))
        else:
            status_var = tk.StringVar(value='todo')
        
        # Deadline
        tk.Label(container, text="Deadline (Optional)", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        deadline_frame = tk.Frame(container, bg=self.COLORS['surface'])
        deadline_frame.pack(fill='x', pady=(0, 20))
        
        deadline_var = tk.StringVar(value=task['deadline'] if task and task.get('deadline') else '')
        deadline_entry = tk.Entry(deadline_frame, textvariable=deadline_var,
                                 font=("Segoe UI", 10), state='readonly',
                                 readonlybackground=self.COLORS['surface'],
                                 fg=self.COLORS['text'], relief='solid', bd=1)
        deadline_entry.pack(side='left', fill='x', expand=True, ipady=6, ipadx=10)
        
        def pick_deadline():
            self.open_datetime_picker(deadline_var)
        
        date_btn = tk.Button(deadline_frame, text="📅 Pick Date",
                            font=("Segoe UI", 9), bg=self.COLORS['primary'],
                            fg='white', relief='flat', cursor='hand2',
                            padx=15, pady=6, command=pick_deadline)
        date_btn.pack(side='left', padx=(10, 0))
        
        if deadline_var.get():
            clear_btn = tk.Button(deadline_frame, text="✕",
                                 font=("Segoe UI", 9), bg=self.COLORS['danger'],
                                 fg='white', relief='flat', cursor='hand2',
                                 padx=10, pady=6,
                                 command=lambda: deadline_var.set(''))
            clear_btn.pack(side='left', padx=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(container, bg=self.COLORS['surface'])
        button_frame.pack(fill='x', pady=(20, 0))
        
        def save_task():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Validation Error", "Please enter a task title.")
                return
            
            description = desc_text.get('1.0', 'end').strip()
            priority = priority_var.get()
            status = status_var.get()
            deadline = deadline_var.get().strip() or None
            
            if task:
                # Update existing
                task['title'] = title
                task['description'] = description
                task['priority'] = priority
                task['status'] = status
                task['deadline'] = deadline
                if status == 'done' and not task.get('completed_at'):
                    task['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif status != 'done':
                    task['completed_at'] = None
                # Save immediately to database
                self.save_task_to_db(task)
            else:
                # Create new
                new_task = {
                    'id': str(uuid.uuid4()),  # Temporary UUID until saved to DB
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'status': status,
                    'deadline': deadline,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'completed_at': None
                }
                self.tasks.append(new_task)
                # Save immediately to database
                self.save_task_to_db(new_task)
            
            self.apply_filters()
            self.update_stats()
            dialog.destroy()
            
            self.show_notification("✅ Task saved!", self.COLORS['success'])
        
        save_btn = tk.Button(button_frame, text="💾 Save Task",
                            font=("Segoe UI", 11, "bold"),
                            bg=self.COLORS['primary'], fg='white',
                            relief='flat', cursor='hand2',
                            padx=20, pady=10, command=save_task)
        save_btn.pack(side='right')
        
        cancel_btn = tk.Button(button_frame, text="Cancel",
                              font=("Segoe UI", 10),
                              bg=self.COLORS['text_light'], fg='white',
                              relief='flat', cursor='hand2',
                              padx=20, pady=10, command=dialog.destroy)
        cancel_btn.pack(side='right', padx=(0, 10))
        
        # Keyboard shortcuts
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Control-Return>', lambda e: save_task())

    def edit_task(self, task_id):
        """Open edit dialog for task"""
        self.open_detailed_task_dialog(task_id)

    def change_status(self, task_id, new_status):
        """Change task status"""
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if task:
            task['status'] = new_status
            if new_status == 'done':
                task['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                task['completed_at'] = None
            
            # Save immediately to database
            self.save_task_to_db(task)
            self.apply_filters()
            self.update_stats()

    def delete_task(self, task_id):
        """Delete a task"""
        if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
            # Delete from database if available
            if self.db and self.user_id:
                try:
                    # Get database ID from mapping
                    db_id = self.task_id_map.get(task_id)
                    if db_id:
                        self.db.delete_task(db_id, self.user_id)
                        print(f"Deleted task {task_id} (DB ID: {db_id}) from database")
                    elif task_id.isdigit():
                        # Try direct deletion if it's a numeric ID
                        self.db.delete_task(int(task_id), self.user_id)
                        print(f"Deleted task {task_id} from database")
                except Exception as e:
                    print(f"Error deleting task from database: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Remove from local list and mapping
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            if task_id in self.task_id_map:
                del self.task_id_map[task_id]
            
            self.apply_filters()
            self.update_stats()
            self.show_notification("🗑️ Task deleted", self.COLORS['danger'])

    def set_filter(self, filter_type, param=None):
        """Set active filter"""
        self.current_filter = filter_type
        self.filter_param = param
        
        # Update button styles
        for key, btn in self.filter_buttons.items():
            if key == filter_type:
                btn.config(bg=self.COLORS['hover'], font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg=self.COLORS['surface'], font=("Segoe UI", 10))
        
        self.apply_filters()

    def apply_filters(self):
        """Apply current filters to task list"""
        filtered = self.tasks.copy()
        
        # Apply search
        if self.search_query:
            query = self.search_query.lower()
            filtered = [t for t in filtered if 
                       query in t['title'].lower() or 
                       query in t.get('description', '').lower()]
        
        # Apply filter
        if self.current_filter == 'today':
            today = datetime.now().date()
            filtered = [t for t in filtered if t.get('deadline') and 
                       datetime.strptime(t['deadline'], "%Y-%m-%d %H:%M").date() == today]
        elif self.current_filter == 'week':
            today = datetime.now().date()
            week_end = today + timedelta(days=7)
            filtered = [t for t in filtered if t.get('deadline') and 
                       today <= datetime.strptime(t['deadline'], "%Y-%m-%d %H:%M").date() <= week_end]
        elif self.current_filter == 'priority':
            priority = self.filter_param or 'high'
            filtered = [t for t in filtered if t.get('priority') == priority]
        
        self.filtered_tasks = filtered
        self.render_tasks()

    def on_search_change(self):
        """Handle search input change"""
        self.search_query = self.search_var.get().strip()
        self.apply_filters()

    def update_stats(self):
        """Update statistics display"""
        total = len(self.tasks)
        todo = len([t for t in self.tasks if t['status'] == 'todo'])
        progress = len([t for t in self.tasks if t['status'] == 'progress'])
        done = len([t for t in self.tasks if t['status'] == 'done'])
        
        self.stat_widgets['total'].config(text=str(total))
        self.stat_widgets['todo'].config(text=str(todo))
        self.stat_widgets['progress'].config(text=str(progress))
        self.stat_widgets['done'].config(text=str(done))

    def show_notification(self, message, color):
        """Show temporary notification"""
        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.configure(bg=color)
        
        # Position
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 20
        notification.geometry(f"300x60+{x}+{y}")
        
        tk.Label(notification, text=message, font=("Segoe UI", 11, "bold"),
                bg=color, fg='white', padx=20, pady=20).pack()
        
        notification.after(2000, notification.destroy)

    def open_datetime_picker(self, target_var):
        """Open datetime picker dialog"""
        picker = tk.Toplevel(self.root)
        picker.title("Select Date & Time")
        picker.configure(bg=self.COLORS['background'])
        picker.geometry("380x480")  # Increased size to show time picker
        picker.transient(self.root)
        picker.grab_set()
        
        # Center
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() - 380) // 2
        y = (picker.winfo_screenheight() - 480) // 2
        picker.geometry(f"380x480+{x}+{y}")
        
        # Container
        container = tk.Frame(picker, bg=self.COLORS['surface'])
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title
        tk.Label(container, text="📅 Select Date & Time",
                font=("Segoe UI", 14, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(pady=(0, 20))
        
        # Calendar
        now = datetime.now()
        year_var = tk.IntVar(value=now.year)
        month_var = tk.IntVar(value=now.month)
        day_var = tk.IntVar(value=now.day)
        hour_var = tk.IntVar(value=now.hour)
        minute_var = tk.IntVar(value=(now.minute // 15) * 15)
        
        # Calendar header
        cal_header = tk.Frame(container, bg=self.COLORS['surface'])
        cal_header.pack(fill='x', pady=(0, 10))
        
        prev_btn = tk.Button(cal_header, text='◀', font=("Segoe UI", 10),
                            bg=self.COLORS['primary'], fg='white',
                            relief='flat', cursor='hand2', padx=10)
        prev_btn.pack(side='left')
        
        month_label = tk.Label(cal_header, text="", font=("Segoe UI", 12, "bold"),
                              bg=self.COLORS['surface'], fg=self.COLORS['text'])
        month_label.pack(side='left', expand=True)
        
        next_btn = tk.Button(cal_header, text='▶', font=("Segoe UI", 10),
                            bg=self.COLORS['primary'], fg='white',
                            relief='flat', cursor='hand2', padx=10)
        next_btn.pack(side='right')
        
        # Calendar grid
        cal_frame = tk.Frame(container, bg=self.COLORS['surface'])
        cal_frame.pack(pady=(0, 15))
        
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, day in enumerate(days):
            tk.Label(cal_frame, text=day, font=("Segoe UI", 8, "bold"),
                    bg=self.COLORS['surface'], fg=self.COLORS['text_light'],
                    width=5).grid(row=0, column=i, padx=1, pady=2)
        
        day_buttons = []
        selected_day_btn = [None]  # Track selected day button
        
        def update_calendar():
            for btn in day_buttons:
                if isinstance(btn, tk.Button):
                    btn.destroy()
                elif isinstance(btn, tk.Label):
                    btn.destroy()
            day_buttons.clear()
            
            month_label.config(text=f"{_calendar.month_name[month_var.get()]} {year_var.get()}")
            
            cal = _calendar.Calendar(firstweekday=0)
            month_days = cal.monthdayscalendar(year_var.get(), month_var.get())
            
            row = 1
            for week in month_days:
                for col, day in enumerate(week):
                    if day == 0:
                        lbl = tk.Label(cal_frame, text="", width=5, height=2,
                                      bg=self.COLORS['surface'])
                        lbl.grid(row=row, column=col, padx=1, pady=1)
                        day_buttons.append(lbl)
                    else:
                        # Check if this is the selected day (for current displayed month)
                        current_month = month_var.get()
                        current_year = year_var.get()
                        selected_day = day_var.get()
                        is_selected = (day == selected_day)
                        is_today = (day == now.day and current_month == now.month and 
                                   current_year == now.year)
                        
                        btn = tk.Button(cal_frame, text=str(day), width=5, height=2,
                                       font=("Segoe UI", 9),
                                       bg=self.COLORS['primary'] if (is_selected or is_today) else self.COLORS['surface'],
                                       fg='white' if (is_selected or is_today) else self.COLORS['text'],
                                       relief='solid' if is_selected else 'flat',
                                       bd=2 if is_selected else 1,
                                       cursor='hand2',
                                       command=lambda d=day: select_day(d))
                        btn.grid(row=row, column=col, padx=1, pady=1)
                        day_buttons.append(btn)
                        
                        if is_selected:
                            selected_day_btn[0] = btn
                row += 1
        
        def select_day(day):
            """Handle day selection"""
            day_var.set(day)
            # Highlight the selected button
            for btn in day_buttons:
                if isinstance(btn, tk.Button) and btn.cget('text') == str(day):
                    if selected_day_btn[0]:
                        # Reset previous selected button
                        prev_day = selected_day_btn[0].cget('text')
                        is_today = (int(prev_day) == now.day and 
                                   month_var.get() == now.month and 
                                   year_var.get() == now.year)
                        selected_day_btn[0].config(
                            bg=self.COLORS['primary'] if is_today else self.COLORS['surface'],
                            fg='white' if is_today else self.COLORS['text'],
                            relief='flat', bd=1
                        )
                    # Highlight new selection
                    btn.config(bg=self.COLORS['primary'], fg='white', 
                              relief='solid', bd=2)
                    selected_day_btn[0] = btn
                    break
        
        def prev_month():
            m, y = month_var.get(), year_var.get()
            if m == 1:
                month_var.set(12)
                year_var.set(y - 1)
            else:
                month_var.set(m - 1)
            update_calendar()
        
        def next_month():
            m, y = month_var.get(), year_var.get()
            if m == 12:
                month_var.set(1)
                year_var.set(y + 1)
            else:
                month_var.set(m + 1)
            update_calendar()
        
        prev_btn.config(command=prev_month)
        next_btn.config(command=next_month)
        
        # Time picker - make it more visible
        time_label_frame = tk.Frame(container, bg=self.COLORS['surface'])
        time_label_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(time_label_frame, text="Time:", font=("Segoe UI", 11, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(side='left')
        
        time_frame = tk.Frame(container, bg=self.COLORS['surface'])
        time_frame.pack(fill='x', pady=(0, 20))
        
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=5,
                               textvariable=hour_var, wrap=True,
                               font=("Segoe UI", 10))
        hour_spin.pack(side='left', padx=(0, 5))
        
        tk.Label(time_frame, text=":", font=("Segoe UI", 14, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(side='left', padx=2)
        
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, increment=1,
                                 width=5, textvariable=minute_var, wrap=True,
                                 font=("Segoe UI", 10))
        minute_spin.pack(side='left', padx=(5, 0))
        
        # Buttons
        btn_frame = tk.Frame(container, bg=self.COLORS['surface'])
        btn_frame.pack(fill='x')
        
        def set_datetime():
            try:
                selected_day = day_var.get()
                if selected_day == 0:
                    messagebox.showwarning("Invalid Date", "Please select a day from the calendar.")
                    return
                dt = datetime(year_var.get(), month_var.get(), selected_day,
                            hour_var.get(), minute_var.get())
                target_var.set(dt.strftime("%Y-%m-%d %H:%M"))
                picker.destroy()
            except ValueError as e:
                messagebox.showwarning("Invalid Date", f"Please select a valid date. Error: {e}")
        
        save_btn = tk.Button(btn_frame, text="Set Date",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.COLORS['success'], fg='white',
                            relief='flat', cursor='hand2',
                            padx=20, pady=10, command=set_datetime)
        save_btn.pack(side='right')
        
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                              font=("Segoe UI", 10),
                              bg=self.COLORS['text_light'], fg='white',
                              relief='flat', cursor='hand2',
                              padx=20, pady=10, command=picker.destroy)
        cancel_btn.pack(side='right', padx=(0, 10))
        
        update_calendar()

    # Data persistence
    def load_tasks(self):
        """Load tasks from Supabase (or local JSON file as fallback)"""
        if self.db and self.user_id:
            try:
                db_tasks = self.db.get_user_tasks(self.user_id)
                # Convert database format to app format
                self.tasks = []
                self.task_id_map = {}  # Reset mapping
                for task in db_tasks:
                    db_id = task['id']
                    # Use database ID as string for local storage
                    local_id = str(db_id)
                    self.tasks.append({
                        'id': local_id,
                        'title': task['title'],
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 'medium'),
                        'status': task.get('status', 'todo'),
                        'deadline': task.get('deadline'),
                        'created_at': task.get('created_at', ''),
                        'completed_at': task.get('completed_at')
                    })
                    # Map local ID to database ID (they're the same when loaded from DB)
                    self.task_id_map[local_id] = db_id
                print(f"Loaded {len(self.tasks)} tasks from database for user_id {self.user_id}")
                return
            except Exception as e:
                print(f"Error loading tasks from database: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to local load
        
        # Fallback to local JSON file
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        else:
            self.tasks = []

    def save_task_to_db(self, task):
        """Save a single task to database immediately"""
        if self.db and self.user_id:
            try:
                local_id = task['id']
                # Get database ID from mapping, or None if new task
                db_id = self.task_id_map.get(local_id)
                
                task_data = {
                    'id': db_id,  # Use mapped database ID, or None for new tasks
                    'title': task['title'],
                    'description': task.get('description', ''),
                    'priority': task.get('priority', 'medium'),
                    'status': task.get('status', 'todo'),
                    'deadline': task.get('deadline'),
                    'completed_at': task.get('completed_at')
                }
                
                # Save to database
                saved_db_id = self.db.save_task(self.user_id, task_data)
                
                # Update mapping with the database ID returned
                if saved_db_id:
                    # Update local ID if this was a new task
                    if local_id not in self.task_id_map or db_id is None:
                        if db_id is None:
                            # New task - update local ID to match database ID
                            old_id = local_id
                            task['id'] = str(saved_db_id)
                            self.task_id_map[str(saved_db_id)] = saved_db_id
                            # Update task references if needed
                            if old_id in self.task_id_map:
                                del self.task_id_map[old_id]
                        else:
                            self.task_id_map[local_id] = saved_db_id
                    else:
                        self.task_id_map[local_id] = saved_db_id
                
                print(f"Saved task '{task['title']}' to database with ID {saved_db_id}")
                return True
            except Exception as e:
                print(f"Error saving task to database: {e}")
                import traceback
                traceback.print_exc()
                return False
        return False
    
    def save_tasks(self):
        """Save all tasks to Supabase (or local JSON file as fallback)"""
        if self.db and self.user_id:
            try:
                # Save each task to database
                for task in self.tasks:
                    self.save_task_to_db(task)
                print(f"Saved {len(self.tasks)} tasks to database for user_id {self.user_id}")
                return
            except Exception as e:
                print(f"Error saving tasks to database: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to local save
        
        # Fallback to local JSON file
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save tasks: {e}")

    def start_auto_save(self):
        """Start auto-save timer"""
        self.save_tasks()
        self.root.after(60000, self.start_auto_save)  # Save every minute

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.open_detailed_task_dialog())
        self.root.bind('<Control-f>', lambda e: self.search_var.set('') or None)
        self.root.bind('<F5>', lambda e: self.apply_filters())

    def on_close(self):
        """Handle window close"""
        self.save_tasks()
        self.root.destroy()

    # Utility methods
    def _darken_color(self, hex_color, factor=0.8):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernToDoApp(root)
    root.mainloop()