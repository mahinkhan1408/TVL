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
        
        # Task input
        self.quick_task_var = tk.StringVar()
        task_entry = tk.Entry(quick_add, textvariable=self.quick_task_var,
                             font=("Segoe UI", 11), bg=self.COLORS['surface'],
                             fg=self.COLORS['text'], relief='solid', bd=1,
                             highlightthickness=1, highlightcolor=self.COLORS['primary'])
        task_entry.pack(fill='x', pady=(0, 10), ipady=8, ipadx=10)
        task_entry.bind('<Return>', lambda e: self.quick_add_task())
        
        # Priority selector
        priority_frame = tk.Frame(quick_add, bg=self.COLORS['surface'])
        priority_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(priority_frame, text="Priority:", font=("Segoe UI", 9),
                bg=self.COLORS['surface'], fg=self.COLORS['text_light']).pack(side='left')
        
        self.quick_priority_var = tk.StringVar(value='medium')
        
        priorities = [('🔴', 'high'), ('🟡', 'medium'), ('🟢', 'low')]
        for emoji, priority in priorities:
            rb = tk.Radiobutton(priority_frame, text=emoji, value=priority,
                               variable=self.quick_priority_var,
                               bg=self.COLORS['surface'], font=("Segoe UI", 14),
                               selectcolor=self.COLORS['surface'], 
                               activebackground=self.COLORS['surface'],
                               indicatoron=False, relief='flat', cursor='hand2',
                               padx=8)
            rb.pack(side='left', padx=2)
        
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
            ('📝 All Tasks', 'all', None),
            ('📅 Today', 'today', None),
            ('📆 This Week', 'week', None),
            ('⚡ High Priority', 'priority', 'high'),
        ]
        
        self.filter_buttons = {}
        for label, filter_type, param in filters:
            btn = tk.Button(filters_frame, text=label, 
                           font=("Segoe UI", 10),
                           bg=self.COLORS['surface'], fg=self.COLORS['text'],
                           relief='flat', cursor='hand2', anchor='w',
                           padx=15, pady=8,
                           command=lambda f=filter_type, p=param: self.set_filter(f, p))
            btn.pack(fill='x', pady=2)
            
            # Hover effects
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
            ('todo', 'To Do', '📋', self.COLORS['danger']),
            ('progress', 'In Progress', '⚡', self.COLORS['warning']),
            ('done', 'Completed', '✅', self.COLORS['success']),
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
        # Card container
        card = tk.Frame(parent, bg=self.COLORS['surface'], 
                       relief='solid', bd=1, cursor='hand2')
        card.pack(fill='x', pady=5)
        
        # Content
        content = tk.Frame(card, bg=self.COLORS['surface'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Left side - checkbox and content
        left_frame = tk.Frame(content, bg=self.COLORS['surface'])
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Top row - priority, title, badges
        top_row = tk.Frame(left_frame, bg=self.COLORS['surface'])
        top_row.pack(fill='x')
        
        # Priority indicator
        priority = task.get('priority', 'medium')
        priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        
        tk.Label(top_row, text=priority_colors.get(priority, '⚪'),
                font=("Segoe UI", 14), bg=self.COLORS['surface']).pack(side='left', padx=(0, 10))
        
        # Title
        title_text = task.get('title', 'Untitled')
        if task.get('status') == 'done':
            title_text = f"~~{title_text}~~"
            title_fg = self.COLORS['text_light']
        else:
            title_fg = self.COLORS['text']
        
        title_label = tk.Label(top_row, text=title_text,
                              font=("Segoe UI", 12, "bold"),
                              bg=self.COLORS['surface'], fg=title_fg,
                              anchor='w')
        title_label.pack(side='left', fill='x', expand=True)
        
        # Status badge
        status = task.get('status', 'todo')
        status_config = self.COLORS[status]
        
        status_labels = {'todo': 'To Do', 'progress': 'In Progress', 'done': 'Done'}
        status_badge = tk.Label(top_row, text=status_labels[status],
                               font=("Segoe UI", 8, "bold"),
                               bg=status_config['bg'], fg=status_config['text'],
                               padx=8, pady=3)
        status_badge.pack(side='right', padx=5)
        
        # Bottom row - description, deadline
        if task.get('description') or task.get('deadline'):
            bottom_row = tk.Frame(left_frame, bg=self.COLORS['surface'])
            bottom_row.pack(fill='x', pady=(8, 0))
            
            # Description
            if task.get('description'):
                desc = task['description']
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                
                tk.Label(bottom_row, text=desc,
                        font=("Segoe UI", 9), bg=self.COLORS['surface'],
                        fg=self.COLORS['text_light'], anchor='w').pack(side='left', fill='x')
            
            # Deadline
            if task.get('deadline'):
                deadline_str = task['deadline']
                try:
                    deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    
                    if deadline_dt < now:
                        deadline_color = self.COLORS['danger']
                        deadline_icon = "🔴"
                    elif deadline_dt < now + timedelta(days=1):
                        deadline_color = self.COLORS['warning']
                        deadline_icon = "🟡"
                    else:
                        deadline_color = self.COLORS['text_light']
                        deadline_icon = "📅"
                    
                    deadline_display = deadline_dt.strftime("%b %d, %H:%M")
                    
                    deadline_label = tk.Label(bottom_row, 
                                            text=f"{deadline_icon} {deadline_display}",
                                            font=("Segoe UI", 9),
                                            bg=self.COLORS['surface'],
                                            fg=deadline_color)
                    deadline_label.pack(side='right', padx=(10, 0))
                except:
                    pass
        else:
            bottom_row = None
        
        # Right side - actions
        actions_frame = tk.Frame(content, bg=self.COLORS['surface'])
        actions_frame.pack(side='right', padx=(10, 0))
        
        # Action buttons
        action_buttons = []
        
        # Edit button
        edit_btn = tk.Label(actions_frame, text="✏️", font=("Segoe UI", 14),
                           bg=self.COLORS['surface'], cursor='hand2')
        edit_btn.pack(side='left', padx=5)
        edit_btn.bind('<Button-1>', lambda e: self.edit_task(task['id']))
        action_buttons.append(edit_btn)
        
        # Status change buttons
        if status != 'progress':
            progress_btn = tk.Label(actions_frame, text="⚡", font=("Segoe UI", 14),
                                   bg=self.COLORS['surface'], cursor='hand2')
            progress_btn.pack(side='left', padx=5)
            progress_btn.bind('<Button-1>', lambda e: self.change_status(task['id'], 'progress'))
            action_buttons.append(progress_btn)
        
        if status != 'done':
            done_btn = tk.Label(actions_frame, text="✅", font=("Segoe UI", 14),
                               bg=self.COLORS['surface'], cursor='hand2')
            done_btn.pack(side='left', padx=5)
            done_btn.bind('<Button-1>', lambda e: self.change_status(task['id'], 'done'))
            action_buttons.append(done_btn)
        
        # Delete button
        delete_btn = tk.Label(actions_frame, text="🗑️", font=("Segoe UI", 14),
                             bg=self.COLORS['surface'], cursor='hand2')
        delete_btn.pack(side='left', padx=5)
        delete_btn.bind('<Button-1>', lambda e: self.delete_task(task['id']))
        action_buttons.append(delete_btn)
        
        # Hover effects
        def on_enter(e):
            card.config(bg=self.COLORS['hover'], relief='solid', bd=2,
                       highlightthickness=0)
            content.config(bg=self.COLORS['hover'])
            left_frame.config(bg=self.COLORS['hover'])
            top_row.config(bg=self.COLORS['hover'])
            for widget in top_row.winfo_children():
                try:
                    if widget != status_badge:
                        widget.config(bg=self.COLORS['hover'])
                except:
                    pass
            
            if bottom_row:
                bottom_row.config(bg=self.COLORS['hover'])
                for widget in bottom_row.winfo_children():
                    try:
                        widget.config(bg=self.COLORS['hover'])
                    except:
                        pass
            
            actions_frame.config(bg=self.COLORS['hover'])
            for btn in action_buttons:
                btn.config(bg=self.COLORS['hover'])
        
        def on_leave(e):
            card.config(bg=self.COLORS['surface'], relief='solid', bd=1)
            content.config(bg=self.COLORS['surface'])
            left_frame.config(bg=self.COLORS['surface'])
            top_row.config(bg=self.COLORS['surface'])
            for widget in top_row.winfo_children():
                try:
                    if widget != status_badge:
                        widget.config(bg=self.COLORS['surface'])
                except:
                    pass
            
            try:
                if bottom_row:
                    bottom_row.config(bg=self.COLORS['surface'])
                    for widget in bottom_row.winfo_children():
                        try:
                            widget.config(bg=self.COLORS['surface'])
                        except:
                            pass
            except:
                pass
            
            actions_frame.config(bg=self.COLORS['surface'])
            for btn in action_buttons:
                btn.config(bg=self.COLORS['surface'])
        
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
            'id': str(uuid.uuid4()),
            'title': title,
            'description': '',
            'priority': self.quick_priority_var.get(),
            'status': 'todo',
            'deadline': None,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed_at': None
        }
        
        self.tasks.append(task)
        self.save_tasks()
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
        
        priorities = [
            ('🔴 High', 'high'),
            ('🟡 Medium', 'medium'),
            ('🟢 Low', 'low')
        ]
        
        for label, value in priorities:
            rb = tk.Radiobutton(priority_frame, text=label, value=value,
                               variable=priority_var, bg=self.COLORS['surface'],
                               font=("Segoe UI", 10), selectcolor=self.COLORS['surface'],
                               activebackground=self.COLORS['surface'])
            rb.pack(side='left', padx=(0, 15))
        
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
            else:
                # Create new
                new_task = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'status': status,
                    'deadline': deadline,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'completed_at': None
                }
                self.tasks.append(new_task)
            
            self.save_tasks()
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
            
            self.save_tasks()
            self.apply_filters()
            self.update_stats()

    def delete_task(self, task_id):
        """Delete a task"""
        if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
            # Delete from database if available
            if self.db and self.user_id and task_id.isdigit():
                try:
                    self.db.delete_task(int(task_id), self.user_id)
                except Exception as e:
                    print(f"Error deleting task from database: {e}")
            
            # Remove from local list
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            self.save_tasks()
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
        picker.geometry("350x400")
        picker.transient(self.root)
        picker.grab_set()
        
        # Center
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() - 350) // 2
        y = (picker.winfo_screenheight() - 400) // 2
        picker.geometry(f"350x400+{x}+{y}")
        
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
        
        def update_calendar():
            for btn in day_buttons:
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
                        btn = tk.Button(cal_frame, text=str(day), width=5, height=2,
                                       font=("Segoe UI", 9),
                                       bg=self.COLORS['surface'], fg=self.COLORS['text'],
                                       relief='flat', cursor='hand2',
                                       command=lambda d=day: day_var.set(d))
                        btn.grid(row=row, column=col, padx=1, pady=1)
                        day_buttons.append(btn)
                        
                        if (day == now.day and month_var.get() == now.month and 
                            year_var.get() == now.year):
                            btn.config(bg=self.COLORS['primary'], fg='white')
                row += 1
        
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
        
        # Time picker
        time_frame = tk.Frame(container, bg=self.COLORS['surface'])
        time_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(time_frame, text="Time:", font=("Segoe UI", 10, "bold"),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(side='left', padx=(0, 10))
        
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=4,
                               textvariable=hour_var, wrap=True)
        hour_spin.pack(side='left', padx=5)
        
        tk.Label(time_frame, text=":", font=("Segoe UI", 12),
                bg=self.COLORS['surface'], fg=self.COLORS['text']).pack(side='left')
        
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=45, increment=15,
                                 width=4, textvariable=minute_var, wrap=True)
        minute_spin.pack(side='left', padx=5)
        
        # Buttons
        btn_frame = tk.Frame(container, bg=self.COLORS['surface'])
        btn_frame.pack(fill='x')
        
        def set_datetime():
            try:
                dt = datetime(year_var.get(), month_var.get(), day_var.get(),
                            hour_var.get(), minute_var.get())
                target_var.set(dt.strftime("%Y-%m-%d %H:%M"))
                picker.destroy()
            except ValueError:
                messagebox.showwarning("Invalid Date", "Please select a valid date.")
        
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
                for task in db_tasks:
                    self.tasks.append({
                        'id': str(task['id']),
                        'title': task['title'],
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 'medium'),
                        'status': task.get('status', 'todo'),
                        'deadline': task.get('deadline'),
                        'created_at': task.get('created_at', ''),
                        'completed_at': task.get('completed_at')
                    })
                return
            except Exception as e:
                print(f"Error loading tasks from database: {e}")
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

    def save_tasks(self):
        """Save tasks to Supabase (or local JSON file as fallback)"""
        if self.db and self.user_id:
            try:
                # Save each task to database
                for task in self.tasks:
                    task_data = {
                        'id': int(task['id']) if task['id'].isdigit() else None,
                        'title': task['title'],
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 'medium'),
                        'status': task.get('status', 'todo'),
                        'deadline': task.get('deadline'),
                        'completed_at': task.get('completed_at')
                    }
                    self.db.save_task(self.user_id, task_data)
                return
            except Exception as e:
                print(f"Error saving tasks to database: {e}")
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