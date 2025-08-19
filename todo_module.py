import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime, timedelta
import json
import os
import uuid
import sys

try:
    import winsound
except Exception:
    winsound = None

from theme_manager import theme_manager
import calendar as _calendar


class ToDoModule:
    """Enhanced To-Do board with improved UI, colors, and seamless design.

    Columns:
      - Need to Do (Soft Red)
      - In-Progress (Warm Orange)
      - Completed (Fresh Green)

    Features:
      - Modern card design with subtle shadows
      - Color-coded priority system
      - Full-width notes with height limit (4-5 lines)
      - Smooth drag and drop interactions
      - Enhanced visual feedback
      - Better typography and spacing
    """

    STORAGE_FILENAME = "todo_tasks.json"

    # Enhanced color scheme
    COLORS = {
        'todo': {
            'bg': '#FFE5E5',           # Soft red background
            'accent': '#FF6B6B',       # Red accent
            'border': '#FF9999',       # Light red border
            'hover': '#FFD1D1'         # Hover state
        },
        'progress': {
            'bg': '#FFF4E5',           # Warm orange background
            'accent': '#FF9F40',       # Orange accent
            'border': '#FFB366',       # Light orange border
            'hover': '#FFEAD1'         # Hover state
        },
        'done': {
            'bg': '#E8F8E8',           # Fresh green background
            'accent': '#4CAF50',       # Green accent
            'border': '#81C784',       # Light green border
            'hover': '#F1FBF1'         # Hover state
        }
    }

    # UI Constants
    CARD_RADIUS = 12
    SHADOW_COLOR = "#E0E0E0"
    TEXT_PRIMARY = "#2C3E50"
    TEXT_SECONDARY = "#7F8C8D"
    WHITE = "#FFFFFF"
    BACKGROUND = "#F8F9FA"

    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced To-Do Board")

        # Theme
        self.colors = theme_manager.get_current_colors()
        theme_manager.register_theme_callback(self.on_theme_changed)

        # Enhanced window setup
        self.root.update_idletasks()
        width = 1000
        height = 650
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg=self.BACKGROUND)

        # Data / storage
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.storage_path = os.path.join(self.app_data_dir, self.STORAGE_FILENAME)
        self.tasks_by_id = {}
        self._load_tasks()

        # Ensure we persist on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Drag state
        self._dragging_card = None
        self._drag_start_xy = (0, 0)

        # Create UI
        self._create_header()
        self._create_columns()
        self._render_all_columns()

        # Reminder loop
        self._scheduled_ids = set()
        self._deadline_notified = set()
        self.root.after(30_000, self._check_deadlines)

    def _create_header(self):
        """Create enhanced header with modern styling"""
        header_container = tk.Frame(self.root, bg=self.BACKGROUND)
        header_container.pack(fill='x', padx=20, pady=(20, 10))

        # Main header card
        header = tk.Frame(header_container, bg=self.WHITE, relief='flat', bd=0)
        header.pack(fill='x')
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(header_container, bg=self.SHADOW_COLOR, height=2)
        shadow_frame.place(in_=header, x=2, y=2, relwidth=1, relheight=1)
        header.lift()

        # Header content
        content = tk.Frame(header, bg=self.WHITE)
        content.pack(fill='both', expand=True, padx=25, pady=20)

        # Title
        title_label = tk.Label(content, text="✨ Add New Task", 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.WHITE, fg=self.TEXT_PRIMARY)
        title_label.pack(anchor='w', pady=(0, 15))

        # Form layout
        form_frame = tk.Frame(content, bg=self.WHITE)
        form_frame.pack(fill='x')

        # Left side - inputs
        left_panel = tk.Frame(form_frame, bg=self.WHITE)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 20))

        # Task title
        self.new_title_var = tk.StringVar()
        title_entry = self._create_modern_entry(left_panel, "Task Title", self.new_title_var)
        title_entry.pack(fill='x', pady=(0, 12))

        # Description with modern styling
        desc_label = tk.Label(left_panel, text="Description (optional)", 
                             font=("Segoe UI", 10), bg=self.WHITE, fg=self.TEXT_SECONDARY)
        desc_label.pack(anchor='w', pady=(0, 4))
        
        self.new_detail_text = tk.Text(left_panel, height=3, wrap='word',
                                      font=("Segoe UI", 10),
                                      bg=self.WHITE, fg=self.TEXT_PRIMARY,
                                      relief='solid', bd=1, borderwidth=1,
                                      highlightthickness=1, highlightcolor="#3498DB",
                                      padx=12, pady=8)
        self.new_detail_text.pack(fill='x', pady=(0, 12))

        # Deadline picker
        deadline_frame = tk.Frame(left_panel, bg=self.WHITE)
        deadline_frame.pack(fill='x')
        
        deadline_label = tk.Label(deadline_frame, text="Deadline", 
                                 font=("Segoe UI", 10), bg=self.WHITE, fg=self.TEXT_SECONDARY)
        deadline_label.pack(anchor='w', pady=(0, 4))
        
        deadline_input_frame = tk.Frame(deadline_frame, bg=self.WHITE)
        deadline_input_frame.pack(fill='x')
        
        self.new_deadline_var = tk.StringVar()
        self.deadline_entry = tk.Entry(deadline_input_frame, textvariable=self.new_deadline_var,
                                      font=("Segoe UI", 10), state='readonly',
                                      readonlybackground=self.WHITE,
                                      fg=self.TEXT_PRIMARY, relief='solid', bd=1,
                                      highlightthickness=1, highlightcolor="#3498DB")
        self.deadline_entry.pack(side='left', fill='x', expand=True)
        
        cal_btn = tk.Button(deadline_input_frame, text='📅', font=("Segoe UI", 12),
                           bg="#3498DB", fg='white', relief='flat', cursor='hand2',
                           padx=10, command=self._open_datetime_picker)
        cal_btn.pack(side='left', padx=(8, 0))

        # Right side - action button
        right_panel = tk.Frame(form_frame, bg=self.WHITE)
        right_panel.pack(side='right')
        
        add_btn = tk.Button(right_panel, text="➕ Add Task", 
                           font=("Segoe UI", 12, "bold"),
                           bg="#2ECC71", fg='white', relief='flat', cursor='hand2',
                           padx=30, pady=15, command=self._add_task)
        add_btn.pack(pady=(20, 0))

        # Hover effects
        self._add_button_hover_effect(add_btn, "#27AE60", "#2ECC71")
        self._add_button_hover_effect(cal_btn, "#2980B9", "#3498DB")

    def _create_modern_entry(self, parent, placeholder, textvariable):
        """Create a modern entry widget with placeholder text"""
        frame = tk.Frame(parent, bg=self.WHITE)
        
        label = tk.Label(frame, text=placeholder, font=("Segoe UI", 10),
                        bg=self.WHITE, fg=self.TEXT_SECONDARY)
        label.pack(anchor='w', pady=(0, 4))
        
        entry = tk.Entry(frame, textvariable=textvariable, font=("Segoe UI", 11),
                        bg=self.WHITE, fg=self.TEXT_PRIMARY, relief='solid', bd=1,
                        highlightthickness=1, highlightcolor="#3498DB")
        entry.pack(fill='x')
        
        return frame

    def _add_button_hover_effect(self, button, hover_color, normal_color):
        """Add hover effect to buttons"""
        def on_enter(e):
            button.configure(bg=hover_color)
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def _create_columns(self):
        """Create enhanced column layout"""
        # Main columns container
        columns_container = tk.Frame(self.root, bg=self.BACKGROUND)
        columns_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Title row
        title_row = tk.Frame(columns_container, bg=self.BACKGROUND, height=40)
        title_row.pack(fill='x', pady=(0, 10))
        title_row.pack_propagate(False)

        columns_data = [
            ('todo', 'Need to Do', '📋'),
            ('progress', 'In Progress', '⚡'),
            ('done', 'Completed', '✅')
        ]

        for i, (key, title, icon) in enumerate(columns_data):
            title_frame = tk.Frame(title_row, bg=self.BACKGROUND)
            title_frame.pack(side='left', fill='both', expand=True, padx=8)
            
            title_label = tk.Label(title_frame, text=f"{icon} {title}", 
                                  font=("Segoe UI", 14, "bold"),
                                  bg=self.BACKGROUND, fg=self.TEXT_PRIMARY)
            title_label.pack()

        # Columns frame
        columns_frame = tk.Frame(columns_container, bg=self.BACKGROUND)
        columns_frame.pack(fill='both', expand=True)
        columns_frame.grid_columnconfigure((0, 1, 2), weight=1)
        columns_frame.grid_rowconfigure(0, weight=1)

        self.column_frames = {}
        for i, (key, title, icon) in enumerate(columns_data):
            self._build_enhanced_column(columns_frame, i, key, title, self.COLORS[key])

    def _build_enhanced_column(self, parent, grid_col, key, title, color_scheme):
        """Build enhanced column with modern design"""
        wrapper = tk.Frame(parent, bg=self.BACKGROUND)
        wrapper.grid(row=0, column=grid_col, sticky='nsew', padx=8)

        # Column container with rounded appearance
        column_container = tk.Frame(wrapper, bg=color_scheme['bg'], relief='flat', bd=0)
        column_container.pack(fill='both', expand=True)

        # Add subtle border
        border_frame = tk.Frame(wrapper, bg=color_scheme['border'], height=2)
        border_frame.place(in_=column_container, x=0, y=0, relwidth=1, height=2)

        # Scrollable area
        canvas = tk.Canvas(column_container, bg=color_scheme['bg'], 
                          highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(column_container, orient='vertical', 
                               command=canvas.yview, width=12)
        scrollable_frame = tk.Frame(canvas, bg=color_scheme['bg'])

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Mouse wheel binding
        self._bind_mousewheel_enhanced(canvas, scrollable_frame)

        self.column_frames[key] = {
            'wrapper': wrapper,
            'container': column_container,
            'canvas': canvas,
            'scrollbar': scrollbar,
            'body': scrollable_frame,
            'colors': color_scheme
        }

    def _bind_mousewheel_enhanced(self, canvas, frame):
        """Enhanced mouse wheel binding"""
        def scroll_canvas(event):
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
                elif event.num == 4:
                    canvas.yview_scroll(-1, 'units')
                elif event.num == 5:
                    canvas.yview_scroll(1, 'units')
            except:
                pass

        # Bind to multiple widgets
        for widget in [canvas, frame]:
            widget.bind('<MouseWheel>', scroll_canvas)
            widget.bind('<Button-4>', scroll_canvas)
            widget.bind('<Button-5>', scroll_canvas)

    def _render_all_columns(self):
        """Render all columns with enhanced cards"""
        for key in ('todo', 'progress', 'done'):
            self._render_column(key)

    def _render_column(self, key):
        """Render individual column with enhanced task cards"""
        col = self.column_frames[key]
        body = col['body']
        
        # Clear existing widgets
        for widget in body.winfo_children():
            widget.destroy()

        # Get and sort tasks
        tasks = [t for t in self.tasks_by_id.values() if t['status'] == key]
        tasks.sort(key=lambda x: (x.get('deadline') or '9999-12-31 23:59', x['title']))

        # Create enhanced cards
        for task in tasks:
            self._create_enhanced_task_card(body, task, col['colors'])

    def _create_enhanced_task_card(self, parent, task, color_scheme):
        """Create enhanced task card with modern design"""
        # Main card container
        card_container = tk.Frame(parent, bg=color_scheme['bg'])
        card_container.pack(fill='x', padx=12, pady=8)

        # Card with shadow effect
        card = tk.Frame(card_container, bg=self.WHITE, relief='flat', bd=0)
        card.pack(fill='x')

        # Shadow
        shadow = tk.Frame(card_container, bg=self.SHADOW_COLOR, height=1)
        shadow.place(in_=card, x=2, y=2, relwidth=1, relheight=1)
        card.lift()

        # Card content
        content = tk.Frame(card, bg=self.WHITE)
        content.pack(fill='both', expand=True, padx=16, pady=12)

        # Header row with status indicator and menu
        header = tk.Frame(content, bg=self.WHITE)
        header.pack(fill='x', pady=(0, 8))

        # Status indicator
        status_indicator = tk.Canvas(header, width=12, height=12, 
                                   bg=self.WHITE, highlightthickness=0)
        status_indicator.pack(side='left', padx=(0, 10))
        status_indicator.create_oval(2, 2, 10, 10, 
                                   fill=color_scheme['accent'], 
                                   outline=color_scheme['accent'])

        # Title with enhanced typography
        title_label = tk.Label(header, text=task['title'], 
                              font=("Segoe UI", 12, "bold"),
                              bg=self.WHITE, fg=self.TEXT_PRIMARY,
                              anchor='w', justify='left')
        title_label.pack(side='left', fill='x', expand=True)

        # Menu button
        menu_btn = tk.Button(header, text='⋮', font=("Segoe UI", 14),
                           bg=self.WHITE, fg=self.TEXT_SECONDARY,
                           relief='flat', cursor='hand2', bd=0)
        menu_btn.pack(side='right')

        # Create context menu
        self._create_card_menu(menu_btn, task)

        # Description section (limited to 4-5 lines)
        description = (task.get('detail') or '').strip()
        if description:
            # Calculate approximate lines (assuming ~50 chars per line)
            max_chars = 250  # Roughly 5 lines
            if len(description) > max_chars:
                display_text = description[:max_chars] + "..."
            else:
                display_text = description

            desc_label = tk.Label(content, text=display_text,
                                 font=("Segoe UI", 10), bg=self.WHITE,
                                 fg=self.TEXT_SECONDARY, anchor='w',
                                 justify='left', wraplength=250)
            desc_label.pack(fill='x', pady=(0, 8))

        # Deadline section
        deadline = task.get('deadline')
        if deadline:
            deadline_frame = tk.Frame(content, bg=self.WHITE)
            deadline_frame.pack(fill='x')
            
            # Deadline icon and text
            deadline_icon = tk.Label(deadline_frame, text='🕒',
                                   font=("Segoe UI", 10), bg=self.WHITE)
            deadline_icon.pack(side='left', padx=(0, 6))
            
            deadline_label = tk.Label(deadline_frame, text=f"Due: {deadline}",
                                    font=("Segoe UI", 9), bg=self.WHITE,
                                    fg=self.TEXT_SECONDARY)
            deadline_label.pack(side='left')

            # Check if deadline is approaching
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
                now = datetime.now()
                if deadline_dt < now:
                    deadline_label.configure(fg="#E74C3C")  # Red for overdue
                elif deadline_dt < now + timedelta(hours=24):
                    deadline_label.configure(fg="#F39C12")  # Orange for urgent
            except:
                pass

        # Click handlers
        clickable_widgets = [card, content, header, title_label]
        for widget in clickable_widgets:
            widget.bind('<Button-1>', lambda e, t=task: self._open_detail(t['id']))

        # Drag and drop
        for widget in clickable_widgets:
            widget.bind('<Button-1>', lambda e, c=card, t=task: self._on_drag_start(e, c, t))
            widget.bind('<B1-Motion>', self._on_drag_motion)
            widget.bind('<ButtonRelease-1>', lambda e, t=task: self._on_drag_release(e, t['id']))

        # Hover effect
        def on_enter(e):
            card.configure(bg=color_scheme['hover'])
            content.configure(bg=color_scheme['hover'])
            header.configure(bg=color_scheme['hover'])
            for widget in clickable_widgets[1:]:  # Skip card itself
                try:
                    widget.configure(bg=color_scheme['hover'])
                except:
                    pass

        def on_leave(e):
            card.configure(bg=self.WHITE)
            content.configure(bg=self.WHITE)
            header.configure(bg=self.WHITE)
            for widget in clickable_widgets[1:]:  # Skip card itself
                try:
                    widget.configure(bg=self.WHITE)
                except:
                    pass

        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)

        # Store reference
        task['_card'] = card

    def _create_card_menu(self, button, task):
        """Create context menu for task card"""
        menu = tk.Menu(button, tearoff=0, font=("Segoe UI", 10))
        menu.add_command(label="✏️ Edit", command=lambda: self._open_detail(task['id']))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=lambda: self._delete_task(task['id']))
        
        def show_menu():
            try:
                menu.tk_popup(button.winfo_rootx(), 
                            button.winfo_rooty() + button.winfo_height())
            except:
                pass
        
        button.configure(command=show_menu)

    # Theme management
    def on_theme_changed(self, theme_name, colors):
        self.colors = colors
        try:
            self.root.configure(bg=self.BACKGROUND)
        except:
            pass

    # Task management methods (keeping existing functionality)
    def _load_tasks(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for t in data:
                        if 'id' in t:
                            self.tasks_by_id[t['id']] = {
                                'id': t.get('id'),
                                'title': t.get('title', ''),
                                'detail': t.get('detail', ''),
                                'deadline': t.get('deadline'),
                                'status': t.get('status', 'todo'),
                                'reminder_shown': bool(t.get('reminder_shown', False)),
                                'deadline_notified': bool(t.get('deadline_notified', False)),
                            }
                else:
                    self.tasks_by_id = {}
                    for tid, t in data.items():
                        self.tasks_by_id[tid] = {
                            'id': t.get('id', tid),
                            'title': t.get('title', ''),
                            'detail': t.get('detail', ''),
                            'deadline': t.get('deadline'),
                            'status': t.get('status', 'todo'),
                            'reminder_shown': bool(t.get('reminder_shown', False)),
                            'deadline_notified': bool(t.get('deadline_notified', False)),
                        }
            except:
                self.tasks_by_id = {}
        else:
            self.tasks_by_id = {}

    def _save_tasks(self):
        try:
            payload = []
            for t in self.tasks_by_id.values():
                payload.append({
                    'id': t.get('id'),
                    'title': t.get('title', ''),
                    'detail': t.get('detail', ''),
                    'deadline': t.get('deadline'),
                    'status': t.get('status', 'todo'),
                    'reminder_shown': bool(t.get('reminder_shown', False)),
                    'deadline_notified': bool(t.get('deadline_notified', False)),
                })
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
        except:
            pass

    def _on_window_close(self):
        try:
            self._save_tasks()
        finally:
            try:
                self.root.destroy()
            except:
                pass

    def _add_task(self):
        title = (self.new_title_var.get() or '').strip()
        if not title:
            messagebox.showinfo("To-Do", "Please enter a task title.")
            return
        
        deadline_raw = (self.new_deadline_var.get() or '').strip()
        deadline = None
        if deadline_raw:
            try:
                deadline_dt = datetime.strptime(deadline_raw, "%Y-%m-%d %H:%M")
                deadline = deadline_dt.strftime("%Y-%m-%d %H:%M")
            except:
                messagebox.showwarning("To-Do", "Deadline format must be YYYY-MM-DD HH:MM")
                return

        task_id = str(uuid.uuid4())
        self.tasks_by_id[task_id] = {
            'id': task_id,
            'title': title,
            'detail': self.new_detail_text.get('1.0', 'end').strip(),
            'deadline': deadline,
            'status': 'todo',
            'reminder_shown': False,
            'deadline_notified': False,
        }
        
        self._save_tasks()
        self._render_all_columns()
        
        # Clear form
        self.new_title_var.set("")
        self.new_deadline_var.set("")
        self.new_detail_text.delete('1.0', 'end')

    # Drag and drop implementation (enhanced)
    def _on_drag_start(self, event, widget, task):
        self._dragging_card = widget
        self._drag_start_xy = (event.x_root, event.y_root)
        
        # Enhanced ghost window
        try:
            self._ghost = tk.Toplevel(self.root)
            self._ghost.overrideredirect(True)
            self._ghost.attributes('-alpha', 0.8)
            self._ghost.configure(bg=self.WHITE)
            
            ghost_frame = tk.Frame(self._ghost, bg=self.WHITE, relief='solid', bd=1)
            ghost_frame.pack(padx=2, pady=2)
            
            tk.Label(ghost_frame, text=f"📌 {task['title'][:30]}...", 
                    font=("Segoe UI", 10, "bold"),
                    bg=self.WHITE, fg=self.TEXT_PRIMARY).pack(padx=12, pady=8)
            
            self._ghost.geometry(f"200x40+{event.x_root+15}+{event.y_root+15}")
        except:
            self._ghost = None

    def _on_drag_motion(self, event):
        try:
            self.root.configure(cursor='hand2')
        except:
            pass
        
        # Move ghost
        try:
            if self._ghost:
                self._ghost.geometry(f"200x40+{event.x_root+15}+{event.y_root+15}")
        except:
            pass
        
        # Enhanced visual feedback
        target = self._hit_test_column(event.x_root, event.y_root)
        for key, col in self.column_frames.items():
            try:
                if key == target:
                    col['container'].configure(relief='solid', bd=2, 
                                             highlightbackground=col['colors']['accent'])
                else:
                    col['container'].configure(relief='flat', bd=0)
            except:
                continue

    def _on_drag_release(self, event, task_id):
        try:
            self.root.configure(cursor='')
        except:
            pass
        
        # Destroy ghost
        try:
            if self._ghost:
                self._ghost.destroy()
                self._ghost = None
        except:
            pass
        
        if not self._dragging_card:
            return
        
        drop_target = self._hit_test_column(event.x_root, event.y_root)
        self._dragging_card = None
        
        if drop_target and drop_target != self.tasks_by_id[task_id]['status']:
            self.tasks_by_id[task_id]['status'] = drop_target
            self._save_tasks()
            self._render_all_columns()
        
        # Reset column highlights
        for col in self.column_frames.values():
            try:
                col['container'].configure(relief='flat', bd=0)
            except:
                continue

    def _hit_test_column(self, screen_x, screen_y):
        for key, col in self.column_frames.items():
            try:
                wrapper = col['wrapper']
                x = wrapper.winfo_rootx()
                y = wrapper.winfo_rooty()
                w = wrapper.winfo_width()
                h = wrapper.winfo_height()
                if x <= screen_x <= x + w and y <= screen_y <= y + h:
                    return key
            except:
                continue
        return None

    # Detail view (enhanced)
    def _open_detail(self, task_id):
        task = self.tasks_by_id.get(task_id)
        if not task:
            return
        
        # Enhanced detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("✏️ Edit Task")
        detail_window.configure(bg=self.BACKGROUND)
        detail_window.geometry("500x400")
        detail_window.transient(self.root)
        detail_window.grab_set()

        # Center the window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (400 // 2)
        detail_window.geometry(f"500x400+{x}+{y}")

        # Main container
        main_frame = tk.Frame(detail_window, bg=self.WHITE, relief='flat', bd=0)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(main_frame, text="📝 Task Details",
                              font=("Segoe UI", 16, "bold"),
                              bg=self.WHITE, fg=self.TEXT_PRIMARY)
        title_label.pack(anchor='w', pady=(0, 20))

        # Form fields
        title_var = tk.StringVar(value=task['title'])
        title_frame = self._create_modern_entry(main_frame, "Task Title", title_var)
        title_frame.pack(fill='x', pady=(0, 15))

        # Deadline
        deadline_var = tk.StringVar(value=task.get('deadline') or '')
        deadline_frame = self._create_modern_entry(main_frame, "Deadline (YYYY-MM-DD HH:MM)", deadline_var)
        deadline_frame.pack(fill='x', pady=(0, 15))

        # Description
        desc_label = tk.Label(main_frame, text="Description", 
                             font=("Segoe UI", 12, "bold"),
                             bg=self.WHITE, fg=self.TEXT_PRIMARY)
        desc_label.pack(anchor='w', pady=(0, 8))
        
        detail_text = tk.Text(main_frame, height=8, wrap='word',
                             font=("Segoe UI", 10),
                             bg=self.WHITE, fg=self.TEXT_PRIMARY,
                             relief='solid', bd=1, borderwidth=1,
                             highlightthickness=1, highlightcolor="#3498DB",
                             padx=12, pady=8)
        detail_text.pack(fill='both', expand=True, pady=(0, 20))
        detail_text.insert('1.0', task.get('detail', ''))

        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.WHITE)
        button_frame.pack(fill='x')

        def save_changes():
            new_title = title_var.get().strip()
            if not new_title:
                messagebox.showwarning("Edit Task", "Title cannot be empty")
                return
            
            deadline_str = deadline_var.get().strip()
            if deadline_str:
                try:
                    datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                except:
                    messagebox.showwarning("Edit Task", "Deadline format must be YYYY-MM-DD HH:MM")
                    return
            else:
                deadline_str = None
            
            self.tasks_by_id[task_id]['title'] = new_title
            self.tasks_by_id[task_id]['deadline'] = deadline_str
            self.tasks_by_id[task_id]['detail'] = detail_text.get('1.0', 'end').strip()
            self._save_tasks()
            self._render_all_columns()
            detail_window.destroy()

        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel",
                              font=("Segoe UI", 11),
                              bg="#95A5A6", fg='white', relief='flat',
                              cursor='hand2', padx=20, pady=10,
                              command=detail_window.destroy)
        cancel_btn.pack(side='right', padx=(10, 0))

        # Save button
        save_btn = tk.Button(button_frame, text="💾 Save Changes",
                            font=("Segoe UI", 11, "bold"),
                            bg="#3498DB", fg='white', relief='flat',
                            cursor='hand2', padx=20, pady=10,
                            command=save_changes)
        save_btn.pack(side='right')

        # Add hover effects
        self._add_button_hover_effect(save_btn, "#2980B9", "#3498DB")
        self._add_button_hover_effect(cancel_btn, "#7F8C8D", "#95A5A6")

    def _delete_task(self, task_id):
        if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
            if task_id in self.tasks_by_id:
                del self.tasks_by_id[task_id]
                self._save_tasks()
                self._render_all_columns()

    # Notification methods
    def _check_deadlines(self):
        now = datetime.now()
        for task in list(self.tasks_by_id.values()):
            deadline_str = task.get('deadline')
            if not deadline_str:
                continue
            
            try:
                deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            except:
                continue

            # 15 minutes before reminder
            if not task.get('reminder_shown') and now >= deadline_dt - timedelta(minutes=15) and now < deadline_dt:
                task['reminder_shown'] = True
                self._save_tasks()
                self._show_enhanced_reminder(task['title'])

            # Deadline notification
            if not task.get('deadline_notified') and now >= deadline_dt:
                task['deadline_notified'] = True
                self._save_tasks()
                self._play_deadline_sound()

        self.root.after(30_000, self._check_deadlines)

    def _show_enhanced_reminder(self, title):
        """Show enhanced reminder popup"""
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg="#F39C12")
        popup.attributes('-topmost', True)
        
        w, h = 350, 80
        try:
            x = self.root.winfo_rootx() + self.root.winfo_width() - w - 30
            y = self.root.winfo_rooty() + 30
        except:
            x, y = 100, 100
        
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        # Content frame
        content = tk.Frame(popup, bg="#F39C12")
        content.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Icon and text
        icon_label = tk.Label(content, text="⏰", font=("Segoe UI", 20),
                             bg="#F39C12", fg="white")
        icon_label.pack(side='left', padx=(15, 10), pady=15)
        
        text_frame = tk.Frame(content, bg="#F39C12")
        text_frame.pack(side='left', fill='both', expand=True, pady=15)
        
        tk.Label(text_frame, text="Reminder", font=("Segoe UI", 12, "bold"),
                bg="#F39C12", fg="white").pack(anchor='w')
        tk.Label(text_frame, text=f"Due in 15 minutes: {title}", 
                font=("Segoe UI", 10), bg="#F39C12", fg="white",
                wraplength=250).pack(anchor='w')
        
        # Auto-close after 4 seconds
        popup.after(4000, popup.destroy)

    def _play_deadline_sound(self):
        """Play deadline notification sound"""
        if winsound and sys.platform.startswith('win'):
            try:
                winsound.Beep(880, 2000)
            except:
                try:
                    self.root.bell()
                except:
                    pass
        else:
            try:
                self.root.bell()
                self.root.after(1000, self.root.bell)
            except:
                pass

    # Enhanced Date-Time Picker
    def _open_datetime_picker(self):
        """Enhanced date-time picker with modern UI"""
        picker = tk.Toplevel(self.root)
        picker.title("📅 Select Date & Time")
        picker.configure(bg=self.BACKGROUND)
        picker.geometry("300x350")
        picker.transient(self.root)
        picker.grab_set()

        # Center window
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() // 2) - (300 // 2)
        y = (picker.winfo_screenheight() // 2) - (350 // 2)
        picker.geometry(f"300x350+{x}+{y}")

        # Main container
        main_container = tk.Frame(picker, bg=self.WHITE, relief='flat', bd=0)
        main_container.pack(fill='both', expand=True, padx=15, pady=15)

        # Title
        title_label = tk.Label(main_container, text="📅 Select Date & Time",
                              font=("Segoe UI", 14, "bold"),
                              bg=self.WHITE, fg=self.TEXT_PRIMARY)
        title_label.pack(pady=(0, 20))

        # Calendar state
        now = datetime.now()
        current_year = tk.IntVar(value=now.year)
        current_month = tk.IntVar(value=now.month)
        selected_day = tk.IntVar(value=now.day)
        selected_hour = tk.IntVar(value=now.hour)
        selected_minute = tk.IntVar(value=(now.minute // 5) * 5)

        # Calendar header
        cal_header = tk.Frame(main_container, bg=self.WHITE)
        cal_header.pack(fill='x', pady=(0, 10))

        prev_btn = tk.Button(cal_header, text='◀', width=3,
                            font=("Segoe UI", 12), bg="#3498DB", fg='white',
                            relief='flat', cursor='hand2')
        prev_btn.pack(side='left')

        month_label = tk.Label(cal_header, text="", font=("Segoe UI", 12, "bold"),
                              bg=self.WHITE, fg=self.TEXT_PRIMARY)
        month_label.pack(side='left', expand=True)

        next_btn = tk.Button(cal_header, text='▶', width=3,
                            font=("Segoe UI", 12), bg="#3498DB", fg='white',
                            relief='flat', cursor='hand2')
        next_btn.pack(side='right')

        # Calendar grid
        cal_frame = tk.Frame(main_container, bg=self.WHITE)
        cal_frame.pack(pady=(0, 15))

        # Days header
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, day in enumerate(days):
            tk.Label(cal_frame, text=day, font=("Segoe UI", 9, "bold"),
                    bg=self.WHITE, fg=self.TEXT_SECONDARY, width=4).grid(row=0, column=i, padx=1, pady=2)

        day_buttons = []

        def update_calendar():
            # Clear existing buttons
            for btn in day_buttons:
                btn.destroy()
            day_buttons.clear()

            # Update month label
            month_label.configure(text=f"{_calendar.month_name[current_month.get()]} {current_year.get()}")

            # Generate calendar
            cal = _calendar.Calendar(firstweekday=0)
            month_days = cal.monthdayscalendar(current_year.get(), current_month.get())

            row = 1
            for week in month_days:
                for col, day in enumerate(week):
                    if day == 0:
                        # Empty cell
                        empty = tk.Label(cal_frame, text="", width=4, height=2, bg=self.WHITE)
                        empty.grid(row=row, column=col, padx=1, pady=1)
                        day_buttons.append(empty)
                    else:
                        # Day button
                        btn = tk.Button(cal_frame, text=str(day), width=4, height=2,
                                       font=("Segoe UI", 9),
                                       bg=self.WHITE, fg=self.TEXT_PRIMARY,
                                       relief='flat', cursor='hand2',
                                       command=lambda d=day: selected_day.set(d))
                        btn.grid(row=row, column=col, padx=1, pady=1)
                        day_buttons.append(btn)

                        # Highlight today
                        if (day == now.day and current_month.get() == now.month and 
                            current_year.get() == now.year):
                            btn.configure(bg="#E3F2FD", fg="#1976D2")
                row += 1

        def prev_month():
            month = current_month.get() - 1
            year = current_year.get()
            if month < 1:
                month = 12
                year -= 1
            current_month.set(month)
            current_year.set(year)
            update_calendar()

        def next_month():
            month = current_month.get() + 1
            year = current_year.get()
            if month > 12:
                month = 1
                year += 1
            current_month.set(month)
            current_year.set(year)
            update_calendar()

        prev_btn.configure(command=prev_month)
        next_btn.configure(command=next_month)

        # Time selection
        time_frame = tk.Frame(main_container, bg=self.WHITE)
        time_frame.pack(fill='x', pady=(0, 20))

        tk.Label(time_frame, text="🕐 Time:", font=("Segoe UI", 11, "bold"),
                bg=self.WHITE, fg=self.TEXT_PRIMARY).pack(side='left', padx=(0, 10))

        # Hour spinner
        hour_frame = tk.Frame(time_frame, bg=self.WHITE)
        hour_frame.pack(side='left', padx=(0, 5))
        
        hour_spin = ttk.Spinbox(hour_frame, from_=0, to=23, width=3,
                               textvariable=selected_hour, wrap=True,
                               font=("Segoe UI", 10))
        hour_spin.pack()

        tk.Label(time_frame, text=":", font=("Segoe UI", 12, "bold"),
                bg=self.WHITE, fg=self.TEXT_PRIMARY).pack(side='left', padx=2)

        # Minute spinner
        minute_frame = tk.Frame(time_frame, bg=self.WHITE)
        minute_frame.pack(side='left', padx=(5, 0))
        
        minute_spin = ttk.Spinbox(minute_frame, from_=0, to=55, increment=5,
                                 width=3, textvariable=selected_minute, wrap=True,
                                 font=("Segoe UI", 10))
        minute_spin.pack()

        # Buttons
        button_frame = tk.Frame(main_container, bg=self.WHITE)
        button_frame.pack(fill='x')

        def set_datetime():
            try:
                selected_dt = datetime(current_year.get(), current_month.get(),
                                     selected_day.get(), selected_hour.get(),
                                     selected_minute.get())
                self.new_deadline_var.set(selected_dt.strftime("%Y-%m-%d %H:%M"))
                picker.destroy()
            except ValueError:
                messagebox.showwarning("Date Picker", "Please select a valid date and time.")

        cancel_btn = tk.Button(button_frame, text="Cancel",
                              font=("Segoe UI", 10), bg="#95A5A6", fg='white',
                              relief='flat', cursor='hand2', padx=15, pady=8,
                              command=picker.destroy)
        cancel_btn.pack(side='right', padx=(10, 0))

        set_btn = tk.Button(button_frame, text="✓ Set Date",
                           font=("Segoe UI", 10, "bold"), bg="#27AE60", fg='white',
                           relief='flat', cursor='hand2', padx=15, pady=8,
                           command=set_datetime)
        set_btn.pack(side='right')

        # Add hover effects
        self._add_button_hover_effect(set_btn, "#229954", "#27AE60")
        self._add_button_hover_effect(cancel_btn, "#7F8C8D", "#95A5A6")
        self._add_button_hover_effect(prev_btn, "#2980B9", "#3498DB")
        self._add_button_hover_effect(next_btn, "#2980B9", "#3498DB")

        # Initialize calendar
        update_calendar()


# Additional utility functions can be added here if needed