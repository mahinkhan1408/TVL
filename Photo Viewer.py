import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import os
import glob
import sys
import shutil
import threading
from queue import Queue

# Try to register HEIC/HEIF support for iPhone photos
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC support not available, will skip HEIC files 

class FastImageViewer:
    """
    A fast image viewer using Tkinter and Pillow, featuring optimized scaling, 
    smooth zoom/pan via mouse scroll/drag, double-click selection, keyboard rotation, 
    and in-viewer drawing/marking. Rotation is now permanent upon key press (A/S).
    Supports a blurred image background for aesthetic purposes (not true desktop transparency).
    """
    def __init__(self, root=None):
        # If root is provided, use it; otherwise create a new Tk window
        if root is None:
            self.root = tk.Tk()
            self.is_standalone = True
        else:
            self.root = root
            self.is_standalone = False
        
        self.root.title("Fast Python Image Viewer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#2c3e50") 

        # --- State Variables ---
        self.image_files = []
        self.current_index = -1
        self.current_photo = None       
        self.cache = {}                 
        self.current_pil_img = None     
        
        self.zoom_factor = 1.0          
        self.image_offset_x = 0         
        self.image_offset_y = 0         
        self.image_item = None          
        
        self.selected_files = set()     
        self.current_rotation = 0
        
        # --- Performance Optimization for Large Images ---
        self.max_image_dimension = 4000  # Maximum width or height before downscaling
        self.max_cache_size = 3  # Reduce cache size to save memory
        
        # --- Gallery/Thumbnail View ---
        self.thumbnail_cache = {}  # Cache for thumbnails (LRU limited)
        self.thumbnail_cache_order = []  # Track access order for LRU eviction
        self.max_thumbnail_cache_size = 200  # Maximum number of thumbnails to keep in memory
        self.initial_thumbnail_load_count = 50  # Load first 50 thumbnails initially (very conservative for large folders)
        self.gallery_canvas = None
        self.thumbnail_size = 90  # Size of thumbnails in gallery (reduced for better fit)
        self.thumbnail_padding = 6  # Padding between thumbnails (3px on each side)
        self.thumbnail_spacing = self.thumbnail_size + self.thumbnail_padding  # Total width per thumbnail
        self.gallery_updating = False  # Flag to prevent multiple simultaneous updates
        self.thumbnail_load_queue = []  # Queue for loading thumbnails
        self.thumbnail_loading_active = False  # Flag to prevent multiple load operations
        self.thumbnails_loaded_range = (0, 0)  # Track which range of thumbnails have been loaded
        self.last_gallery_selection_index = -1  # Track last selected thumbnail for efficient updates
        self.gallery_thumbnails = {}  # Store canvas item IDs for thumbnails: {index: {'image_id': id, 'photo': PhotoImage}}
        
        # --- PERFORMANCE OPTIMIZATION ---
        self.zoom_update_pending = False
        self.zoom_update_id = None
        self.image_load_queue = Queue()
        self.loading_thread = None
        self.preview_cache = {}  # Cache for lower quality previews during zoom
        self.zoom_active = False       
        
        # --- NEW MARKER STATE ---
        self.marker_mode_active = False 
        self.spacebar_held = False      
        self.marks_cache = {}           
        self.last_mark_coord = None
        self.marker_color = "red"  # Default color: red, yellow, or green
        self.marker_width = 2  # Reduced from 5 to 2 for thinner lines
        
        # --- SHAPE MARKING STATE ---
        self.shape_mode_active = False
        self.current_shape_type = None  # "square", "circle", "line"
        self.shape_start_coord = None
        self.current_shape_item = None
        self.shapes_cache = {}  # Store shapes separately from marks
        self.selected_shape_id = None  # For resizing
        
        # --- ERASER STATE ---
        self.eraser_mode_active = False
        self.mark_items = {}  # Map canvas item IDs to mark indices
        self.shape_items = {}  # Map canvas item IDs to shape indices     
        
        # --- BLURRY BACKGROUND STATE ---
        self.background_image_path = None # Set this to an image path if you want a blurred background
        self.blurred_background_photo = None
        self.blurred_canvas_item = None
        
        # --- Setup UI Components ---
        self.create_widgets()
        
        # --- Bind Global Events ---
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Home>", lambda e: self.go_to_first_image())
        self.root.bind("<End>", lambda e: self.go_to_last_image())
        self.root.bind("<Configure>", self.on_resize)
        
        # --- Rotation Bindings (a for Left, s for Right) ---
        # NOTE: These now trigger permanent save/overwrite to the file.
        self.root.bind("a", lambda e: self.rotate_left())
        self.root.bind("s", lambda e: self.rotate_right())
        
        # --- Delete Binding (d for Delete) ---
        self.root.bind("d", lambda e: self.delete_current_image())
        
        # Use after to allow the window to fully initialize before asking for a folder
        self.root.after(100, self.load_directory) 

    def create_widgets(self):
        """Initializes and packs the main UI elements and defines styles."""
        
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        style.configure("TFrame", background="#34495e") # Keep frame background solid for readability
        style.configure("TLabel", background="#34495e", foreground="#ecf0f1", font=('Inter', 12))
        
        # --- Define ALL Button Styles via ttk.Style.configure ---
        
        # 1. Base TButton Style (for navigation, zoom, and disabled state) - Smaller buttons
        style.configure("TButton", font=('Inter', 9), background="#3498db", foreground="white", relief="flat", padding=[4, 2]) 
        style.map("TButton", background=[('active', '#2980b9'), ('disabled', '#7f8c8d')], foreground=[('disabled', '#bdc3c7')])
        
        # 2. Marker Button Styles
        style.configure("Marker.Off.TButton", background="#95a5a6", foreground="white", padding=[4, 2]) 
        style.configure("Marker.On.TButton", background="#e74c3c", foreground="white", padding=[4, 2])  
        
        # 3. Save Button Styles
        style.configure("Save.Enabled.TButton", background="#27ae60", foreground="white", padding=[4, 2]) 
        style.configure("Save.Disabled.TButton", background="#3498db", foreground="white", padding=[4, 2]) 
        
        # 4. Icon Button Style (for zoom buttons)
        style.configure("Icon.TButton", font=('Inter', 14, 'bold'), background="#3498db", foreground="white", relief="flat", padding=[2, 2], width=3) 
        style.map("Icon.TButton", background=[('active', '#2980b9'), ('disabled', '#7f8c8d')], foreground=[('disabled', '#bdc3c7')])
        # --- End Style Definitions ---

        # Main content area with left sidebar and canvas
        self.main_content = tk.Frame(self.root, bg="#34495e")
        self.main_content.pack(expand=True, fill=tk.BOTH)
        
        # Left sidebar for color selection (initially hidden - width 0)
        self.color_sidebar = tk.Frame(self.main_content, bg="#2c3e50", width=80)
        # Always pack it but with width 0 when hidden
        self.color_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.color_sidebar.pack_propagate(False)
        # Initially hide it by setting width to 0
        self.color_sidebar.config(width=0)
        
        # Create scrollable canvas for sidebar content
        sidebar_canvas = tk.Canvas(self.color_sidebar, bg="#2c3e50", highlightthickness=0, width=80)
        sidebar_scrollbar = tk.Scrollbar(self.color_sidebar, orient="vertical", command=sidebar_canvas.yview)
        self.sidebar_content = tk.Frame(sidebar_canvas, bg="#2c3e50")
        
        self.sidebar_content.bind(
            "<Configure>",
            lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        )
        
        sidebar_window = sidebar_canvas.create_window((0, 0), window=self.sidebar_content, anchor="nw", width=80)
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
        
        # Update canvas window width when canvas is resized
        def configure_sidebar_width(event):
            canvas_width = event.width
            sidebar_canvas.itemconfig(sidebar_window, width=canvas_width)
        sidebar_canvas.bind('<Configure>', configure_sidebar_width)
        
        sidebar_scrollbar.pack(side="right", fill="y")
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mouse wheel to sidebar canvas (only when hovering over sidebar)
        def on_sidebar_scroll(event):
            # Only scroll if mouse is over sidebar
            if sidebar_canvas.winfo_containing(event.x_root, event.y_root):
                sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        sidebar_canvas.bind("<MouseWheel>", on_sidebar_scroll)
        
        # Color selector label
        color_label = tk.Label(self.sidebar_content, text="Marker Color", 
                              bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 8, "bold"), wraplength=70)
        color_label.pack(pady=(10, 5))
        
        # Color selection buttons
        self.color_buttons = {}
        colors = [
            ("red", "#e74c3c", "Red"),
            ("yellow", "#f1c40f", "Yellow"),
            ("green", "#2ecc71", "Green")
        ]
        
        for color_name, color_hex, display_name in colors:
            btn_frame = tk.Frame(self.sidebar_content, bg="#2c3e50")
            btn_frame.pack(pady=4)
            
            # Color button (no label text)
            color_btn = tk.Button(btn_frame, bg=color_hex, width=6, height=1,
                                 relief="solid", bd=2, cursor="hand2",
                                 command=lambda c=color_name: self.set_marker_color(c))
            color_btn.pack()
            
            # Selection indicator (initially hidden)
            indicator = tk.Frame(btn_frame, bg="#ecf0f1", height=2)
            indicator.pack(fill=tk.X, pady=(2, 0))
            indicator.pack_forget()
            
            self.color_buttons[color_name] = {
                'button': color_btn,
                'indicator': indicator
            }
        
        # Set default color (red) as selected
        self.set_marker_color("red")
        
        # Thickness control section
        thickness_separator = tk.Frame(self.sidebar_content, bg="#34495e", height=1)
        thickness_separator.pack(fill=tk.X, pady=(10, 8), padx=5)
        
        thickness_label = tk.Label(self.sidebar_content, text="Thickness", 
                                  bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 8, "bold"), wraplength=70)
        thickness_label.pack(pady=(0, 5))
        
        # Thickness control frame
        thickness_frame = tk.Frame(self.sidebar_content, bg="#2c3e50")
        thickness_frame.pack(pady=4, padx=5)
        
        # Thickness slider
        self.thickness_var = tk.IntVar(value=self.marker_width)
        thickness_scale = tk.Scale(thickness_frame, 
                                   from_=1, to=20, 
                                   orient=tk.HORIZONTAL,
                                   variable=self.thickness_var,
                                   bg="#2c3e50", fg="#ecf0f1",
                                   highlightthickness=0,
                                   troughcolor="#34495e",
                                   activebackground="#3498db",
                                   length=70,
                                   command=self.set_marker_thickness)
        thickness_scale.pack()
        
        # Thickness value label
        self.thickness_value_label = tk.Label(thickness_frame, 
                                             text=str(self.marker_width),
                                             bg="#2c3e50", fg="#ecf0f1", 
                                             font=("Segoe UI", 8))
        self.thickness_value_label.pack(pady=(2, 0))
        
        # Eraser section
        eraser_separator = tk.Frame(self.sidebar_content, bg="#34495e", height=1)
        eraser_separator.pack(fill=tk.X, pady=(10, 8), padx=5)
        
        eraser_label = tk.Label(self.sidebar_content, text="Eraser", 
                              bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 9, "bold"))
        eraser_label.pack(pady=(0, 5))
        
        eraser_btn_frame = tk.Frame(self.sidebar_content, bg="#2c3e50")
        eraser_btn_frame.pack(pady=4)
        
        self.eraser_button = tk.Button(eraser_btn_frame, 
                                       text="🧹", 
                                       command=self.toggle_eraser_mode, 
                                       width=6, height=1,
                                       relief="solid", bd=2, cursor="hand2",
                                       font=("Segoe UI", 14),
                                       bg="#34495e", fg="#ecf0f1",
                                       takefocus=0)
        self.eraser_button.pack()
        
        eraser_text = tk.Label(eraser_btn_frame, text="Eraser", bg="#2c3e50", 
                             fg="#ecf0f1", font=("Segoe UI", 8))
        eraser_text.pack(pady=(2, 0))
        
        # Eraser indicator (initially hidden)
        self.eraser_indicator = tk.Frame(eraser_btn_frame, bg="#ecf0f1", height=2)
        self.eraser_indicator.pack(fill=tk.X, pady=(2, 0))
        self.eraser_indicator.pack_forget()
        
        # Shape selector section
        shape_separator = tk.Frame(self.sidebar_content, bg="#34495e", height=1)
        shape_separator.pack(fill=tk.X, pady=(10, 8), padx=5)
        
        shape_label = tk.Label(self.sidebar_content, text="Shape Mark", 
                              bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 8, "bold"), wraplength=70)
        shape_label.pack(pady=(0, 5))
        
        # Shape selection buttons
        self.shape_buttons = {}
        shapes = [
            ("square", "⬜", "Square"),
            ("circle", "⭕", "Circle"),
            ("line", "─", "Line")
        ]
        
        for shape_name, shape_icon, display_name in shapes:
            btn_frame = tk.Frame(self.sidebar_content, bg="#2c3e50")
            btn_frame.pack(pady=3)
            
            # Shape button (icon only, no label)
            shape_btn = tk.Button(btn_frame, text=shape_icon, width=6, height=1,
                                 relief="solid", bd=2, cursor="hand2",
                                 font=("Segoe UI", 12),
                                 bg="#34495e", fg="#ecf0f1",
                                 command=lambda s=shape_name: self.set_shape_type(s))
            shape_btn.pack()
            
            # Selection indicator (initially hidden)
            indicator = tk.Frame(btn_frame, bg="#ecf0f1", height=2)
            indicator.pack(fill=tk.X, pady=(2, 0))
            indicator.pack_forget()
            
            self.shape_buttons[shape_name] = {
                'button': shape_btn,
                'indicator': indicator
            }
        
        # Set default to None (no shape mode)
        self.set_shape_type(None)
        
        # Erase All Button - Clear all marks and shapes for current image
        erase_separator = tk.Frame(self.sidebar_content, bg="#34495e", height=1)
        erase_separator.pack(fill=tk.X, pady=(10, 8), padx=5)
        
        erase_label = tk.Label(self.sidebar_content, text="Actions", 
                              bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 9, "bold"))
        erase_label.pack(pady=(0, 5))
        
        erase_btn_frame = tk.Frame(self.sidebar_content, bg="#2c3e50")
        erase_btn_frame.pack(pady=4)
        
        self.erase_all_button = tk.Button(erase_btn_frame, 
                                          text="Erase All", 
                                          command=self.erase_all_marks, 
                                          state=tk.DISABLED,
                                          width=8, height=1,
                                          relief="solid", bd=2, cursor="hand2",
                                          font=("Segoe UI", 8),
                                          bg="#e74c3c", fg="white",
                                          takefocus=0)
        self.erase_all_button.pack()
        
        # Image display area (Canvas for smooth panning)
        # Canvas background is set to a placeholder, will be updated by _draw_blurred_background
        self.image_canvas = tk.Canvas(self.main_content, bg="#34495e", highlightthickness=0) 
        self.image_canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # --- Canvas Bindings for Interaction (Centralized) ---
        self.image_canvas.bind("<Double-Button-1>", lambda e: self.toggle_selection()) 
        self.image_canvas.bind("<MouseWheel>", self.on_mouse_scroll)                  
        self.image_canvas.bind("<Button-4>", self.on_mouse_scroll)                   
        self.image_canvas.bind("<Button-5>", self.on_mouse_scroll)                   
        
        # Centralized Mouse Handlers
        self.image_canvas.bind("<ButtonPress-1>", self.on_click_press)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_motion)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_click_release)

        # --- Spacebar Bindings (Canvas-Specific) ---
        self.image_canvas.bind("<space>", self.key_press_handler)
        self.image_canvas.bind("<KeyRelease-space>", self.key_release_handler)
        
        # Initial call to draw blurred background
        self.root.after_idle(self._draw_blurred_background)
        
        # Status Label at the bottom of the window
        status_frame = tk.Frame(self.root, bg="#34495e", height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = ttk.Label(status_frame, text="Select a directory to start.", style="TLabel")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Control buttons frame below status bar
        control_frame = ttk.Frame(self.root, padding="5 5 5 5", style="TFrame")
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Navigation Buttons
        self.prev_button = ttk.Button(control_frame, text="← Prev", command=self.prev_image, state=tk.DISABLED, style="TButton", takefocus=0)
        self.prev_button.pack(side=tk.LEFT, padx=3)

        self.next_button = ttk.Button(control_frame, text="Next →", command=self.next_image, state=tk.DISABLED, style="TButton", takefocus=0)
        self.next_button.pack(side=tk.LEFT, padx=3)
        
        # Marker Toggle Button
        self.marker_button = ttk.Button(control_frame, 
                                        text="Marker (Off)", 
                                        command=self.toggle_marker_mode, 
                                        style="Marker.Off.TButton", 
                                        takefocus=0)
        self.marker_button.pack(side=tk.LEFT, padx=10)
        
        # Save Button
        self.save_button = ttk.Button(control_frame, 
                                      text="Save (0)", 
                                      command=self.save_marked_files, 
                                      state=tk.DISABLED, 
                                      style="Save.Disabled.TButton", 
                                      takefocus=0)
        self.save_button.pack(side=tk.LEFT, padx=10)
        
        # Copy Button
        self.copy_button = ttk.Button(control_frame, text="Copy (0)", command=self.copy_selected_files, state=tk.DISABLED, style="TButton", takefocus=0)
        self.copy_button.pack(side=tk.LEFT, padx=10)
        
        # Zoom Buttons with icons
        self.zoom_in_button = ttk.Button(control_frame, text="+", command=self.zoom_in, style="Icon.TButton", takefocus=0)
        self.zoom_in_button.pack(side=tk.LEFT, padx=10)
        
        self.zoom_out_button = ttk.Button(control_frame, text="−", command=self.zoom_out, style="Icon.TButton", takefocus=0)
        self.zoom_out_button.pack(side=tk.LEFT, padx=3)
        
        # Rotation Buttons
        self.rotate_left_button = ttk.Button(control_frame, text="↺", command=self.rotate_left, style="Icon.TButton", takefocus=0)
        self.rotate_left_button.pack(side=tk.LEFT, padx=10)
        
        self.rotate_right_button = ttk.Button(control_frame, text="↻", command=self.rotate_right, style="Icon.TButton", takefocus=0)
        self.rotate_right_button.pack(side=tk.LEFT, padx=3)
        
        # Load Button (Far Right)
        self.load_button = ttk.Button(control_frame, text="Load Folder", command=self.load_directory, style="TButton", takefocus=0)
        self.load_button.pack(side=tk.RIGHT, padx=5)
        
        # Gallery/Thumbnail view frame (between controls and status bar)
        gallery_container = tk.Frame(self.root, bg="#2c3e50", height=110)
        gallery_container.pack(side=tk.BOTTOM, fill=tk.X, before=status_frame)
        gallery_container.pack_propagate(False)
        
        # Scrollable canvas for thumbnails - draw directly on canvas, no Frame widgets
        self.gallery_canvas = tk.Canvas(gallery_container, bg="#2c3e50", height=110, highlightthickness=0)
        gallery_scrollbar = tk.Scrollbar(gallery_container, orient="horizontal", command=self.gallery_canvas.xview)
        self.gallery_canvas.configure(xscrollcommand=gallery_scrollbar.set)
        
        gallery_scrollbar.pack(side="bottom", fill="x")
        self.gallery_canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mouse wheel to gallery canvas
        def on_gallery_scroll(event):
            if self.gallery_canvas.winfo_containing(event.x_root, event.y_root):
                self.gallery_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        self.gallery_canvas.bind("<MouseWheel>", on_gallery_scroll)
        
        # Bind click events to canvas for thumbnail navigation
        def on_gallery_click(event):
            if not self.image_files:
                return
            # Calculate which thumbnail was clicked based on x coordinate
            # Account for canvas scrolling
            canvas_x = self.gallery_canvas.canvasx(event.x)
            # Each thumbnail slot is exactly thumbnail_spacing wide
            # Slot 0 starts at 0, slot 1 at thumbnail_spacing, etc.
            # So we can simply divide by spacing to get the slot index
            thumbnail_index = int(canvas_x / self.thumbnail_spacing)
            # Clamp to valid range
            thumbnail_index = max(0, min(thumbnail_index, len(self.image_files) - 1))
            if 0 <= thumbnail_index < len(self.image_files):
                self.navigate_to_image(thumbnail_index)
        self.gallery_canvas.bind("<Button-1>", on_gallery_click)
        self.gallery_canvas.config(cursor="hand2")


    def _set_marker_button_color(self, active):
        """Switches the style and text of the marker button based on state."""
        if active:
            # Change style to Red (On)
            self.marker_button.config(style="Marker.On.TButton", text="Marker (ON)")
        else:
            # Change style to Gray (Off)
            self.marker_button.config(style="Marker.Off.TButton", text="Marker (Off)")
            
    def _set_save_button_color(self, enabled):
        """Switches the style of the save button based on state."""
        if enabled:
            # Change style to Green (Enabled)
            self.save_button.config(style="Save.Enabled.TButton")
        else:
            # Change style to Blue (Disabled)
            self.save_button.config(style="Save.Disabled.TButton")
    
    def set_marker_thickness(self, value=None):
        """Sets the marker/shape thickness."""
        if value is None:
            value = self.thickness_var.get()
        else:
            # Scale widget passes value as string
            value = int(float(value))
        self.marker_width = value
        # Update the value label
        if hasattr(self, 'thickness_value_label'):
            self.thickness_value_label.config(text=str(value))
    
    def set_marker_color(self, color_name):
        """Sets the marker color and updates the UI."""
        self.marker_color = color_name
        
        # Update all color buttons to show selection
        for name, widgets in self.color_buttons.items():
            if name == color_name:
                # Show selection indicator
                widgets['indicator'].pack(fill=tk.X, pady=(3, 0))
                widgets['button'].config(relief="sunken", bd=3)
            else:
                # Hide selection indicator
                widgets['indicator'].pack_forget()
                widgets['button'].config(relief="solid", bd=2)
    
    def set_shape_type(self, shape_type):
        """Sets the shape type for shape marking mode. Toggles off if same shape is clicked again."""
        # Toggle: if clicking the same shape that's already selected, deselect it
        if shape_type == self.current_shape_type:
            shape_type = None
        
        self.current_shape_type = shape_type
        self.shape_mode_active = (shape_type is not None)
        
        # Disable eraser when shape mode is active
        if self.shape_mode_active:
            self.eraser_mode_active = False
            self._update_eraser_button_state()
        
        # Update all shape buttons to show selection
        for name, widgets in self.shape_buttons.items():
            if name == shape_type:
                # Show selection indicator
                widgets['indicator'].pack(fill=tk.X, pady=(3, 0))
                widgets['button'].config(relief="sunken", bd=3, bg="#3498db")
            else:
                # Hide selection indicator
                widgets['indicator'].pack_forget()
                widgets['button'].config(relief="solid", bd=2, bg="#34495e")
        
        # Clear any ongoing shape drawing
        if self.current_shape_item:
            self.image_canvas.delete(self.current_shape_item)
            self.current_shape_item = None
        self.shape_start_coord = None
    
    def toggle_eraser_mode(self):
        """Toggles the eraser mode."""
        self.eraser_mode_active = not self.eraser_mode_active
        
        # Disable shape mode when eraser is active
        if self.eraser_mode_active:
            self.shape_mode_active = False
            self.current_shape_type = None
            # Update shape buttons
            for name, widgets in self.shape_buttons.items():
                widgets['indicator'].pack_forget()
                widgets['button'].config(relief="solid", bd=2, bg="#34495e")
        
        self._update_eraser_button_state()
    
    def _update_eraser_button_state(self):
        """Updates the eraser button visual state."""
        if self.eraser_mode_active:
            self.eraser_button.config(relief="sunken", bd=3, bg="#3498db")
            self.eraser_indicator.pack(fill=tk.X, pady=(3, 0))
        else:
            self.eraser_button.config(relief="solid", bd=2, bg="#34495e")
            self.eraser_indicator.pack_forget()
    
    def _erase_at_point(self, x, y):
        """Erases marks or shapes near the clicked point."""
        if self.current_index == -1 or not self.image_files:
            return
        
        current_file = self.image_files[self.current_index]
        erased = False
        
        # Check for shapes first (they're larger and easier to click)
        if current_file in self.shapes_cache:
            shapes = self.shapes_cache[current_file]
            image_coords = self.image_canvas.coords(self.image_item)
            if image_coords:
                disp_w = self.current_photo.width()
                disp_h = self.current_photo.height()
                img_x0 = image_coords[0] - disp_w / 2
                img_y0 = image_coords[1] - disp_h / 2
                
                # Check each shape to see if click is inside it
                for i, shape in enumerate(shapes[:]):  # Use slice to avoid modification during iteration
                    if shape['rotation'] == self.current_rotation:
                        norm_x1, norm_y1, norm_x2, norm_y2 = shape['coords']
                        x1 = img_x0 + norm_x1 * disp_w
                        y1 = img_y0 + norm_y1 * disp_h
                        x2 = img_x0 + norm_x2 * disp_w
                        y2 = img_y0 + norm_y2 * disp_h
                        
                        # Check if point is inside shape bounds
                        min_x, max_x = min(x1, x2), max(x1, x2)
                        min_y, max_y = min(y1, y2), max(y1, y2)
                        
                        if min_x <= x <= max_x and min_y <= y <= max_y:
                            # Remove shape
                            shapes.remove(shape)
                            erased = True
                            break
        
        # Check for marks (lines) - find closest mark
        if not erased and current_file in self.marks_cache:
            marks = self.marks_cache[current_file]
            image_coords = self.image_canvas.coords(self.image_item)
            if image_coords:
                disp_w = self.current_photo.width()
                disp_h = self.current_photo.height()
                img_x0 = image_coords[0] - disp_w / 2
                img_y0 = image_coords[1] - disp_h / 2
                
                closest_mark = None
                min_distance = 20  # Maximum distance to erase (20 pixels)
                
                for mark in marks[:]:
                    if mark['rotation'] == self.current_rotation:
                        # Convert normalized coords to canvas coords
                        start_x = img_x0 + mark['start'][0] * disp_w
                        start_y = img_y0 + mark['start'][1] * disp_h
                        end_x = img_x0 + mark['end'][0] * disp_w
                        end_y = img_y0 + mark['end'][1] * disp_h
                        
                        # Calculate distance from point to line segment
                        # Using point-to-line distance formula
                        A = end_y - start_y
                        B = start_x - end_x
                        C = end_x * start_y - start_x * end_y
                        distance = abs(A * x + B * y + C) / ((A**2 + B**2)**0.5) if (A**2 + B**2) > 0 else float('inf')
                        
                        # Also check if point is within the line segment bounds
                        if min(start_x, end_x) <= x <= max(start_x, end_x) or min(start_y, end_y) <= y <= max(start_y, end_y):
                            if distance < min_distance:
                                min_distance = distance
                                closest_mark = mark
                
                if closest_mark:
                    marks.remove(closest_mark)
                    erased = True
        
        if erased:
            # Redraw marks and shapes
            self._draw_all_marks()
            self._draw_all_shapes()
            self.update_navigation_state()
            self.update_status()

    # --- NEW: Mouse Scroll Handler ---

    def on_mouse_scroll(self, event):
        """Handles mouse wheel scrolling for zoom in/out with fast, smooth zooming."""
        if self.current_pil_img is None:
            return

        # Get mouse position relative to canvas
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)
        
        # Determine zoom direction and amount - MUCH FASTER increments
        # Windows/Mac typically use event.delta (e.g., 120 or -120)
        # Linux (X11) often uses event.num (4 for up, 5 for down)
        
        zoom_delta = 0
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # Scroll Up (Zoom In) - use larger increments for faster zoom
            if hasattr(event, 'delta'):
                # Proportional zoom: larger scroll = more zoom (increased multiplier)
                zoom_delta = min(event.delta / 120.0 * 0.25, 0.5)  # Increased from 0.15/0.3 to 0.25/0.5
            else:
                zoom_delta = 0.25  # Increased from 0.15
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # Scroll Down (Zoom Out)
            if hasattr(event, 'delta'):
                zoom_delta = max(event.delta / 120.0 * 0.25, -0.5)  # Increased from -0.15/-0.3 to -0.25/-0.5
            else:
                zoom_delta = -0.25  # Increased from -0.15
        
        if zoom_delta == 0:
            return
        
        # Calculate new zoom factor
        old_zoom = self.zoom_factor
        new_zoom = max(1.0, min(5.0, self.zoom_factor + zoom_delta))
        
        if new_zoom == old_zoom:
            return
        
        # Mark zoom as active for fast preview mode
        self.zoom_active = True
        
        # Cancel any pending zoom update
        if self.zoom_update_id:
            self.root.after_cancel(self.zoom_update_id)
        
        # Immediate zoom update with fast preview
        self._zoom_towards_point_fast(canvas_x, canvas_y, old_zoom, new_zoom)
        
        # Schedule high-quality update after zoom stops (debouncing)
        self.zoom_update_id = self.root.after(150, self._finalize_zoom_quality)
            
    # --- Marker Mode Logic ---
    
    def toggle_marker_mode(self):
        """Toggles the marker drawing mode."""
        self.marker_mode_active = not self.marker_mode_active
        
        self._set_marker_button_color(self.marker_mode_active)
        
        # Show/hide the color sidebar based on marker mode
        if self.marker_mode_active:
            self.image_canvas.focus_set() # Ensure canvas has focus when marker mode is on
            # Show the color and shape selector sidebar by setting width
            self.color_sidebar.config(width=80)
            # Force update to ensure it's visible
            self.root.update_idletasks()
        else:
            # Hide the color and shape selector sidebar by setting width to 0
            self.color_sidebar.config(width=0)
            # Force update
            self.root.update_idletasks()
        
        # Clear the last mark coordinates to prevent rogue lines
        self.last_mark_coord = None
        
    def key_press_handler(self, event):
        """
        Handles key press events, specifically for Spacebar.
        Spacebar now ONLY sets the held state for marking.
        """
        if event.keysym == 'space':
            self.spacebar_held = True

    def key_release_handler(self, event):
        """Handles key release events, specifically for Spacebar."""
        if event.keysym == 'space':
            self.spacebar_held = False
            self.last_mark_coord = None # End the current drawing stroke
            
    # --- Centralized Mouse Handlers ---

    def on_click_press(self, event):
        """Handles the start of a mouse click (pan, mark, shape, or eraser)."""
        if self.current_pil_img is None: return

        # Check if eraser mode is active
        if self.eraser_mode_active:
            self._erase_at_point(event.x, event.y)
            return

        # Check if shape mode is active
        if self.shape_mode_active and self.current_shape_type:
            # Start drawing a shape
            self.shape_start_coord = (event.x, event.y)
            self.current_shape_item = None
            return

        # Check if marker mode is active AND spacebar is held
        if self.marker_mode_active and self.spacebar_held:
            # Start Marking: Marker ON + Spacebar + Left Click
            self.last_mark_coord = (event.x, event.y)
            
            # NEW: Automatically select the photo when marking starts
            current_file = self.image_files[self.current_index]
            if current_file not in self.selected_files:
                self.selected_files.add(current_file)
                self.update_status()
                self.update_navigation_state()
                self._draw_selection_border()

        elif self.zoom_factor > 1.0:
            # Start Panning: Left Click Drag (only when zoomed)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def on_mouse_motion(self, event):
        """Handles mouse motion (mark, pan, or shape drawing)."""
        if self.current_pil_img is None: return

        # Check if drawing a shape
        if self.shape_mode_active and self.shape_start_coord:
            self._draw_shape_preview(event.x, event.y)
            return

        # Ensure marking only happens if mode is active AND space is held
        if self.marker_mode_active and self.spacebar_held and self.last_mark_coord:
            # Drawing a Mark
            self._do_mark(event.x, event.y)
        elif self.zoom_factor > 1.0:
            # Panning
            self._do_pan_motion(event.x, event.y)

    def on_click_release(self, event):
        """Handles the end of a mouse click (mark, pan, or shape)."""
        if self.current_pil_img is None: return
        
        # Finalize shape drawing
        if self.shape_mode_active and self.shape_start_coord:
            self._finalize_shape(event.x, event.y)
            self.shape_start_coord = None
            return
        
        self.last_mark_coord = None 
        # Only call clamping if the item exists (prevents crash on initial load)
        if self.image_item:
            self._center_and_clamp_image() 

    def _draw_shape_preview(self, current_x, current_y):
        """Draws a preview of the shape while dragging."""
        if not self.shape_start_coord or not self.current_shape_type:
            return
        
        # Delete previous preview
        if self.current_shape_item:
            self.image_canvas.delete(self.current_shape_item)
        
        x1, y1 = self.shape_start_coord
        x2, y2 = current_x, current_y
        
        # Draw shape based on type
        if self.current_shape_type == "square":
            # Rectangle/square
            self.current_shape_item = self.image_canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.marker_color, width=self.marker_width,
                tags="shape_preview"
            )
        elif self.current_shape_type == "circle":
            # Circle/ellipse
            self.current_shape_item = self.image_canvas.create_oval(
                x1, y1, x2, y2,
                outline=self.marker_color, width=self.marker_width,
                tags="shape_preview"
            )
        elif self.current_shape_type == "line":
            # Line tool - draw a straight line from start to end point
            self.current_shape_item = self.image_canvas.create_line(
                x1, y1, x2, y2,
                fill=self.marker_color, width=self.marker_width,
                tags="shape_preview"
            )
    
    def _finalize_shape(self, end_x, end_y):
        """Finalizes the shape and saves it to the cache."""
        if not self.shape_start_coord or not self.current_shape_type:
            return
        
        # Get image coordinates for normalization
        image_coords = self.image_canvas.coords(self.image_item)
        if not image_coords:
            return
        
        disp_w = self.current_photo.width()
        disp_h = self.current_photo.height()
        img_x0 = image_coords[0] - disp_w / 2
        img_y0 = image_coords[1] - disp_h / 2
        
        # Normalize coordinates
        x1, y1 = self.shape_start_coord
        x2, y2 = end_x, end_y
        
        # Convert to image-relative coordinates
        norm_x1 = (x1 - img_x0) / disp_w
        norm_y1 = (y1 - img_y0) / disp_h
        norm_x2 = (x2 - img_x0) / disp_w
        norm_y2 = (y2 - img_y0) / disp_h
        
        # Store shape
        file_path = self.image_files[self.current_index]
        if file_path not in self.shapes_cache:
            self.shapes_cache[file_path] = []
        
        self.shapes_cache[file_path].append({
            'type': self.current_shape_type,
            'coords': (norm_x1, norm_y1, norm_x2, norm_y2),
            'color': self.marker_color,
            'width': self.marker_width,
            'rotation': self.current_rotation
        })
        
        # Delete preview and redraw permanent shape
        if self.current_shape_item:
            self.image_canvas.delete(self.current_shape_item)
            self.current_shape_item = None
        
        # Redraw all shapes
        self._draw_all_shapes()
        
        # Automatically select the photo
        if file_path not in self.selected_files:
            self.selected_files.add(file_path)
            self.update_status()
            self.update_navigation_state()
            self._draw_selection_border()
    
    def _draw_all_shapes(self):
        """Redraws all stored shapes for the current image."""
        self.image_canvas.delete("shape")
        
        file_path = self.image_files[self.current_index]
        if file_path not in self.shapes_cache:
            return
        
        shapes = self.shapes_cache[file_path]
        
        image_coords = self.image_canvas.coords(self.image_item)
        if not image_coords:
            return
        
        disp_w = self.current_photo.width()
        disp_h = self.current_photo.height()
        img_x0 = image_coords[0] - disp_w / 2
        img_y0 = image_coords[1] - disp_h / 2
        
        for shape in shapes:
            if shape['rotation'] == self.current_rotation:
                # Convert normalized coords back to canvas coords
                norm_x1, norm_y1, norm_x2, norm_y2 = shape['coords']
                x1 = img_x0 + norm_x1 * disp_w
                y1 = img_y0 + norm_y1 * disp_h
                x2 = img_x0 + norm_x2 * disp_w
                y2 = img_y0 + norm_y2 * disp_h
                
                color = shape.get('color', self.marker_color)
                width = shape.get('width', self.marker_width)
                shape_type = shape['type']
                
                if shape_type == "square":
                    self.image_canvas.create_rectangle(
                        x1, y1, x2, y2,
                        outline=color, width=width,
                        tags="shape"
                    )
                elif shape_type == "circle":
                    self.image_canvas.create_oval(
                        x1, y1, x2, y2,
                        outline=color, width=width,
                        tags="shape"
                    )
                elif shape_type == "line":
                    # Line tool - draw a straight line
                    self.image_canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=width,
                        tags="shape"
                    )

    def _do_mark(self, current_x, current_y):
        """Draws a line segment and saves the mark relative to the image."""
        if not self.last_mark_coord: return
        
        self.image_canvas.create_line(
            self.last_mark_coord[0], self.last_mark_coord[1], 
            current_x, current_y,
            fill=self.marker_color, width=self.marker_width, 
            tags="mark"
        )
        
        image_coords = self.image_canvas.coords(self.image_item)
        if not image_coords: return # <-- SAFETY CHECK ADDED
        
        disp_w = self.current_photo.width()
        disp_h = self.current_photo.height()
        
        # Use safe coordinates from image_coords list
        img_x0 = image_coords[0] - disp_w / 2 
        img_y0 = image_coords[1] - disp_h / 2

        # Normalize coordinates
        norm_start = ( (self.last_mark_coord[0] - img_x0) / disp_w, (self.last_mark_coord[1] - img_y0) / disp_h )
        norm_end = ( (current_x - img_x0) / disp_w, (current_y - img_y0) / disp_h )
        
        file_path = self.image_files[self.current_index]
        if file_path not in self.marks_cache:
            self.marks_cache[file_path] = []

        self.marks_cache[file_path].append({
            'start': norm_start,
            'end': norm_end,
            'rotation': self.current_rotation,
            'color': self.marker_color  # Store color with each mark
        })

        self.last_mark_coord = (current_x, current_y)

    def _draw_all_marks(self):
        """Redraws all stored marks for the current image."""
        self.image_canvas.delete("mark") 
        
        file_path = self.image_files[self.current_index]
        if file_path not in self.marks_cache:
            return

        marks = self.marks_cache[file_path]
        
        image_coords = self.image_canvas.coords(self.image_item)
        if not image_coords: return # <-- SAFETY CHECK ADDED

        disp_w = self.current_photo.width()
        disp_h = self.current_photo.height()
        img_x0 = image_coords[0] - disp_w / 2
        img_y0 = image_coords[1] - disp_h / 2
        
        for mark in marks:
            if mark['rotation'] == self.current_rotation:
                # Get color from mark (default to red for old marks without color)
                mark_color = mark.get('color', 'red')
                
                # Convert normalized (0.0 to 1.0) coords back to canvas pixel coords
                start_x = img_x0 + mark['start'][0] * disp_w
                start_y = img_y0 + mark['start'][1] * disp_h
                end_x = img_x0 + mark['end'][0] * disp_w
                end_y = img_y0 + mark['end'][1] * disp_h
                
                self.image_canvas.create_line(
                    start_x, start_y, 
                    end_x, end_y,
                    fill=mark_color, width=self.marker_width, 
                    tags="mark"
                )

    # --- Zoom Methods ---

    def _zoom_towards_point_fast(self, canvas_x, canvas_y, old_zoom, new_zoom):
        """
        Fast zoom update using lower quality resampling for responsiveness.
        """
        if not self.current_pil_img:
            return
        
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:
            self.zoom_factor = new_zoom
            self.update_image_display_fast(self.current_index)
            return
        
        # Get current image position
        if self.image_item:
            image_coords = self.image_canvas.coords(self.image_item)
            if image_coords:
                current_x, current_y = image_coords[0], image_coords[1]
            else:
                current_x, current_y = canvas_w // 2, canvas_h // 2
        else:
            current_x, current_y = canvas_w // 2, canvas_h // 2
        
        # Calculate relative position
        rel_x = canvas_x - current_x
        rel_y = canvas_y - current_y
        
        # Update zoom factor
        self.zoom_factor = new_zoom
        
        # Calculate zoom ratio
        zoom_ratio = new_zoom / old_zoom if old_zoom > 0 else 1.0
        
        # Adjust offset
        self.image_offset_x = (self.image_offset_x + rel_x) * zoom_ratio - rel_x
        self.image_offset_y = (self.image_offset_y + rel_y) * zoom_ratio - rel_y
        
        # Fast update with lower quality
        self.update_image_display_fast(self.current_index)
    
    def _finalize_zoom_quality(self):
        """Finalizes zoom with high quality after user stops zooming."""
        self.zoom_active = False
        if self.current_pil_img:
            self.update_image_display(self.current_index)

    def _zoom_towards_point(self, canvas_x, canvas_y, old_zoom, new_zoom):
        """
        Zooms towards a specific point on the canvas (typically the mouse cursor).
        This makes zooming feel more natural and intuitive.
        """
        if not self.current_pil_img:
            return
        
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:
            # Canvas not ready yet
            self.zoom_factor = new_zoom
            self.update_image_display(self.current_index)
            return
        
        # Get current image position and size
        if self.image_item:
            image_coords = self.image_canvas.coords(self.image_item)
            if image_coords:
                current_x, current_y = image_coords[0], image_coords[1]
            else:
                current_x, current_y = canvas_w // 2, canvas_h // 2
        else:
            current_x, current_y = canvas_w // 2, canvas_h // 2
        
        # Calculate the point on the image that's under the cursor
        # Relative to image center
        rel_x = canvas_x - current_x
        rel_y = canvas_y - current_y
        
        # Update zoom factor
        self.zoom_factor = new_zoom
        
        # Calculate how the image size changes
        zoom_ratio = new_zoom / old_zoom if old_zoom > 0 else 1.0
        
        # Adjust offset to keep the point under cursor in the same place
        # When zooming in, we need to move the image so the cursor point stays fixed
        self.image_offset_x = (self.image_offset_x + rel_x) * zoom_ratio - rel_x
        self.image_offset_y = (self.image_offset_y + rel_y) * zoom_ratio - rel_y
        
        # Update the display
        self.update_image_display(self.current_index)

    # --- Panning Methods ---

    def _do_pan_motion(self, current_x, current_y):
        """Calculates and applies the offset during a drag motion."""
        dx = current_x - self.pan_start_x
        dy = current_y - self.pan_start_y
        
        self.image_offset_x += dx
        self.image_offset_y += dy
        
        self.pan_start_x = current_x
        self.pan_start_y = current_y
        
        self._center_and_clamp_image()

    def _center_and_clamp_image(self):
        """Ensures the image is moved within the bounds of the canvas and updates position."""
        if not self.image_item or not self.current_pil_img: return
        if not self.current_photo: return
        
        display_w = self.current_photo.width()
        display_h = self.current_photo.height()

        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        max_x = max(0, (display_w - canvas_w) / 2)
        max_y = max(0, (display_h - canvas_h) / 2)
        
        self.image_offset_x = max(-max_x, min(max_x, self.image_offset_x))
        self.image_offset_y = max(-max_y, min(max_y, self.image_offset_y))

        x_center = canvas_w // 2 + self.image_offset_x
        y_center = canvas_h // 2 + self.image_offset_y
        
        self.image_canvas.coords(self.image_item, x_center, y_center)
        
        self._draw_selection_border()
        self._draw_all_marks() # Redraw marks to follow the pan/zoom
        self._draw_all_shapes() # Redraw shapes to follow the pan/zoom

    # --- Rotation Methods (Now Permanent) ---

    def _save_rotation(self, angle):
        """
        Rotates the underlying file permanently by the given angle.
        Called by rotate_right and rotate_left.
        """
        if self.current_index == -1 or not self.image_files: return

        file_path = self.image_files[self.current_index]
        self.status_label.config(text=f"Saving rotation to {os.path.basename(file_path)}...", foreground="#f39c12")
        self.root.update() 
        
        try:
            # 1. Load original image
            original_img = Image.open(file_path)
            original_format = original_img.format
            
            # 2. Rotate image
            rotated_img = original_img.rotate(angle, expand=True, resample=Image.Resampling.LANCZOS)
            
            # 3. Save, overwriting the original file, using the original format
            # Save must be done with the rotation angle as 0, as the file is now rotated.
            rotated_img.save(file_path, format=original_format)
            
            # 4. Invalidate the cache for this image
            if self.current_index in self.cache:
                del self.cache[self.current_index]
            
            # 5. Reset local state and redraw
            self.current_rotation = 0 # Rotation is now saved to the file
            self.image_offset_x = 0
            self.image_offset_y = 0
            
            # Force a re-load and display of the permanently rotated file
            self.update_image_display(self.current_index) 
            self.status_label.config(text=f"Successfully rotated and saved {os.path.basename(file_path)}.", foreground="#2ecc71")
            
        except Exception as e:
            print(f"Error saving rotation for {file_path}: {e}")
            self.status_label.config(text=f"Error saving rotation: {e}", foreground="#e74c3c")


    def rotate_right(self):
        """Rotates the image 90 degrees clockwise (right) and saves permanently."""
        if not self.current_pil_img: return
        self._save_rotation(angle=-90) # -90 is clockwise

    def rotate_left(self):
        """Rotates the image 90 degrees counter-clockwise (left) and saves permanently."""
        if not self.current_pil_img: return
        self._save_rotation(angle=90) # 90 is counter-clockwise
        
    # --- File/Image Loading Methods ---

    def load_directory(self):
        """Opens a file dialog to select a directory and loads image files."""
        directory = filedialog.askdirectory()
        if directory:
            self.image_files = self._get_image_files(directory)
            self.current_index = 0
            self.cache = {} 
            self.current_pil_img = None
            self.zoom_factor = 1.0
            self.image_offset_x = 0
            self.image_offset_y = 0
            self.current_rotation = 0 
            self.selected_files.clear() 
            self.marks_cache.clear() # Clear marks cache on new directory load
            self.shapes_cache.clear() # Clear shapes cache on new directory load
            
            if self.image_files:
                # Clear thumbnail cache and order
                self.thumbnail_cache.clear()
                self.thumbnail_cache_order.clear()
                self.thumbnails_loaded_range = (0, 0)
                self.last_gallery_selection_index = -1
                
                # Find the first valid image (skip corrupted ones)
                found_valid = False
                for i in range(len(self.image_files)):
                    if self.update_image_display(i, reset_zoom=True):
                        found_valid = True
                        break
                
                if not found_valid:
                    self.status_label.config(text="No valid images found in the selected directory.")
                    self.image_canvas.delete("all")
                    self.current_index = -1
                else:
                    # Update gallery view first (with placeholders)
                    self.update_gallery()
                    # Only pre-load thumbnails if folder is small (less than 1000 photos)
                    if len(self.image_files) < 1000:
                        self.preload_all_thumbnails()
                    # For large folders, thumbnails will load on-demand as user navigates
                
                self.image_canvas.focus_set() # Ensure canvas has focus
            else:
                self.status_label.config(text="No images found in the selected directory.")
                self.image_canvas.delete("all")
                self.update_navigation_state()
                self.update_status()
                # Clear gallery
                if self.gallery_canvas:
                    self.gallery_canvas.delete("all")
                    self.gallery_thumbnails.clear()

    def _get_image_files(self, directory):
        """
        Returns a sorted list of absolute paths to image files in the directory.
        Sorts by file modification time (oldest first).
        Supports: JPG, JPEG, PNG, GIF, BMP, JFIF, HEIC, HEIF (iPhone photos)
        """
        supported_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.jfif', '*.heic', '*.heif']
        files = []
        for ext in supported_extensions:
            # Check both lowercase and uppercase extensions
            files.extend(glob.glob(os.path.join(directory, ext)))
            files.extend(glob.glob(os.path.join(directory, ext.upper())))
        
        # Remove duplicates (in case both lowercase and uppercase match)
        files = list(set(files))
        
        # --- Sort by modification time (mtime) in ascending order ---
        files.sort(key=os.path.getmtime)
        return files

    def on_resize(self, event):
        """Recalculates the target size and redraws the current image."""
        if event.widget == self.image_canvas:
            self._draw_blurred_background() # Redraw background on resize
            if self.current_index != -1 and self.image_files:
                if self.zoom_factor == 1.0:
                    self.image_offset_x = 0
                    self.image_offset_y = 0
                self.update_image_display(self.current_index)
                
    def _get_original_image(self, index):
        """Loads or retrieves the original PIL Image object from cache.
        For very large images, automatically downscales to improve performance."""
        if index in self.cache:
            return self.cache[index]
            
        file_path = self.image_files[index]
        try:
            # We explicitly handle the cache clearance for new image viewing
            if len(self.cache) > self.max_cache_size:
                # Simple LRU-like cache: remove the oldest entry (lowest index key)
                oldest_index = min(self.cache.keys())
                del self.cache[oldest_index]

            img = Image.open(file_path)
            
            # Performance optimization: downscale very large images
            orig_w, orig_h = img.size
            if orig_w > self.max_image_dimension or orig_h > self.max_image_dimension:
                # Calculate scaling factor to fit within max dimension
                scale = min(self.max_image_dimension / orig_w, self.max_image_dimension / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                # Use high-quality resampling for downscaling
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to RGBA if not already to support potential transparency/drawing
            if img.mode != 'RGBA':
                img = img.convert('RGBA') 
            img.load() 
            self.cache[index] = img 
            return img
        except Exception as e:
            print(f"Error loading original image {file_path}: {e}")
            return None

    def update_image_display(self, index, reset_zoom=False):
        """
        Loads, scales the image, and draws it onto the canvas.
        This is the main function responsible for the visual update.
        Returns True if image loaded successfully, False otherwise.
        """
        # Validate index before proceeding
        if index < 0 or index >= len(self.image_files):
            return False
        
        # 1. Load the original PIL Image
        pil_image = self._get_original_image(index)
        if not pil_image:
            self.image_canvas.delete("all")
            return False

        # 2. Handle Zoom/Rotation Reset on Navigation
        if reset_zoom:
            self.zoom_factor = 1.0
            self.image_offset_x = 0 
            self.image_offset_y = 0 
            self.current_rotation = 0 
            
        # Clear only the displayed image, not the background
        if self.image_item:
            self.image_canvas.delete(self.image_item)
            self.image_item = None
        self.image_canvas.delete("mark") # Clear marks before redraw
        self.image_canvas.delete("shape") # Clear shapes before redraw
        self.image_canvas.delete("shape_preview") # Clear shape preview
        self.image_canvas.delete("selection_border") # Clear border before redraw
        
        self.current_pil_img = pil_image
        
        # 2.5 Apply rotation (OPTIMIZATION: skip if 0 to avoid expensive operation)
        if self.current_rotation == 0:
            rotated_image = pil_image  # No rotation needed
        else:
            rotated_image = pil_image.rotate(self.current_rotation, expand=True, resample=Image.Resampling.LANCZOS)

        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        # 3. Calculate target size
        orig_w, orig_h = rotated_image.size
        
        if self.zoom_factor == 1.0:
            # Fit to Window logic - OPTIMIZATION: use thumbnail directly (no copy needed)
            # Limit thumbnail size to canvas size for performance
            max_thumb_size = max(canvas_w, canvas_h) * 2  # Allow 2x for better quality
            if orig_w > max_thumb_size or orig_h > max_thumb_size:
                # Pre-scale very large images before thumbnail
                scale = min(max_thumb_size / orig_w, max_thumb_size / orig_h)
                pre_w = int(orig_w * scale)
                pre_h = int(orig_h * scale)
                img_copy = rotated_image.resize((pre_w, pre_h), Image.Resampling.LANCZOS)
                img_copy.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            else:
                # Use thumbnail directly - more efficient than copy + resize
                img_copy = rotated_image.copy() if rotated_image is not pil_image else pil_image.copy()
                img_copy.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        else:
            # Zoomed logic - limit maximum display size for performance
            display_w = int(orig_w * self.zoom_factor)
            display_h = int(orig_h * self.zoom_factor)
            
            # Limit maximum display size to prevent memory issues
            max_display_size = 6000  # Maximum pixels for display
            if display_w > max_display_size or display_h > max_display_size:
                scale = min(max_display_size / display_w, max_display_size / display_h)
                display_w = int(display_w * scale)
                display_h = int(display_h * scale)
            
            # Use appropriate resampling based on size
            if display_w > 2000 or display_h > 2000:
                # For large displays, use BILINEAR for better performance
                img_copy = rotated_image.resize((display_w, display_h), Image.Resampling.BILINEAR)
            else:
                # For smaller displays, use LANCZOS for better quality
                img_copy = rotated_image.resize((display_w, display_h), Image.Resampling.LANCZOS)

        # 4. Convert and draw onto Canvas
        photo_image = ImageTk.PhotoImage(img_copy)
        self.current_photo = photo_image
        
        x_center = canvas_w // 2 
        y_center = canvas_h // 2
        
        # 4.1 CREATE THE IMAGE ITEM *BEFORE* CALLING CLAMPING/DRAWING FUNCTIONS
        self.image_item = self.image_canvas.create_image(
            x_center, y_center, 
            image=self.current_photo, 
            anchor=tk.CENTER
        )
        self.image_canvas.tag_raise(self.image_item) # Ensure image is above background
        
        # 4.2 NOW check zoom and center/clamp the image position
        if self.zoom_factor > 1.0:
            self._center_and_clamp_image() 
        
        # 5. Update state and status bar
        # Ensure index is valid before setting current_index
        if index < 0 or index >= len(self.image_files):
            # Invalid index - don't update
            return False
        
        if self.current_index != index:
            self.current_index = index
            
        # OPTIMIZATION: Defer non-critical updates to avoid blocking image display
        # Update image first, then update UI elements
        self._draw_selection_border()
        self._draw_all_marks()
        self._draw_all_shapes()
        
        # Defer status and navigation updates (less critical, can happen after image is shown)
        self.root.after_idle(self.update_navigation_state)
        self.root.after_idle(self.update_status)
        
        # Update gallery to highlight current image (defer for performance)
        if self.gallery_canvas:
            self.root.after_idle(self.update_gallery_selection)
            
        # 6. Initiate pre-caching for the next image (only if not at last image)
        if self.current_index < len(self.image_files) - 1:
            self.root.after(50, self.pre_cache_next)
        return True

    def pre_cache_next(self):
        """Pre-loads adjacent images in background for smooth navigation."""
        # Preload next and previous images in background thread
        def load_adjacent_images():
            indices_to_load = []
            if self.current_index + 1 < len(self.image_files):
                indices_to_load.append(self.current_index + 1)
            if self.current_index - 1 >= 0:
                indices_to_load.append(self.current_index - 1)
            # Also preload 2 ahead/behind for very smooth navigation
            if self.current_index + 2 < len(self.image_files):
                indices_to_load.append(self.current_index + 2)
            if self.current_index - 2 >= 0:
                indices_to_load.append(self.current_index - 2)
            
            for idx in indices_to_load:
                if idx not in self.cache:
                    try:
                        file_path = self.image_files[idx]
                        img = Image.open(file_path)
                        
                        # Performance optimization: downscale very large images in background
                        orig_w, orig_h = img.size
                        if orig_w > self.max_image_dimension or orig_h > self.max_image_dimension:
                            scale = min(self.max_image_dimension / orig_w, self.max_image_dimension / orig_h)
                            new_w = int(orig_w * scale)
                            new_h = int(orig_h * scale)
                            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        img.load()
                        self.cache[idx] = img
                    except Exception as e:
                        pass  # Silently fail for background loading
        
        # Run in background thread
        if self.loading_thread is None or not self.loading_thread.is_alive():
            self.loading_thread = threading.Thread(target=load_adjacent_images, daemon=True)
            self.loading_thread.start()
    
    def update_image_display_fast(self, index):
        """Fast image display update using lower quality resampling for zoom responsiveness."""
        pil_image = self._get_original_image(index)
        if not pil_image:
            return
        
        # Clear image
        if self.image_item:
            self.image_canvas.delete(self.image_item)
            self.image_item = None
        
        # Apply rotation
        rotated_image = pil_image.rotate(self.current_rotation, expand=True, resample=Image.Resampling.NEAREST)
        
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        orig_w, orig_h = rotated_image.size
        
        if self.zoom_factor == 1.0:
            img_copy = rotated_image.copy()
            img_copy.thumbnail((canvas_w, canvas_h), Image.Resampling.NEAREST)  # Fast NEAREST
        else:
            display_w = int(orig_w * self.zoom_factor)
            display_h = int(orig_h * self.zoom_factor)
            # Use NEAREST for speed during zoom
            img_copy = rotated_image.resize((display_w, display_h), Image.Resampling.NEAREST)
        
        # Convert and draw
        photo_image = ImageTk.PhotoImage(img_copy)
        self.current_photo = photo_image
        
        x_center = canvas_w // 2
        y_center = canvas_h // 2
        
        self.image_item = self.image_canvas.create_image(
            x_center, y_center,
            image=self.current_photo,
            anchor=tk.CENTER
        )
        
        if self.zoom_factor > 1.0:
            self._center_and_clamp_image()

    def zoom_in(self):
        """Increases the zoom factor by a smaller increment for smoother zoom."""
        if not self.current_pil_img: return
        old_zoom = self.zoom_factor
        new_zoom = min(self.zoom_factor + 0.1, 5.0)
        
        if new_zoom != old_zoom:
            # Zoom towards center when using button
            canvas_w = self.image_canvas.winfo_width()
            canvas_h = self.image_canvas.winfo_height()
            self._zoom_towards_point(canvas_w // 2, canvas_h // 2, old_zoom, new_zoom)

    def zoom_out(self):
        """Decreases the zoom factor by a smaller increment. Minimum zoom is 1.0 (fit to window)."""
        if not self.current_pil_img: return
        old_zoom = self.zoom_factor
        new_zoom = max(self.zoom_factor - 0.1, 1.0)
        
        if new_zoom != old_zoom:
            # Zoom towards center when using button
            canvas_w = self.image_canvas.winfo_width()
            canvas_h = self.image_canvas.winfo_height()
            self._zoom_towards_point(canvas_w // 2, canvas_h // 2, old_zoom, new_zoom)
            
            if new_zoom == 1.0:
                self.image_offset_x = 0
                self.image_offset_y = 0
            
    def next_image(self):
        """Moves to and displays the next image, resetting zoom, pan, and rotation.
        Automatically skips corrupted images and continues to the next valid one.
        Stops at the last valid image."""
        if not self.image_files or self.current_index >= len(self.image_files) - 1:
            return
        
        # Try to find the next valid image
        start_index = self.current_index + 1
        max_attempts = len(self.image_files) - start_index
        attempts = 0
        
        while attempts < max_attempts:
            next_index = start_index + attempts
            # Strict bounds check - don't go beyond the last image
            if next_index >= len(self.image_files):
                break
            # Try to load the image
            if self.update_image_display(next_index, reset_zoom=True):
                # Successfully loaded, preload next images for smooth navigation
                self.pre_cache_next()
                # Load thumbnails around current position if needed
                self.load_thumbnails_around_index(next_index)
                return
            attempts += 1
            
    def go_to_first_image(self):
        """Navigates to the first image in the gallery (Home key)."""
        if not self.image_files or len(self.image_files) == 0:
            return
        self.navigate_to_image(0)
    
    def go_to_last_image(self):
        """Navigates to the last image in the gallery (End key)."""
        if not self.image_files or len(self.image_files) == 0:
            return
        last_index = len(self.image_files) - 1
        self.navigate_to_image(last_index)
    
    def delete_current_image(self):
        """Deletes the current image file (D key)."""
        if self.current_index == -1 or not self.image_files or len(self.image_files) == 0:
            return
        
        current_file = self.image_files[self.current_index]
        
        try:
            # Delete the file from disk
            if os.path.exists(current_file):
                os.remove(current_file)
            
            # Remove from selected files if it was selected
            if current_file in self.selected_files:
                self.selected_files.remove(current_file)
            
            # Clean up caches
            if current_file in self.marks_cache:
                del self.marks_cache[current_file]
            if current_file in self.shapes_cache:
                del self.shapes_cache[current_file]
            
            # Remove thumbnail from cache and gallery if it exists
            if self.current_index in self.thumbnail_cache:
                del self.thumbnail_cache[self.current_index]
            if self.current_index in self.thumbnail_cache_order:
                self.thumbnail_cache_order.remove(self.current_index)
            if self.current_index in self.gallery_thumbnails:
                # Delete the canvas item
                thumbnail_data = self.gallery_thumbnails[self.current_index]
                if 'image_id' in thumbnail_data and self.gallery_canvas:
                    self.gallery_canvas.delete(thumbnail_data['image_id'])
                del self.gallery_thumbnails[self.current_index]
            
            # Remove from image_files list
            deleted_index = self.current_index
            del self.image_files[self.current_index]
            
            # Update thumbnail cache indices (shift all indices after deleted one down by 1)
            # Items before deleted_index keep their indices, items after need to shift down by 1
            new_thumbnail_cache = {}
            new_thumbnail_cache_order = []
            new_gallery_thumbnails = {}
            
            # Process existing cache items
            for old_idx in list(self.thumbnail_cache.keys()):
                if old_idx < deleted_index:
                    # Keep same index (before deleted position)
                    new_thumbnail_cache[old_idx] = self.thumbnail_cache[old_idx]
                    if old_idx in self.thumbnail_cache_order:
                        new_thumbnail_cache_order.append(old_idx)
                    if old_idx in self.gallery_thumbnails:
                        new_gallery_thumbnails[old_idx] = self.gallery_thumbnails[old_idx]
                elif old_idx > deleted_index:
                    # Shift down by 1 (after deleted position)
                    new_idx = old_idx - 1
                    new_thumbnail_cache[new_idx] = self.thumbnail_cache[old_idx]
                    if old_idx in self.thumbnail_cache_order:
                        new_thumbnail_cache_order.append(new_idx)
                    if old_idx in self.gallery_thumbnails:
                        new_gallery_thumbnails[new_idx] = self.gallery_thumbnails[old_idx]
            
            self.thumbnail_cache = new_thumbnail_cache
            self.thumbnail_cache_order = new_thumbnail_cache_order
            self.gallery_thumbnails = new_gallery_thumbnails
            
            # Update current index
            if len(self.image_files) == 0:
                # No more images
                self.current_index = -1
                self.image_canvas.delete("all")
                self.update_status()
                self.update_navigation_state()
                if self.gallery_canvas:
                    self.gallery_canvas.delete("all")
                    self.gallery_thumbnails.clear()
            elif self.current_index >= len(self.image_files):
                # Was at the end, go to the new last image
                self.current_index = len(self.image_files) - 1
                self.update_image_display(self.current_index, reset_zoom=True)
                self.load_thumbnails_around_index(self.current_index)
                self.root.after_idle(lambda: self._scroll_gallery_to_thumbnail(self.current_index))
            else:
                # Stay at same index (which now points to the next image)
                self.update_image_display(self.current_index, reset_zoom=True)
                self.load_thumbnails_around_index(self.current_index)
                self.root.after_idle(lambda: self._scroll_gallery_to_thumbnail(self.current_index))
            
            # Update gallery to reflect the removed image
            if self.gallery_canvas and len(self.image_files) > 0:
                # Rebuild gallery with updated indices
                self.update_gallery()
            
            self.update_status()
            self.update_navigation_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete photo:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def prev_image(self):
        """Moves to and displays the previous image, resetting zoom, pan, and rotation.
        Automatically skips corrupted images and continues to the previous valid one."""
        if self.current_index <= 0:
            return
        
        # Try to find the previous valid image
        start_index = self.current_index - 1
        max_attempts = start_index + 1
        attempts = 0
        
        while attempts < max_attempts:
            prev_index = start_index - attempts
            if prev_index < 0:
                break
            # Try to load the image
            if self.update_image_display(prev_index, reset_zoom=True):
                # Successfully loaded, preload adjacent images for smooth navigation
                self.pre_cache_next()
                # Load thumbnails around current position if needed
                self.load_thumbnails_around_index(prev_index)
                return
            attempts += 1

    def toggle_selection(self):
        """Toggles the current image's selection state via double-click."""
        if self.current_index == -1 or not self.image_files:
            return

        current_file = self.image_files[self.current_index]
        
        if current_file in self.selected_files:
            self.selected_files.remove(current_file)
        else:
            self.selected_files.add(current_file)

        self.update_status()
        self.update_navigation_state()
        self._draw_selection_border()
        
    def _draw_selection_border(self):
        """Draws or removes a semi-transparent selection border on the canvas."""
        self.image_canvas.delete("selection_border") 
        
        if self.current_index != -1 and self.image_files[self.current_index] in self.selected_files:
            if self.image_item:
                coords = self.image_canvas.coords(self.image_item)
                if not coords: return
                x, y = coords[0], coords[1]
                
                disp_w = self.current_photo.width()
                disp_h = self.current_photo.height()
                
                pad = 4 
                x0 = x - disp_w / 2 - pad
                y0 = y - disp_h / 2 - pad
                x1 = x + disp_w / 2 + pad
                y1 = y + disp_h / 2 + pad
                
                self.image_canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#2ecc71", 
                    width=4,
                    tags="selection_border"
                )
                self.image_canvas.tag_raise("selection_border") 

    def erase_all_marks(self):
        """Erases all marks and shapes for the current image."""
        if self.current_index == -1 or not self.image_files:
            return
        
        current_file = self.image_files[self.current_index]
        
        # Clear marks and shapes for current image
        if current_file in self.marks_cache:
            del self.marks_cache[current_file]
        if current_file in self.shapes_cache:
            del self.shapes_cache[current_file]
        
        # Clear from canvas
        self.image_canvas.delete("mark")
        self.image_canvas.delete("shape")
        
        # Update UI
        self.update_navigation_state()
        self.update_status()
        self.status_label.config(text="All marks and shapes erased for current image.", foreground="#2ecc71")
    
    def copy_selected_files(self):
        """Copies all selected files to a user-specified destination directory."""
        if not self.selected_files:
            self.status_label.config(text="Error: No photos selected to copy.", foreground="#e74c3c")
            return

        dest_dir = filedialog.askdirectory(title="Select Destination Folder for Copied Images")
        
        if not dest_dir:
            self.status_label.config(text="Copy operation cancelled.", foreground="#f1c40f")
            return

        copied_count = 0
        error_count = 0
        
        self.status_label.config(text=f"Copying {len(self.selected_files)} files...", foreground="#3498db")
        self.root.update() 

        for file_path in self.selected_files:
            try:
                shutil.copy2(file_path, dest_dir)
                copied_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error copying {os.path.basename(file_path)}: {e}")

        if copied_count > 0:
            message = f"Successfully copied {copied_count} photos to: {dest_dir}"
            if error_count > 0:
                message += f" ({error_count} errors occurred. Check console.)"
                self.status_label.config(text=message, foreground="#f39c12")
            else:
                self.status_label.config(text=message, foreground="#2ecc71")
        else:
            self.status_label.config(text=f"Failed to copy any photos. {error_count} errors occurred. Check console.", foreground="#e74c3c")

        self.selected_files.clear()
        self.update_status()
        self.update_navigation_state()

    def save_marked_files(self):
        """Applies stored marks and shapes to the original image files and overwrites them."""
        # Get files with marks or shapes
        marked_files = set()
        for f in self.marks_cache:
            marks = self.marks_cache.get(f)
            if marks and len(marks) > 0:
                marked_files.add(f)
        for f in self.shapes_cache:
            shapes = self.shapes_cache.get(f)
            if shapes and len(shapes) > 0:
                marked_files.add(f)
        marked_files = list(marked_files)
        
        if not marked_files:
            self.status_label.config(text="No marked photos found to save.", foreground="#f1c40f")
            return
            
        saved_count = 0
        self.status_label.config(text=f"Saving {len(marked_files)} marked files...", foreground="#27ae60")
        self.root.update() 
        
        for file_path in marked_files:
            try:
                # 1. Get the original image (ensured to be RGBA in _get_original_image)
                original_img = Image.open(file_path)
                
                # Determine original format and extension for proper saving
                original_format = original_img.format
                
                # Ensure we have an RGBA copy for drawing on
                img_for_draw = original_img.convert('RGBA')
                img_w, img_h = img_for_draw.size
                
                # Create a drawing context
                draw = ImageDraw.Draw(img_for_draw)
                
                # 2. Re-apply all marks
                if file_path in self.marks_cache:
                    marks = self.marks_cache[file_path]
                    for mark in marks:
                        # Get normalized coordinates
                        norm_start = mark['start']
                        norm_end = mark['end']
                        # Get color from mark (default to red for old marks without color)
                        mark_color = mark.get('color', 'red')
                        
                        # Convert normalized coords (0-1) to pixel coords (0-W/H)
                        start_x = int(norm_start[0] * img_w)
                        start_y = int(norm_start[1] * img_h)
                        end_x = int(norm_end[0] * img_w)
                        end_y = int(norm_end[1] * img_h)

                        # Draw line on the image copy with reduced width (3 instead of 8)
                        draw.line([start_x, start_y, end_x, end_y], fill=mark_color, width=3)
                
                # 3. Re-apply all shapes (save all shapes regardless of rotation)
                if file_path in self.shapes_cache:
                    shapes = self.shapes_cache[file_path]
                    if shapes:  # Check if shapes list is not empty
                        for shape in shapes:
                            try:
                                norm_x1, norm_y1, norm_x2, norm_y2 = shape['coords']
                                x1 = int(norm_x1 * img_w)
                                y1 = int(norm_y1 * img_h)
                                x2 = int(norm_x2 * img_w)
                                y2 = int(norm_y2 * img_h)
                                
                                color = shape.get('color', 'red')
                                width = shape.get('width', 2)
                                shape_type = shape['type']
                                
                                if shape_type == "square":
                                    draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
                                elif shape_type == "circle":
                                    draw.ellipse([x1, y1, x2, y2], outline=color, width=width)
                                elif shape_type == "line":
                                    # Line tool - draw a straight line
                                    draw.line([x1, y1, x2, y2], fill=color, width=width)
                            except Exception as shape_error:
                                print(f"Error drawing shape {shape.get('type', 'unknown')}: {shape_error}")
                                continue

                # 4. Save the modified image, overwriting the original file
                # Convert back to the original mode if necessary (e.g., RGB for JPEG)
                if original_img.mode != 'RGBA':
                    final_img = img_for_draw.convert(original_img.mode)
                else:
                    final_img = img_for_draw
                
                # *** CRITICAL FIX: Explicitly pass the original format to .save() ***
                # This prevents PIL from guessing or using a default format that corrupts the file.
                final_img.save(file_path, format=original_format) 
                
                # 5. Invalidate cache for this file
                for index, path in enumerate(self.image_files):
                    if path == file_path and index in self.cache:
                        del self.cache[index]
                        break
                
                # 6. Clear the mark and shape history after successful save
                if file_path in self.marks_cache:
                    del self.marks_cache[file_path]
                if file_path in self.shapes_cache:
                    del self.shapes_cache[file_path]
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving marked image {os.path.basename(file_path)}: {e}")
                
        # If the currently viewed image was just saved, force a redraw to show the embedded marks
        if self.current_index != -1 and self.image_files[self.current_index] in marked_files:
            self.update_image_display(self.current_index)
            
        self.status_label.config(text=f"Successfully saved and overwrote {saved_count} marked file(s).", foreground="#2ecc71")
        self.update_navigation_state()
        self.update_status()

    def update_navigation_state(self):
        """Updates the state of the navigation and copy buttons."""
        is_loaded = len(self.image_files) > 0
        # Check if any file in the marks_cache or shapes_cache has marks/shapes associated with it
        has_marked_files = (any(self.marks_cache.get(f) for f in self.image_files) or 
                           any(self.shapes_cache.get(f) for f in self.image_files))
        
        if not is_loaded:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            return
        
        # Ensure current_index is within valid range
        if self.current_index < 0:
            self.current_index = 0
        elif self.current_index >= len(self.image_files):
            self.current_index = len(self.image_files) - 1
            
        self.prev_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_index < len(self.image_files) - 1 else tk.DISABLED)
            
        self.copy_button.config(state=tk.NORMAL if self.selected_files else tk.DISABLED)
        self.save_button.config(state=tk.NORMAL if has_marked_files else tk.DISABLED)
        self._set_save_button_color(has_marked_files)
        
        # Enable/disable erase all button based on whether current image has marks/shapes
        if is_loaded and self.current_index != -1:
            current_file = self.image_files[self.current_index]
            has_current_marks = (current_file in self.marks_cache and self.marks_cache.get(current_file)) or \
                               (current_file in self.shapes_cache and self.shapes_cache.get(current_file))
            self.erase_all_button.config(state=tk.NORMAL if has_current_marks else tk.DISABLED)
        else:
            self.erase_all_button.config(state=tk.DISABLED)


    def update_status(self):
        """Updates the status bar with file, zoom, selection, and rotation information."""
        if self.current_index == -1 or not self.image_files:
            self.status_label.config(text="Select a directory to start.")
            return

        file_name = os.path.basename(self.image_files[self.current_index])
        zoom_percent = int(self.zoom_factor * 100)
        
        self.copy_button.config(text=f"Copy ({len(self.selected_files)})")

        # Count files that have marks or shapes
        marked_count = len([f for f in self.marks_cache if self.marks_cache.get(f)]) + \
                      len([f for f in self.shapes_cache if self.shapes_cache.get(f)])
        self.save_button.config(text=f"Save ({marked_count})")
        
        # Rotation should now always be 0 as the rotation is saved to the file, but we display the state for clarity
        rotation_info = f" | Rotation: {self.current_rotation}° (A/S)" 
        
        status_text = (
            f"Image {self.current_index + 1} of {len(self.image_files)}: {file_name} "
            f"| Zoom: {zoom_percent}%"
            f"{rotation_info} "
            f"| Selected: {len(self.selected_files)}"
        )
        self.status_label.config(text=status_text, foreground="#ecf0f1")
        
    # --- Blurry Background (Simulated) ---
    def _draw_blurred_background(self):
        """
        Loads, blurs, and draws a specified background image onto the canvas.
        This provides a simulated transparent blurry background.
        """
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()

        if not canvas_w or not canvas_h:
            return # Canvas not yet ready

        # Only draw if a background image path is provided
        if self.background_image_path and os.path.exists(self.background_image_path):
            try:
                # Load and resize background image to fit canvas
                bg_img = Image.open(self.background_image_path).convert("RGBA")
                bg_img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
                
                # Apply blur
                blurred_img = bg_img.filter(ImageFilter.GaussianBlur(radius=10)) # Adjust radius as needed
                
                self.blurred_background_photo = ImageTk.PhotoImage(blurred_img)
                
                # Delete previous background image if it exists
                if self.blurred_canvas_item:
                    self.image_canvas.delete(self.blurred_canvas_item)
                
                # Draw the blurred background image
                self.blurred_canvas_item = self.image_canvas.create_image(
                    canvas_w // 2, canvas_h // 2, 
                    image=self.blurred_background_photo, 
                    anchor=tk.CENTER,
                    tags="blurred_background"
                )
                self.image_canvas.tag_lower("blurred_background") # Ensure it's always at the bottom
                
            except Exception as e:
                print(f"Error drawing blurred background: {e}")
                self.blurred_background_photo = None # Reset on error
                self.image_canvas.config(bg="#34495e") # Fallback to solid color
        else:
            # If no background image path or path is invalid, ensure solid background
            self.image_canvas.config(bg="#34495e")
    
    # --- Gallery/Thumbnail View Methods ---
    
    def _evict_old_thumbnails(self):
        """Evicts old thumbnails from cache when limit is exceeded (LRU eviction)."""
        while len(self.thumbnail_cache) >= self.max_thumbnail_cache_size and self.thumbnail_cache_order:
            # Remove least recently used thumbnail
            oldest_idx = self.thumbnail_cache_order.pop(0)
            if oldest_idx in self.thumbnail_cache:
                del self.thumbnail_cache[oldest_idx]
    
    def _get_thumbnail(self, index):
        """Generates or retrieves a thumbnail for the image at the given index."""
        if index in self.thumbnail_cache:
            # Update access order (move to end for LRU)
            if index in self.thumbnail_cache_order:
                self.thumbnail_cache_order.remove(index)
            self.thumbnail_cache_order.append(index)
            return self.thumbnail_cache[index]
        
        if index < 0 or index >= len(self.image_files):
            return None
        
        try:
            file_path = self.image_files[index]
            img = Image.open(file_path)
            
            # Create thumbnail
            img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            thumbnail_photo = ImageTk.PhotoImage(img)
            
            # Evict old thumbnails if cache is full
            self._evict_old_thumbnails()
            
            # Add to cache with LRU tracking
            self.thumbnail_cache[index] = thumbnail_photo
            if index in self.thumbnail_cache_order:
                self.thumbnail_cache_order.remove(index)
            self.thumbnail_cache_order.append(index)
            return thumbnail_photo
        except Exception as e:
            print(f"Error generating thumbnail for {file_path}: {e}")
            return None
    
    def _load_thumbnail_batch(self, start_idx, end_idx):
        """Loads a batch of thumbnails in a background thread."""
        if not self.image_files or self.thumbnail_loading_active:
            return
        
        self.thumbnail_loading_active = True
        
        def load_thumbnails():
            """Load thumbnails in background thread - load file data, create PIL Image and PhotoImage in main thread."""
            total_images = len(self.image_files)
            end_idx_clamped = min(end_idx, total_images)
            
            # Collect indices that need loading
            indices_to_load = []
            for i in range(start_idx, end_idx_clamped):
                if i not in self.thumbnail_cache:
                    indices_to_load.append(i)
            
            if not indices_to_load:
                self.thumbnail_loading_active = False
                return
            
            # Process in batches to avoid memory issues (small batches for large folders)
            batch_size = 5
            for batch_start in range(0, len(indices_to_load), batch_size):
                batch_end = min(batch_start + batch_size, len(indices_to_load))
                batch = indices_to_load[batch_start:batch_end]
                
                for i in batch:
                    try:
                        file_path = self.image_files[i]
                        if not os.path.exists(file_path):
                            continue
                        
                        # Read the file as bytes in background thread (file I/O is thread-safe)
                        with open(file_path, 'rb') as f:
                            img_bytes = f.read()
                        
                        # Use a closure to capture the index and file path properly
                        def make_cache_handler(idx, img_data, fpath):
                            def cache_handler():
                                try:
                                    # Check cache limit before creating
                                    if len(self.thumbnail_cache) >= self.max_thumbnail_cache_size:
                                        self._evict_old_thumbnails()
                                    
                                    # Verify index is still valid before caching
                                    if idx >= len(self.image_files):
                                        return
                                    if self.image_files[idx] != fpath:
                                        return  # File list changed, skip this thumbnail
                                    
                                    # Skip if already in cache (race condition protection)
                                    if idx in self.thumbnail_cache:
                                        return
                                    
                                    # Create PIL Image from bytes in main thread (required for thread safety)
                                    from io import BytesIO
                                    img = Image.open(BytesIO(img_data))
                                    
                                    # Calculate proportional dimensions to fit within thumbnail_size
                                    original_width, original_height = img.size
                                    ratio = min(self.thumbnail_size / original_width, self.thumbnail_size / original_height)
                                    new_width = int(original_width * ratio)
                                    new_height = int(original_height * ratio)
                                    
                                    # Resize image while maintaining aspect ratio
                                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                    
                                    # Create a new blank image with the desired square thumbnail_size background
                                    background = Image.new("RGBA", (self.thumbnail_size, self.thumbnail_size), (44, 62, 80, 255))  # Match canvas bg
                                    
                                    # Calculate paste position to center the resized image
                                    paste_x = (self.thumbnail_size - new_width) // 2
                                    paste_y = (self.thumbnail_size - new_height) // 2
                                    
                                    background.paste(img, (paste_x, paste_y))
                                    
                                    # Create PhotoImage in main thread (required for Tkinter)
                                    thumbnail_photo = ImageTk.PhotoImage(background)
                                    
                                    # Add to cache with LRU tracking
                                    self.thumbnail_cache[idx] = thumbnail_photo
                                    if idx in self.thumbnail_cache_order:
                                        self.thumbnail_cache_order.remove(idx)
                                    self.thumbnail_cache_order.append(idx)
                                    
                                    # Update gallery if it's already displayed
                                    self._update_gallery_placeholders()
                                except MemoryError:
                                    print(f"Memory error creating thumbnail {idx}, clearing cache")
                                    # Clear cache and try to continue
                                    self.thumbnail_cache.clear()
                                    self.thumbnail_cache_order.clear()
                                except Exception as e:
                                    print(f"Error creating PhotoImage for thumbnail {idx}: {e}")
                            return cache_handler
                        
                        # Schedule PIL Image and PhotoImage creation in main thread
                        self.root.after(0, make_cache_handler(i, img_bytes, file_path))
                    except Exception as e:
                        # Log errors but continue processing other images
                        print(f"Error loading thumbnail {i}: {e}")
                
                # Small delay between batches to prevent overwhelming the main thread
                import time
                time.sleep(0.1)  # Increased delay to prevent memory issues
            
            # Update loaded range
            self.thumbnails_loaded_range = (min(self.thumbnails_loaded_range[0], start_idx), 
                                           max(self.thumbnails_loaded_range[1], end_idx_clamped))
            self.thumbnail_loading_active = False
        
        # Run in background thread
        thumbnail_thread = threading.Thread(target=load_thumbnails, daemon=True)
        thumbnail_thread.start()
    
    def preload_all_thumbnails(self):
        """Pre-loads initial batch of thumbnails (first 50) in a background thread."""
        if not self.image_files:
            return
        
        total_images = len(self.image_files)
        # Only load first 500 thumbnails initially if there are more than 500 photos
        if total_images > self.initial_thumbnail_load_count:
            load_count = self.initial_thumbnail_load_count
        else:
            load_count = total_images
        
        self.thumbnails_loaded_range = (0, load_count)
        self._load_thumbnail_batch(0, load_count)
    
    def load_thumbnails_around_index(self, index, radius=50):
        """Loads thumbnails around a given index if not already loaded (debounced for performance)."""
        if not self.image_files or self.thumbnail_loading_active:
            return
        
        total_images = len(self.image_files)
        start_idx = max(0, index - radius)
        end_idx = min(total_images, index + radius)
        
        # Check if we need to load any thumbnails in this range
        needs_loading = False
        for i in range(start_idx, end_idx):
            if i not in self.thumbnail_cache:
                needs_loading = True
                break
        
        if needs_loading:
            # Delay loading slightly to avoid loading on every single navigation (debounce)
            self.root.after(300, lambda: self._load_thumbnail_batch(start_idx, end_idx) if not self.thumbnail_loading_active else None)
    
    def _update_gallery_placeholders(self):
        """Updates placeholder thumbnails with actual images when they become available."""
        if not self.gallery_canvas or not self.image_files:
            return
        
        # Update thumbnails that have placeholders but now have cached images
        for index in list(self.gallery_thumbnails.keys()):
            if index in self.thumbnail_cache:
                thumbnail_data = self.gallery_thumbnails[index]
                cached_photo = self.thumbnail_cache[index]
                
                # If we have a cached photo but the stored photo is None (placeholder)
                if thumbnail_data['photo'] is None and cached_photo is not None:
                    # Delete old placeholder (text item)
                    self.gallery_canvas.delete(thumbnail_data['image_id'])
                    
                    # Calculate position (use EXACT same calculation as _draw_thumbnail_on_canvas)
                    slot_start = index * self.thumbnail_spacing
                    x = slot_start + self.thumbnail_size // 2 + self.thumbnail_padding // 2
                    y = 55
                    
                    # Draw new image
                    image_id = self.gallery_canvas.create_image(x, y, image=cached_photo, anchor="center")
                    thumbnail_data['image_id'] = image_id
                    thumbnail_data['photo'] = cached_photo  # Update reference
    
    def _draw_thumbnail_on_canvas(self, index):
        """Draws a single thumbnail on the canvas at the given index."""
        if not self.gallery_canvas or not self.image_files:
            return False
        
        try:
            # Calculate x position: center of each thumbnail slot
            # Each slot is thumbnail_spacing wide, starting at index * thumbnail_spacing
            # Center of slot = start + half of spacing
            slot_start = index * self.thumbnail_spacing
            x = slot_start + self.thumbnail_size // 2 + self.thumbnail_padding // 2
            y = 55  # Center vertically (canvas height is 110)
            
            # Get thumbnail from cache
            thumbnail_photo = self.thumbnail_cache.get(index)
            image_id = None
            
            if thumbnail_photo:
                # Draw thumbnail image
                image_id = self.gallery_canvas.create_image(x, y, image=thumbnail_photo, anchor="center")
            else:
                # Draw placeholder text
                image_id = self.gallery_canvas.create_text(
                    x, y, text="...", fill="#7f8c8d", font=("Arial", 12)
                )
            
            # Store references to keep PhotoImage alive and track items
            # Note: We don't draw borders here - selection border is drawn separately in update_gallery_selection
            self.gallery_thumbnails[index] = {
                'image_id': image_id,
                'photo': thumbnail_photo  # Keep reference to prevent garbage collection
            }
            
            return True
        except Exception as e:
            print(f"Error drawing thumbnail {index} on canvas: {e}")
            return False
    
    def _create_gallery_async(self, start_idx, total_images):
        """Creates gallery thumbnails asynchronously in batches using canvas drawing."""
        # Early exit checks - but don't reset flag if we're mid-creation
        if not self.gallery_canvas or not self.image_files:
            if start_idx == 0:  # Only reset on initial call
                self.gallery_updating = False
            return
        
        # Check if canvas still exists
        try:
            if not self.gallery_canvas.winfo_exists():
                if start_idx == 0:  # Only reset on initial call
                    self.gallery_updating = False
                return
        except:
            if start_idx == 0:  # Only reset on initial call
                self.gallery_updating = False
            return
        
        batch_size = 50
        end_idx = min(start_idx + batch_size, total_images)
        
        # Draw batch of thumbnails on canvas
        created_count = 0
        for i in range(start_idx, end_idx):
            try:
                if self._draw_thumbnail_on_canvas(i):
                    created_count += 1
            except Exception as e:
                print(f"Error drawing thumbnail {i} on canvas: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Progress logging (every 50 thumbnails or at completion)
        if start_idx % 50 == 0 or end_idx >= total_images:
            print(f"Gallery creation progress: {end_idx}/{total_images} ({end_idx*100//total_images}%) - drawn {created_count} in this batch")
        
        # Continue with next batch if there are more
        if end_idx < total_images:
            # Use strict index passing - pass end_idx directly as next start_idx
            next_start = end_idx
            def create_next_batch():
                # Verify we should continue
                if not self.gallery_canvas or not self.image_files:
                    print(f"Stopping gallery creation at {next_start}: gallery_canvas or image_files missing")
                    self.gallery_updating = False
                    return
                if not self.gallery_updating:
                    print(f"Stopping gallery creation at {next_start}: gallery_updating flag is False")
                    return
                try:
                    self._create_gallery_async(next_start, total_images)
                except Exception as e:
                    print(f"Error in async gallery creation continuation at index {next_start}: {e}")
                    import traceback
                    traceback.print_exc()
                    self.gallery_updating = False
            self.root.after(1, create_next_batch)
        else:
            # All thumbnails processed - completion
            print(f"Gallery creation completed: {total_images}/{total_images} (100%)")
            
            # Update scroll region to fit all thumbnails
            total_width = total_images * self.thumbnail_spacing
            canvas_height = 110
            self.gallery_canvas.config(scrollregion=(0, 0, total_width, canvas_height))
            
            self.gallery_updating = False
            
            # Safety check: Use a delay to ensure any lagging thumbnails are drawn
            def finalize_gallery():
                try:
                    actual_count = len(self.gallery_thumbnails)
                    print(f"Final gallery thumbnail count: {actual_count}/{total_images}")
                    self.update_gallery_selection()
                    self._update_gallery_placeholders()
                except Exception as e:
                    print(f"Error finalizing gallery: {e}")
            self.root.after(500, finalize_gallery)
    
    def update_gallery(self):
        """Updates the gallery view with all image thumbnails using canvas drawing."""
        if not self.gallery_canvas or not self.image_files:
            return
        
        # Prevent multiple simultaneous updates
        if self.gallery_updating:
            return
        
        self.gallery_updating = True
        
        try:
            # Ensure canvas is still valid
            if not self.gallery_canvas.winfo_exists():
                self.gallery_updating = False
                return
            
            # Clear existing thumbnails from canvas
            self.gallery_canvas.delete("all")
            self.gallery_thumbnails.clear()
            
            # Draw thumbnails for all images asynchronously to avoid blocking
            # This ensures all thumbnails are drawn even for large folders
            total_images = len(self.image_files)
            self._create_gallery_async(0, total_images)
        except Exception as e:
            print(f"Error updating gallery: {e}")
            import traceback
            traceback.print_exc()
            self.gallery_updating = False
    
    def update_gallery_selection(self):
        """Updates the gallery to highlight the currently selected image and centers it."""
        if not self.gallery_canvas or self.current_index == -1 or not self.image_files:
            return
        
        try:
            # Ensure gallery is visible and populated
            if not self.gallery_canvas.winfo_viewable():
                return
            
            # If gallery is empty but we have images, check if it's still being created
            if len(self.gallery_thumbnails) == 0 and len(self.image_files) > 0:
                if not self.gallery_updating:
                    # Gallery is empty and not being created, rebuild it
                    self.root.after(100, lambda: self.update_gallery())
                return
            
            # Remove previous selection border if it exists (using tag for easy deletion)
            self.gallery_canvas.delete("active_selection")
            
            # Draw selection border for current image (ensure index is valid)
            if 0 <= self.current_index < len(self.image_files) and self.current_index in self.gallery_thumbnails:
                # Calculate border to exactly frame the thumbnail image
                # Use the EXACT same calculation as _draw_thumbnail_on_canvas
                slot_start = self.current_index * self.thumbnail_spacing
                image_center_x = slot_start + self.thumbnail_size // 2 + self.thumbnail_padding // 2
                
                # The image is drawn with anchor="center" at (image_center_x, 55)
                # So the image bounds are:
                # Left: image_center_x - thumbnail_size/2
                # Right: image_center_x + thumbnail_size/2
                # Top: 55 - thumbnail_size/2
                # Bottom: 55 + thumbnail_size/2
                x0 = image_center_x - self.thumbnail_size // 2
                x1 = image_center_x + self.thumbnail_size // 2
                y0 = 55 - self.thumbnail_size // 2
                y1 = 55 + self.thumbnail_size // 2
                
                # Draw clean outline border only (no fill, so thumbnail remains fully visible)
                # Note: In Tkinter, rectangle coordinates define the rectangle bounds,
                # and width is the thickness of the outline drawn around those bounds
                self.gallery_canvas.create_rectangle(
                    x0, y0,
                    x1, y1,
                    outline="#3498db", width=3, fill="",  # No fill, just outline
                    tags="active_selection"
                )
                
                # Update last selected index
                self.last_gallery_selection_index = self.current_index
                
                # Scroll gallery to center current image (debounced)
                self.root.after_idle(lambda idx=self.current_index: self._scroll_gallery_to_thumbnail(idx))
        except Exception as e:
            print(f"Error updating gallery selection: {e}")
            import traceback
            traceback.print_exc()
    
    def _safe_update_gallery(self):
        """Safely updates the gallery without clearing it unnecessarily."""
        try:
            if self.gallery_updating:
                return  # Already updating, don't interfere
            
            if self.gallery_canvas and self.image_files:
                # Check if canvas still exists
                if not self.gallery_canvas.winfo_exists():
                    return
                
                # Only update if gallery is actually empty (don't rebuild if partially populated)
                total_images = len(self.image_files)
                if len(self.gallery_thumbnails) == 0 and total_images > 0:
                    # Gallery is completely empty, rebuild it
                    print(f"Safe update: Gallery is empty, rebuilding for {total_images} images")
                    self.update_gallery()
                # Don't rebuild if gallery is partially populated - it might still be creating
        except Exception as e:
            print(f"Error in safe gallery update: {e}")
            # Reset flag on error
            self.gallery_updating = False
    
    def _scroll_gallery_to_thumbnail(self, index):
        """Scrolls the gallery to center the thumbnail at the given index."""
        if not self.gallery_canvas or not self.image_files:
            return
        
        try:
            # Ensure canvas exists
            if not self.gallery_canvas.winfo_exists():
                return
            
            if not (0 <= index < len(self.image_files)):
                return
            
            # Force update to get accurate canvas size
            self.gallery_canvas.update_idletasks()
            
            # Get canvas dimensions
            canvas_width = self.gallery_canvas.winfo_width()
            if canvas_width <= 1:
                return  # Canvas not ready yet
            
            # Calculate thumbnail position using coordinate calculation
            thumb_x = index * self.thumbnail_spacing + self.thumbnail_padding // 2
            thumb_center_x = thumb_x + self.thumbnail_size // 2
            
            # Calculate total scrollable width
            total_width = len(self.image_files) * self.thumbnail_spacing
            
            if total_width > canvas_width:
                # Calculate scroll position to center the thumbnail
                target_center = canvas_width / 2
                scroll_offset = thumb_center_x - target_center
                
                # Calculate scroll position (0.0 to 1.0)
                scroll_pos = scroll_offset / total_width
                scroll_pos = max(0.0, min(1.0, scroll_pos))
                
                self.gallery_canvas.xview_moveto(scroll_pos)
            else:
                # All thumbnails fit, no need to scroll
                self.gallery_canvas.xview_moveto(0)
        except Exception as e:
            print(f"Error scrolling gallery to thumbnail {index}: {e}")
            import traceback
            traceback.print_exc()
    
    def navigate_to_image(self, index):
        """Navigates to the image at the given index and ensures it's visible in gallery."""
        # Strict bounds check - prevent navigation beyond valid range
        if not self.image_files or index < 0 or index >= len(self.image_files):
            return
        
        # Ensure gallery is visible and populated before navigating
        if self.gallery_canvas:
            try:
                # Only rebuild if gallery is truly empty (not just updating)
                if len(self.gallery_thumbnails) == 0 and not self.gallery_updating:
                    # Gallery is empty, rebuild it first, then navigate
                    self.update_gallery()
                    self.root.after(150, lambda idx=index: self._navigate_after_gallery_ready(idx))
                    return
            except:
                # If there's an error, just continue with navigation
                pass
        
        self.update_image_display(index, reset_zoom=True)
        # Load thumbnails around current position if needed
        self.load_thumbnails_around_index(index)
        # Ensure the clicked thumbnail is visible and centered in the gallery
        # Use after_idle to ensure UI is updated first
        self.root.after_idle(lambda idx=index: self._scroll_gallery_to_thumbnail(idx))
    
    def _navigate_after_gallery_ready(self, index):
        """Navigates to image after gallery is ready."""
        # Strict bounds check
        if not self.image_files or index < 0 or index >= len(self.image_files):
            return
        self.update_image_display(index, reset_zoom=True)
        self.root.after_idle(lambda idx=index: self._scroll_gallery_to_thumbnail(idx))


if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk, ImageDraw, ImageFilter
    except ImportError:
        print("Pillow library is not installed.")
        print("Please install it using: pip install Pillow")
        sys.exit(1)
        
    root = tk.Tk()
    app = FastImageViewer(root)
    
    # --- OPTIONAL: SET A BACKGROUND IMAGE PATH HERE FOR THE BLURRED EFFECT ---
    # For example, replace 'path/to/your/background.jpg' with a real image path.
    # If this is left as None, the canvas will revert to a solid color.
    # Example: app.background_image_path = "C:/Users/Aaron/Pictures/my_cool_desktop_wallpaper.jpg"
    
    # To demonstrate, I will generate a simple abstract background image
    # and use that. In a real scenario, you'd point to an existing image file.
    # Generating a temporary image for demonstration:
    temp_bg_path = "temp_blurred_bg.png"
    if not os.path.exists(temp_bg_path):
        try:
            temp_img = Image.new('RGB', (1200, 900), color = (70, 90, 110)) # Dark blue-gray
            draw_temp = ImageDraw.Draw(temp_img)
            # Add some abstract shapes or text to make it interesting
            draw_temp.ellipse((100, 50, 400, 300), fill=(90, 110, 130))
            draw_temp.rectangle((700, 600, 1100, 800), fill=(110, 130, 150))
            draw_temp.text((500, 400), "Fast Image Viewer", fill=(180, 200, 220), font_size=50)
            temp_img.save(temp_bg_path)
            app.background_image_path = temp_bg_path
        except Exception as e:
            print(f"Could not generate temporary background image: {e}")
            app.background_image_path = None # Fallback to no background
            
    root.mainloop()

    # Clean up the temporary background image if it was created
    if 'temp_bg_path' in locals() and os.path.exists(temp_bg_path):
        try:
            os.remove(temp_bg_path)
        except Exception as e:
            print(f"Error cleaning up temporary background image: {e}")