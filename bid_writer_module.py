import tkinter as tk
from tkinter import messagebox, filedialog
import os
import time
import sys
from datetime import datetime
import tempfile
import csv
import io
import requests
import json
from docx import Document
from docx.shared import Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.shared import RGBColor
from utils import set_cell_background
from theme_manager import theme_manager
import re

try:
    from PIL import Image, ImageTk, ImageGrab
except ImportError:
    messagebox.showwarning("Missing Module", "PIL/Pillow is required for photo support. Install with: pip install pillow")
    Image = None
    ImageTk = None
    ImageGrab = None

class BidWriterApp:
    def __init__(self, root, username, wo_number_to_load=None, on_save_callback=None):
        self.root = root
        self.root.title("Techvengers Bid Writer")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.9)}")
        
        # Use global theme manager
        self.colors = theme_manager.get_current_colors()
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
        
        self.root.configure(bg=self.colors['background'])

        self.title_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=60)
        self.title_frame.pack(fill='x', pady=(0, 10))
        self.title_frame.pack_propagate(False)
        
        self.username_label = tk.Label(self.title_frame, text=f"{username}", 
                                       font=("Arial", 12, "bold"), fg='white', 
                                       bg=self.colors['primary_blue'])
        self.username_label.pack(side="left", padx=20)
        
        # Search frame in the center
        self.search_frame = tk.Frame(self.title_frame, bg=self.colors['primary_blue'])
        self.search_frame.pack(side="left", expand=True, padx=(20, 0))
        
        # Search functionality
        search_container = tk.Frame(self.search_frame, bg=self.colors['white'], relief="solid", bd=1)
        search_container.pack(anchor="center", pady=10)
        
        self.search_entry = tk.Entry(search_container, font=("Arial", 11), relief="flat", bd=0, 
                                    width=30, bg=self.colors['white'], fg=self.colors['text_primary'])
        self.search_entry.pack(side="left", padx=(8, 5), pady=6)
        self.search_entry.bind("<Return>", lambda e: self.perform_search_with_navigation())
        self.search_entry.bind("<KeyRelease>", lambda e: self.perform_search())
        
        search_button = tk.Button(search_container, text="🔍", font=("Arial", 12), 
                                 bg=self.colors['light_blue'], fg="white", relief="flat", 
                                 cursor="hand2", command=self.perform_search)
        search_button.pack(side="right", padx=(0, 5), pady=2)
        
        # Clear search button
        clear_button = tk.Button(search_container, text="✕", font=("Arial", 10), 
                                bg=self.colors['gray_medium'], fg="white", relief="flat", 
                                cursor="hand2", command=self.clear_search)
        clear_button.pack(side="right", padx=(0, 5), pady=2)

        self.refresh_button = tk.Button(self.title_frame, text="Refresh",
                                       font=("Arial", 10, "bold"), bg=self.colors['light_blue'], 
                                       fg="white", relief="flat", cursor="hand2",
                                       activebackground=self.colors['primary_blue'],
                                       command=self.refresh_bids)
        self.refresh_button.pack(side="right", padx=(0, 20))

        self.categories = {}
        self.all_items = {}
        self.bid_data_url = "https://docs.google.com/spreadsheets/d/1sBPUtZqtoPREX2STfjBIs_kNF4HE4kCvsyloL9oC-tY/gviz/tq?tqx=out:csv&sheet=Sheet1"
        
        self.selected_items = {}
        self.item_photos = {}
        self.item_instances = {}
        self.current_photo_item = None
        self.active_category_button = None
        self.active_category = None
        self.search_highlights = []  # Store highlighted widgets for clearing
        self.current_search_results = []  # Store current search matches for navigation
        
        self.category_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.category_frame.pack(pady=10, anchor="w", padx=20, fill="x")

        self.main_content_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.main_content_frame.pack(pady=10, fill="both", expand=True, padx=20)

        self.canvas = tk.Canvas(self.main_content_frame, bg=self.colors['white'], 
                                highlightthickness=1, highlightcolor=self.colors['gray_light'])
        
        self.v_scrollbar = tk.Scrollbar(self.main_content_frame, orient="vertical", 
                                        command=self.canvas.yview, bg=self.colors['gray_light'])
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['white'])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        def _on_mousewheel(event):
            """Handle mouse wheel scrolling with cross-platform compatibility."""
            try:
                # Windows and newer Mac versions
                if hasattr(event, 'delta') and event.delta:
                    delta = int(-1 * (event.delta / 120))
                # Older Mac versions or other platforms
                else:
                    # For platforms that don't have delta, use default scroll amount
                    delta = -1 if event.num == 4 else 1
                
                # Scroll the canvas
                self.canvas.yview_scroll(delta, "units")
            except (AttributeError, TypeError):
                # Fallback for any unexpected event format
                pass
        
        def _on_mousewheel_up(event):
            """Handle mouse wheel scroll up (Linux)."""
            self.canvas.yview_scroll(-1, "units")
            
        def _on_mousewheel_down(event):
            """Handle mouse wheel scroll down (Linux)."""
            self.canvas.yview_scroll(1, "units")
        
        # Create a comprehensive mouse wheel binding helper
        def bind_mousewheel_to_widget(widget):
            """Bind mouse wheel events to a widget for cross-platform scrolling."""
            try:
                # Windows and Mac
                widget.bind("<MouseWheel>", _on_mousewheel)
                # Linux scroll up
                widget.bind("<Button-4>", _on_mousewheel_up)
                # Linux scroll down  
                widget.bind("<Button-5>", _on_mousewheel_down)
                # Mac trackpad horizontal scroll (bind but ignore for now)
                widget.bind("<Shift-MouseWheel>", lambda e: None)
            except Exception:
                # If binding fails for any reason, continue silently
                pass
        
        # Store the binding function for later use
        self.bind_mousewheel_to_widget = bind_mousewheel_to_widget
        
        # Bind to canvas and scrollable frame
        bind_mousewheel_to_widget(self.canvas)
        bind_mousewheel_to_widget(self.scrollable_frame)

        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.wo_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.wo_frame.pack(pady=(10, 0), padx=20, fill='x')

        self.wo_label = tk.Label(self.wo_frame, text="WO: ", 
                                 font=("Arial", 11, "bold"), bg=self.colors['background'], 
                                 fg=self.colors['primary_blue'])
        self.wo_label.pack(side="left", padx=(0, 5))
        self.wo_entry = tk.Entry(self.wo_frame, font=("Arial", 11), relief="solid", bd=1, width=20, bg=self.colors['white'], fg=self.colors['text_primary'])
        self.wo_entry.pack(side="left", padx=(0, 20))

        self.load_state_button = tk.Button(self.wo_frame, text="Load State", command=self.load_state,
                                           font=("Arial", 10, "bold"), bg=self.colors['light_blue'], fg="white",
                                           relief="flat", cursor="hand2")
        self.load_state_button.pack(side="left", padx=(0, 10))

        self.save_state_button = tk.Button(self.wo_frame, text="Save State", command=self.save_state,
                                           font=("Arial", 10, "bold"), bg=self.colors['light_blue'], fg="white",
                                           relief="flat", cursor="hand2")
        self.save_state_button.pack(side="left", padx=(0, 10))


        self.buttons_container = tk.Frame(self.root, bg=self.colors['background'])
        self.buttons_container.pack(pady=10)

        self.generate_button = tk.Button(self.buttons_container, text="Generate Bids", command=self.generate_bids,
                                         font=("Arial", 12, "bold"), bg=self.colors['green'], 
                                         fg="white", height=1, width=20, relief="solid", bd=1, cursor="hand2")
        self.generate_button.pack(side="left", padx=(0, 10))

        self.clear_button = tk.Button(self.buttons_container, text="Clear Bids", command=self.clear_bids,
                                         font=("Arial", 12, "bold"), bg="#dc3545",
                                         fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.clear_button.pack(side="left", padx=(0, 10))
        
        self.save_docs_button = tk.Button(self.buttons_container, text="Save to Docs", command=self.save_to_docs,
                                         font=("Arial", 12, "bold"), bg=self.colors['primary_blue'], 
                                         fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.save_docs_button.pack(side="left", padx=(0, 10))

        self.output_frame = tk.Frame(self.root, bg=self.colors['gray_light'], relief="solid", bd=1)
        self.output_frame.pack(padx=20, pady=(0, 10), fill='both', expand=False)
        
        self.output_header_frame = tk.Frame(self.output_frame, bg=self.colors['gray_light'])
        self.output_header_frame.pack(fill='x', padx=2, pady=(2, 0))

        self.bid_count_label = tk.Label(self.output_header_frame, text="Total Bids: 0",
                                         font=("Arial", 11, "bold"), bg=self.colors['gray_light'],
                                         fg=self.colors['gray_dark'], anchor="w")
        self.bid_count_label.pack(side="left", padx=(8, 0))
        
        self.output_scrollbar = tk.Scrollbar(self.output_frame)
        self.output_scrollbar.pack(side="right", fill="y")

        self.output_text = tk.Text(self.output_frame, font=("Arial", 11), bg=self.colors['white'], 
                                     wrap=tk.WORD, relief="flat", padx=10, pady=10, height=8,
                                     yscrollcommand=self.output_scrollbar.set)
        self.output_text.pack(fill='both', expand=True, padx=(2, 0), pady=2)
        self.output_scrollbar.config(command=self.output_text.yview)

        self.output_text.images = []

        self.footer_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=40)
        self.footer_frame.pack(fill='x', side='bottom')
        self.footer_frame.pack_propagate(False)
        
        self.footer_label = tk.Label(self.footer_frame, text="All rights reserved Techvengers LTD", 
                                     font=("Arial", 10), fg='white', 
                                     bg=self.colors['primary_blue'])
        self.footer_label.pack(expand=True)
        
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.root.bind('<Control-v>', self.handle_global_paste)
        self.root.bind('<Control-s>', self.focus_search_bar)

        self.on_save_callback = on_save_callback

        self.load_bids_from_url(self.bid_data_url)
        if wo_number_to_load:
            self.wo_entry.insert(0, wo_number_to_load)
            self.load_state()

        self.root.after(300000, self.auto_save)

    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        self.apply_theme_to_all_widgets()

    def perform_search(self):
        """Perform search and highlight matching categories and items across all categories."""
        search_term = self.search_entry.get().strip().lower()
        self.clear_highlights()
        
        if not search_term:
            return
        
        # Search and highlight categories
        for widget in self.category_frame.winfo_children():
            if isinstance(widget, tk.Button):
                category_text = widget.cget("text").lower()
                if search_term in category_text:
                    original_bg = widget.cget("bg")
                    widget.configure(bg="#FFD700")  # Yellow highlight
                    self.search_highlights.append((widget, original_bg))
        
        # Search and highlight items across ALL categories
        self.highlight_matching_items_all_categories(search_term)

    def highlight_matching_items_all_categories(self, search_term):
        """Highlight matching items across all categories and highlight their category buttons."""
        # Track which categories have matching items
        categories_with_matches = set()
        
        # First, search through the complete all_items dataset to find all matching categories
        if hasattr(self, 'all_items'):
            for category, items_list in self.all_items.items():
                for item_data in items_list:
                    item_name = item_data.get('item_name', '').lower()
                    template_text = item_data.get('template', '').lower()
                    
                    if (search_term in item_name or 
                        search_term in template_text):
                        categories_with_matches.add(category)
        
        # Then, highlight any currently displayed items that match
        if hasattr(self, 'selected_items'):
            for category, category_items in self.selected_items.items():
                for item_key, item_info in category_items.items():
                    if item_info.get("button"):
                        # Check if item name matches search term
                        item_name = item_info.get("original_name", "").lower()
                        template_text = item_info.get("template", "").lower()
                        
                        if (search_term in item_name or 
                            search_term in template_text):
                            
                            # Highlight the item button if it's currently displayed
                            button = item_info["button"]
                            if button and button.winfo_exists():
                                original_bg = button.cget("bg")
                                button.configure(bg="#FFD700")  # Yellow highlight
                                self.search_highlights.append((button, original_bg))
        
        # Highlight category buttons that have matching items (if not already highlighted)
        for widget in self.category_frame.winfo_children():
            if isinstance(widget, tk.Button):
                category_text = widget.cget("text")
                if (category_text in categories_with_matches and 
                    widget.cget("bg") != "#FFD700"):  # Don't re-highlight if already highlighted
                    original_bg = widget.cget("bg")
                    widget.configure(bg="#FFD700")  # Yellow highlight
                    self.search_highlights.append((widget, original_bg))

    def highlight_matching_items(self, search_term):
        """Highlight matching items in the current grid."""
        if not hasattr(self, 'selected_items') or not self.active_category:
            return
            
        category = self.active_category
        if category not in self.selected_items:
            return
            
        for item_key, item_info in self.selected_items[category].items():
            if item_info.get("button"):
                # Check if item name matches search term
                item_name = item_info.get("original_name", "").lower()
                template_text = item_info.get("template", "").lower()
                
                if (search_term in item_name or 
                    search_term in template_text):
                    
                    button = item_info["button"]
                    original_bg = button.cget("bg")
                    button.configure(bg="#FFD700")  # Yellow highlight
                    self.search_highlights.append((button, original_bg))

    def clear_search(self):
        """Clear search entry and highlights."""
        self.search_entry.delete(0, tk.END)
        self.clear_highlights()

    def clear_highlights(self):
        """Clear all search highlights."""
        for widget, original_bg in self.search_highlights:
            try:
                if widget.winfo_exists():
                    widget.configure(bg=original_bg)
            except:
                pass
        self.search_highlights.clear()

    def focus_search_bar(self, event=None):
        """Focus the search bar when CTRL+S is pressed."""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break"  # Prevent default save dialog

    def perform_search_with_navigation(self):
        """Perform search with highlighting and navigate to first match."""
        self.perform_search()
        self.navigate_to_first_match()

    def navigate_to_first_match(self):
        """Navigate to the first search match found."""
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            return

        # First, check if any category buttons match
        for widget in self.category_frame.winfo_children():
            if isinstance(widget, tk.Button):
                category_text = widget.cget("text").lower()
                if search_term in category_text:
                    # Click on the first matching category to load its items
                    widget.invoke()
                    return

        # If no category match, look for items and switch to their category
        first_match_category = self.find_first_matching_item_category(search_term)
        if first_match_category:
            # Switch to the category containing the first match
            self.switch_to_category_with_match(first_match_category)
            # Scroll to make the match visible (with a small delay to allow UI to update)
            self.root.after(100, lambda: self.scroll_to_first_item_match(search_term))

    def find_first_matching_item_category(self, search_term):
        """Find the first category that contains a matching item."""
        if not hasattr(self, 'all_items'):
            return None
            
        # Search through all categories to find the first match
        for category, items_list in self.all_items.items():
            for item_data in items_list:
                item_name = item_data.get('item_name', '').lower()
                template_text = item_data.get('template', '').lower()
                
                if search_term in item_name or search_term in template_text:
                    return category
        return None

    def switch_to_category_with_match(self, target_category):
        """Switch to the specified category."""
        for widget in self.category_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == target_category:
                widget.invoke()
                break

    def scroll_to_first_item_match(self, search_term):
        """Scroll the grid to make the first matching item visible."""
        if not hasattr(self, 'selected_items') or not self.active_category:
            return
            
        category = self.active_category
        if category not in self.selected_items:
            return
        
        # Find the first matching item in the current view
        first_match_row = None
        row_idx = 1  # Start after header row
        
        # Sort items to maintain consistent order
        sorted_items = sorted(self.selected_items[category].items(), 
                            key=lambda x: x[1]['instance_info']['key'])
        
        for item_key, item_info in sorted_items:
            item_name = item_info.get("original_name", "").lower()
            template_text = item_info.get("template", "").lower()
            
            if search_term in item_name or search_term in template_text:
                first_match_row = row_idx
                break
            row_idx += 1
        
        if first_match_row is not None:
            # Scroll the canvas to make the matching row visible
            self.scroll_to_row(first_match_row)

    def scroll_to_row(self, row_number):
        """Scroll the canvas to make the specified row visible."""
        try:
            # Update the scroll region first
            self.canvas.update_idletasks()
            
            # Calculate the approximate y position of the row
            # Assuming each row is about 40-50 pixels high (header + content + padding)
            row_height = 45
            target_y = row_number * row_height
            
            # Get the current scroll region
            scroll_region = self.canvas.cget("scrollregion")
            if scroll_region:
                # Parse the scroll region (format: "x1 y1 x2 y2")
                parts = scroll_region.split()
                if len(parts) == 4:
                    total_height = float(parts[3]) - float(parts[1])
                    if total_height > 0:
                        # Calculate the fraction to scroll to
                        scroll_fraction = min(target_y / total_height, 1.0)
                        # Scroll to position
                        self.canvas.yview_moveto(scroll_fraction)
        except Exception as e:
            # If scrolling fails, continue silently
            pass

    def apply_theme_to_all_widgets(self):
        """Apply current theme to all widgets in the application."""
        # Update root
        self.root.configure(bg=self.colors['background'])
        
        # Update main frames
        self.title_frame.configure(bg=self.colors['primary_blue'])
        self.category_frame.configure(bg=self.colors['background'])
        self.main_content_frame.configure(bg=self.colors['background'])
        self.wo_frame.configure(bg=self.colors['background'])
        self.buttons_container.configure(bg=self.colors['background'])
        self.output_frame.configure(bg=self.colors['gray_light'])
        self.output_header_frame.configure(bg=self.colors['gray_light'])
        self.footer_frame.configure(bg=self.colors['primary_blue'])
        
        # Update labels
        self.username_label.configure(bg=self.colors['primary_blue'], fg=self.colors['button_text'])
        self.wo_label.configure(bg=self.colors['background'], fg=self.colors['primary_blue'])
        self.bid_count_label.configure(bg=self.colors['gray_light'], fg=self.colors['gray_dark'])
        self.footer_label.configure(bg=self.colors['primary_blue'], fg=self.colors['button_text'])
        
        # Update search elements
        self.search_frame.configure(bg=self.colors['primary_blue'])
        self.search_entry.configure(bg=self.colors['white'], fg=self.colors['text_primary'])
        
        # Update buttons
        self.refresh_button.configure(bg=self.colors['light_blue'], fg=self.colors['button_text'], 
                                     activebackground=self.colors['primary_blue'])
        self.load_state_button.configure(bg=self.colors['light_blue'], fg=self.colors['button_text'])
        self.save_state_button.configure(bg=self.colors['light_blue'], fg=self.colors['button_text'])
        self.generate_button.configure(bg=self.colors['green'], fg=self.colors['button_text'])
        self.save_docs_button.configure(bg=self.colors['primary_blue'], fg=self.colors['button_text'])
        
        # Update text widgets
        self.output_text.configure(bg=self.colors['white'], fg=self.colors['text_primary'])
        self.wo_entry.configure(bg=self.colors['white'], fg=self.colors['text_primary'])
        
        # Update category buttons if they exist
        if hasattr(self, 'category_frame'):
            for widget in self.category_frame.winfo_children():
                if isinstance(widget, tk.Button):
                    if widget == self.active_category_button:
                        widget.configure(bg=self.colors['active_category_color'], fg=self.colors['button_text'])
                    else:
                        widget.configure(bg=self.colors['light_blue'], fg=self.colors['button_text'],
                                       activebackground=self.colors['primary_blue'])
        
        # Update grid if it exists
        self.update_grid_theme()

    def update_grid_theme(self):
        """Update the grid theme if it exists."""
        if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_children():
            # Re-load the current category to apply new theme
            if hasattr(self, 'active_category') and self.active_category:
                self.load_items(self.active_category)



    def auto_save(self):
        try:
            wo_number = self.wo_entry.get().strip()
            if not wo_number:
                # Keep a stable autosave name across this session
                if not hasattr(self, '_autosave_name'):
                    self._autosave_name = f"AutoSave_{int(time.time())}"
                wo_number = self._autosave_name
                self.wo_entry.delete(0, tk.END)
                self.wo_entry.insert(0, wo_number)
            self.save_state(silent=True)
        except Exception:
            # Avoid crashing autosave on transient widget errors
            pass
        finally:
            self.root.after(300000, self.auto_save)

    def update_bid_buttons(self):
        """Update category buttons and apply highlights based on search query."""
        if self.active_category_button:
            self.active_category_button.configure(bg=self.colors['light_blue'])
        
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        self.active_category_button = None
        
        for category in self.all_items:
            bg_color = self.colors['light_blue']

            btn = tk.Button(self.category_frame, text=category, width=20, height=2, 
                             font=("Arial", 12, "bold"), bg=bg_color, 
                             fg='white', relief="flat", cursor="hand2",
                             activebackground=self.colors['primary_blue'], activeforeground='white')

            btn.configure(command=lambda c=category, b=btn: self.load_items_with_highlight(c, b))
            btn.bind("<Enter>", lambda e, b=btn: self.on_hover(b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_leave_button(b))
            
            btn.pack(side="left", padx=5)

    def on_hover(self, button):
        """Change button color on hover, unless it's the active button."""
        if self.active_category_button and button.cget("text") == self.active_category_button.cget("text"):
            pass
        else:
            button.configure(bg=self.colors['primary_blue'])

    def on_leave_button(self, button):
        """Restore button color on mouse leave, unless it's the active button."""
        if self.active_category_button and button.cget("text") == self.active_category_button.cget("text"):
            pass
        else:
            button.configure(bg=self.colors['light_blue'])
        
    def load_items_with_highlight(self, category, button):
        """Load items and highlight the selected button."""
        if self.active_category_button and self.active_category_button.winfo_exists():
            self.active_category_button.configure(bg=self.colors['light_blue'])
        
        self.active_category_button = button
        self.active_category_button.configure(bg=self.colors['active_category_color'])
        
        self.active_category = category
        self.clear_highlights()  # Clear previous highlights when switching categories
        self.load_items(category)
        
        # Re-apply search if there's a search term
        if hasattr(self, 'search_entry') and self.search_entry.get().strip():
            self.perform_search()

    def refresh_bids(self):
        """Refreshes the bids by reloading from the online URL."""
        self.load_bids_from_url(self.bid_data_url)
        messagebox.showinfo("Refresh Complete", "Bid list has been refreshed successfully.")

    def load_bids_from_url(self, url):
        """Loads bid data from a public CSV file URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            self.categories = {}
            for row in reader:
                if 'Category' in row and 'Item' in row and 'Template' in row:
                    category = row['Category']
                    item_name = row['Item']
                    template = row['Template']
                    unit_price = row.get('Unit Price', '0.00')
                    
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append({'item_name': item_name, 'template': template, 'unit_price': unit_price})
            
            self.all_items = self.categories.copy()
            
        except requests.exceptions.RequestException as e:
            messagebox.showwarning("Network Error", f"Could not connect to the online file. Using default bids.\nError: {e}")
            self.load_default_bids()
        except Exception as e:
            messagebox.showwarning("Error", f"Failed to read data from online file. Using default bids.\nError: {e}")
            self.load_default_bids()
        
        self.update_bid_buttons()
        if self.categories:
            self.active_category = list(self.categories.keys())[0]
            first_button = self.category_frame.winfo_children()[0]
            self.load_items_with_highlight(self.active_category, first_button)

    def load_default_bids(self):
        """Loads hardcoded default bids as a fallback."""
        self.categories = {
            "Landscaping": [
                {'item_name': "Trim Shrubs", 'template': "Trim {quantity} LF of shrubs from the {location} of the property. Price includes time, labor and disposal of generated debris. {info}\nPrice: ${total:.2f}", 'unit_price': '15.00'},
                {'item_name': "Trim Tree", 'template': "Trim {quantity} LF from the medium tree 30' tall and 18\" in diameter from {location} of the property. Price includes time, labor and disposal of generated debris. {info}\nPrice: ${total:.2f}", 'unit_price': '125.00'}
            ],
            "Mold": [
                {'item_name': "Antimicrobial", 'template': "Clean & wipe {quantity} SF area of moldy walls in the {location}. Price includes time, labor, required materials and the removal of the generated debris. Must be approved with the Kilz bid. {info}\nPrice: ${total:.2f}", 'unit_price': '0.40'},
                {'item_name': "Kilz", 'template': "Paint 1 coat of Kilz to {quantity} SF area of moldy walls in the {location}. Price includes time, labor, required materials and the removal of the generated debris. Source of the mold: roof leakage. Must be approved with the Kilz bid. {info}\nPrice: ${total:.2f}", 'unit_price': '0.50'}
            ]
        }
        self.all_items = self.categories.copy()
        
    def load_items(self, category):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        grid_frame = tk.Frame(self.scrollable_frame, bg=self.colors['white'])
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind mouse wheel events to the grid frame
        self.bind_mousewheel_to_widget(grid_frame)
        
        # This list defines the properties for each column
        # minsize is a fixed minimum size in pixels.
        # weight determines how the column expands to fill extra space.
        # Higher weight means more expansion.
        col_configs = [
            (0, 40, 0),     # Key column (fixed width)
            (1, 40, 0),     # Add/Delete column (fixed width)
            (2, 120, 2),    # Item column (expands)
            (3, 50, 0),     # Qty column (fixed width)
            (4, 70, 0),     # Unit Price column (fixed width)
            (5, 70, 0),     # Total Price column (fixed width)
            (6, 120, 2),    # Location column (expands)
            (7, 150, 2),    # Additional Info column (expands)
            (8, 200, 2),    # Additional Info column (expands)

            (9, 150, 4)     # Photo column (much wider - ensures photos are visible)
        ]
        
        for col, min_width, weight in col_configs:
            grid_frame.grid_columnconfigure(col, minsize=min_width, weight=int(weight))

        headings = ["Key", "Add", "Item", "Qty", "Unit Price", "Total Price", "Location", "Additional Info", "Live Preview", "Photo"]
        
        for col, heading in enumerate(headings):
            header_frame = tk.Frame(grid_frame, bg=self.colors['primary_blue'], relief="flat", bd=1)
            header_frame.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            
            label = tk.Label(header_frame, text=heading, font=("Arial", 11, "bold"), 
                             bg=self.colors['primary_blue'], fg='white', anchor="w")
            label.pack(fill="both", expand=True, padx=8, pady=8)
            
            # Bind mouse wheel events to header elements
            self.bind_mousewheel_to_widget(header_frame)
            self.bind_mousewheel_to_widget(label)

        if category not in self.selected_items:
            self.selected_items[category] = {}
        
        if category not in self.item_instances:
            self.item_instances[category] = {}

        if category and category in self.all_items:
            for item_data in self.all_items[category]:
                item_name = item_data['item_name']
                if item_name not in self.item_instances[category] or not self.item_instances[category][item_name]:
                    self.item_instances[category][item_name] = [{
                        'instance_id': 1,
                        'display_name': item_name,
                        'key': f"{item_name}_1"
                    }]

        row_idx = 1
        if category and category in self.all_items:
            all_instances_for_category = []
            for item_name in self.item_instances[category]:
                all_instances_for_category.extend(self.item_instances[category][item_name])
            
            all_instances_for_category.sort(key=lambda x: x['key'])

            for instance_info in all_instances_for_category:
                instance_key = instance_info['key']
                display_name = instance_info['display_name']
                original_name = re.sub(r'#.*', '', display_name).strip()
                item_data = next((item for item in self.all_items[category] if item['item_name'] == original_name), None)
                if not item_data: continue

                if instance_key not in self.selected_items[category]:
                    self.selected_items[category][instance_key] = {
                        "selected": False,
                        "template": item_data['template'],
                        "qty": tk.StringVar(value="0"),
                        "unit_price": tk.StringVar(value=item_data['unit_price']),
                        "location": tk.StringVar(),
                        "add_info": tk.StringVar(),
                        "conjunction_key": tk.StringVar(),
                        "total_price_label": None,
                        "button": None,
                        "preview_text": None,
                        "original_name": original_name,
                        "instance_info": instance_info,
                        "photo_frame": None,
                        "photo_label": None,
                        "user_edited": False
                    }

                item_info = self.selected_items[category][instance_key]
                
                key_cell = tk.Frame(grid_frame, bd=1, relief="solid", bg=self.colors['gray_light'])
                key_cell.grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)
                key_entry = tk.Entry(key_cell, textvariable=item_info["conjunction_key"], font=("Arial", 9), justify="center", bg=self.colors['white'], fg=self.colors['text_primary'], relief="flat", bd=0, width=5)
                key_entry.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind mouse wheel events to key cell elements
                self.bind_mousewheel_to_widget(key_cell)
                self.bind_mousewheel_to_widget(key_entry)

                add_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                    bg=self.colors['gray_light'])
                add_cell.grid(row=row_idx, column=1, sticky="nsew", padx=1, pady=1)
                
                # Bind mouse wheel events to add cell
                self.bind_mousewheel_to_widget(add_cell)
                
                if instance_info['instance_id'] == 1:
                    def make_add_callback(cat=category, name=original_name):
                        return lambda: self.add_item_instance(cat, name)
                    
                    add_btn = tk.Button(add_cell, text="+", font=("Arial", 12, "bold"),
                                         bg=self.colors['light_blue'], fg='white', 
                                         relief="flat", cursor="hand2",
                                         activebackground=self.colors['primary_blue'],
                                         command=make_add_callback())
                    add_btn.pack(fill="both", expand=True, padx=2, pady=2)
                    self.bind_mousewheel_to_widget(add_btn)
                else:
                    def make_delete_callback(cat=category, orig_name=original_name, inst_key=instance_key):
                        return lambda: self.delete_item_instance(cat, orig_name, inst_key)
                    
                    delete_btn = tk.Button(add_cell, text="X", font=("Arial", 10, "bold"),
                                             bg='#dc3545', fg='white',
                                             relief="flat", cursor="hand2",
                                             activebackground='#c82333',
                                             command=make_delete_callback())
                    delete_btn.pack(fill="both", expand=True, padx=2, pady=2)
                    self.bind_mousewheel_to_widget(delete_btn)

                item_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                     bg=self.colors['gray_light'])
                item_cell.grid(row=row_idx, column=2, sticky="nsew", padx=1, pady=1)
                
                def make_toggle_callback(cat=category, name=instance_key):
                    return lambda: self.toggle_item(cat, name)

                btn = tk.Button(item_cell, text=display_name, font=("Arial", 9),
                                 bg=self.colors['selected'] if item_info["selected"] else self.colors['white'],
                                 fg=self.colors['text_primary'], anchor="w", relief="flat", cursor="hand2",
                                 activebackground=self.colors['selected'],
                                 command=make_toggle_callback())
                btn.pack(fill="both", expand=True, padx=3, pady=3)
                item_info["button"] = btn
                
                # Bind mouse wheel events to item cell elements
                self.bind_mousewheel_to_widget(item_cell)
                self.bind_mousewheel_to_widget(btn)

                qty_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                     bg=self.colors['gray_light'])
                qty_cell.grid(row=row_idx, column=3, sticky="nsew", padx=1, pady=1)
                qty_entry = tk.Entry(qty_cell, textvariable=item_info["qty"], font=("Arial", 9), 
                                     justify="center", bg=self.colors['white'], fg=self.colors['text_primary'],
                                     relief="flat", bd=0)
                qty_entry.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind mouse wheel events to qty cell elements
                self.bind_mousewheel_to_widget(qty_cell)
                self.bind_mousewheel_to_widget(qty_entry)

                price_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                      bg=self.colors['gray_light'])
                price_cell.grid(row=row_idx, column=4, sticky="nsew", padx=1, pady=1)
                unit_price_entry = tk.Entry(price_cell, textvariable=item_info["unit_price"], 
                                             font=("Arial", 9), justify="center", 
                                             bg=self.colors['white'], fg=self.colors['text_primary'], relief="flat", bd=0)
                unit_price_entry.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind mouse wheel events to price cell elements
                self.bind_mousewheel_to_widget(price_cell)
                self.bind_mousewheel_to_widget(unit_price_entry)

                total_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                      bg=self.colors['gray_light'])
                total_cell.grid(row=row_idx, column=5, sticky="nsew", padx=1, pady=1)
                total_label = tk.Label(total_cell, text="0.00", font=("Arial", 9, "bold"), 
                                        bg=self.colors['background'], fg=self.colors['text_primary'],
                                        justify="center")
                total_label.pack(fill="both", expand=True, padx=3, pady=3)
                item_info["total_price_label"] = total_label
                
                # Bind mouse wheel events to total cell elements
                self.bind_mousewheel_to_widget(total_cell)
                self.bind_mousewheel_to_widget(total_label)

                location_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                         bg=self.colors['gray_light'])
                location_cell.grid(row=row_idx, column=6, sticky="nsew", padx=1, pady=1)
                location_entry = tk.Entry(location_cell, textvariable=item_info["location"], 
                                         font=("Arial", 9), bg=self.colors['white'], fg=self.colors['text_primary'],
                                         relief="flat", bd=0)
                location_entry.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind mouse wheel events to location cell elements
                self.bind_mousewheel_to_widget(location_cell)
                self.bind_mousewheel_to_widget(location_entry)

                info_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                     bg=self.colors['gray_light'])
                info_cell.grid(row=row_idx, column=7, sticky="nsew", padx=1, pady=1)
                add_info_entry = tk.Entry(info_cell, textvariable=item_info["add_info"], 
                                         font=("Arial", 9), bg=self.colors['white'], fg=self.colors['text_primary'],
                                         relief="flat", bd=0)
                add_info_entry.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind mouse wheel events to info cell elements
                self.bind_mousewheel_to_widget(info_cell)
                self.bind_mousewheel_to_widget(add_info_entry)

                preview_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                         bg=self.colors['gray_light'])
                preview_cell.grid(row=row_idx, column=8, sticky="nsew", padx=1, pady=1)
                # Keep this column compact: do not let children expand the cell's size
                preview_cell.grid_propagate(False)
                preview_cell.configure(width=80)

                preview_text = tk.Text(preview_cell, font=("Arial", 9), width=12,
                                       bg=self.colors['preview_bg'], fg=self.colors['text_primary'],
                                       relief="flat", bd=0, wrap=tk.WORD, height=6,
                                       state=tk.NORMAL)
                preview_text.pack(fill="both", expand=True, padx=3, pady=3)
                
                # Bind text changes to update the generated bids
                preview_text.bind("<KeyRelease>", lambda e, item=item_info: self.on_preview_text_change(item))
                
                item_info["preview_text"] = preview_text
                
                # Bind mouse wheel events to preview cell elements
                self.bind_mousewheel_to_widget(preview_cell)
                self.bind_mousewheel_to_widget(preview_text)

                photo_cell = tk.Frame(grid_frame, bd=1, relief="solid", 
                                      bg=self.colors['gray_light'])
                photo_cell.grid(row=row_idx, column=9, sticky="nsew", padx=1, pady=1)
                
                photo_frame = tk.Frame(photo_cell, bg=self.colors['white'], relief="flat", 
                                       bd=1, height=100)
                photo_frame.pack(fill="both", expand=True, padx=3, pady=3)
                photo_frame.pack_propagate(False)
                
                photo_label = tk.Label(photo_frame, text="Click to Select Photo", 
                                       font=("Arial", 8), fg=self.colors['gray_medium'],
                                       bg=self.colors['white'], cursor="hand2")
                photo_label.pack(fill="both", expand=True)

                photo_buttons_frame = tk.Frame(photo_frame, bg=self.colors['white'])
                photo_buttons_frame.pack(side="bottom", fill="x", padx=3, pady=3)

                paste_btn = tk.Button(photo_buttons_frame, text="Paste (Ctrl+V)",
                                       font=("Arial", 7), bg=self.colors['light_blue'],
                                       fg="white", relief="flat", cursor="hand2",
                                       command=lambda c=category, k=instance_key: self.handle_paste(c, k))
                paste_btn.pack(side="bottom", pady=(2, 0))
                
                # Bind mouse wheel events to photo cell elements
                self.bind_mousewheel_to_widget(photo_cell)
                self.bind_mousewheel_to_widget(photo_frame)
                self.bind_mousewheel_to_widget(photo_label)
                self.bind_mousewheel_to_widget(photo_buttons_frame)
                self.bind_mousewheel_to_widget(paste_btn)

                photo_frame.bind("<Enter>", lambda e, cell=photo_frame: self.on_enter(cell))
                photo_frame.bind("<Leave>", lambda e, cell=photo_frame: self.on_leave(cell))
                
                item_info["photo_frame"] = photo_frame
                item_info["photo_label"] = photo_label
                
                photo_key = f"{category}_{instance_key}"
                if photo_key in self.item_photos and self.item_photos[photo_key]:
                    self.load_photo_display(category, instance_key)
                
                def make_photo_callbacks(cat=category, key=instance_key):
                    return {
                        'click': lambda e: self.select_photo(cat, key),
                    }
                
                callbacks = make_photo_callbacks()
                photo_label.bind("<Button-1>", callbacks['click'])
                photo_frame.bind("<Button-1>", callbacks['click'])
                
                def on_focus_in(event, cat=category, key=instance_key):
                    self.current_photo_item = (cat, key)
                
                photo_frame.bind("<FocusIn>", on_focus_in)
                photo_label.bind("<FocusIn>", on_focus_in)

                item_info["qty"].trace_add("write", lambda *_args, i=item_info: self.update_total_and_preview(i))
                item_info["unit_price"].trace_add("write", lambda *_args, i=item_info: self.update_total_and_preview(i))
                item_info["location"].trace_add("write", lambda *_args, i=item_info: self.update_total_and_preview(i))
                item_info["add_info"].trace_add("write", lambda *_args, i=item_info: self.update_total_and_preview(i))
                item_info["conjunction_key"].trace_add("write", lambda *_args, i=item_info: self.update_all_previews())
                
                self.update_total_and_preview(item_info)
                row_idx += 1
        
        # Reset scroll position to top when switching categories
        self.reset_scroll_to_top()
        
    def reset_scroll_to_top(self):
        """Reset the canvas scroll position to the top."""
        def _perform_scroll_reset():
            try:
                # Update the canvas to ensure the scrollregion is properly set
                self.canvas.update_idletasks()
                # Move the view to the top (0.0 = top, 1.0 = bottom)
                self.canvas.yview_moveto(0.0)
            except Exception:
                # If scrolling fails for any reason, continue silently
                pass
        
        # Use a small delay to ensure the UI has fully updated before scrolling
        self.root.after(50, _perform_scroll_reset)
        
    def save_state(self, silent=False):
        """Saves the current state of selected bids and photos to a JSON file."""
        wo_number = self.wo_entry.get().strip()
        if not wo_number:
            if not silent:
                messagebox.showwarning("Warning", "Please enter a Work Order Number to save the state.")
            return

        state = {
            "selected_items": {},
            "item_photos": {}
        }

        for category, items in self.selected_items.items():
            state["selected_items"][category] = {}
            for item_key, item_data in items.items():
                state["selected_items"][category][item_key] = {
                    "selected": item_data["selected"],
                    "template": item_data["template"],
                    "qty": item_data["qty"].get(),
                    "unit_price": item_data["unit_price"].get(),
                    "location": item_data["location"].get(),
                    "add_info": item_data["add_info"].get(),
                    "original_name": item_data["original_name"],
                    "instance_info": item_data["instance_info"],
                    "conjunction_key": item_data["conjunction_key"].get()
                }
        
        for photo_key, photo_data in self.item_photos.items():
            if photo_data and 'path' in photo_data and photo_data['path']:
                state["item_photos"][photo_key] = photo_data['path']
        
        state_file_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
        try:
            with open(state_file_path, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"Failed to save state: {e}")
            return

        # Notify user (only when not silent)
        if not silent:
            try:
                messagebox.showinfo("Success", f"State saved successfully to:\n{os.path.basename(state_file_path)}")
            except Exception:
                pass

        # Fire post-save callback safely (if dashboard is in a state to handle it)
        if callable(self.on_save_callback):
            try:
                # Defer to event loop to avoid running during widget teardown
                self.root.after(0, self._safe_post_save_callback)
            except Exception:
                pass

    def _safe_post_save_callback(self):
        try:
            if callable(self.on_save_callback):
                self.on_save_callback()
        except Exception:
            # Ignore UI errors from other windows (e.g., when user navigated away)
            pass

    def load_state(self):
        """Loads a saved state from a JSON file and populates the UI."""
        wo_number = self.wo_entry.get().strip()
        if not wo_number:
            messagebox.showwarning("Warning", "Please enter a Work Order Number to load the state.")
            return
        
        state_file_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
        if not os.path.exists(state_file_path):
            messagebox.showerror("Error", f"No saved state found for WO '{wo_number}'.")
            return
        
        try:
            with open(state_file_path, 'r') as f:
                state = json.load(f)
            
            self.selected_items = {}
            self.item_photos = {}
            self.item_instances = {}

            for category, items in state.get("selected_items", {}).items():
                self.selected_items[category] = {}
                self.item_instances[category] = {}
                
                for item_key, item_data in items.items():
                    original_name = item_data['original_name']
                    instance_info = item_data.get('instance_info', {})
                    
                    if original_name not in self.item_instances[category]:
                        self.item_instances[category][original_name] = []
                    self.item_instances[category][original_name].append(instance_info)

                    item_data["qty"] = tk.StringVar(value=item_data.get("qty", "0"))
                    item_data["unit_price"] = tk.StringVar(value=item_data.get("unit_price", "0.00"))
                    item_data["location"] = tk.StringVar(value=item_data.get("location", ""))
                    item_data["add_info"] = tk.StringVar(value=item_data.get("add_info", ""))
                    item_data["conjunction_key"] = tk.StringVar(value=item_data.get("conjunction_key", ""))
                    self.selected_items[category][item_key] = item_data
            
            for photo_key, photo_path in state.get("item_photos", {}).items():
                if os.path.exists(photo_path) and Image:
                    image = Image.open(photo_path)
                    self.item_photos[photo_key] = {'original': image, 'path': photo_path}
            
            self.update_bid_buttons()
            if self.active_category:
                self.load_items(self.active_category)
            
            messagebox.showinfo("Success", f"State for WO '{wo_number}' loaded successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load state: {e}")
    
    def select_photo(self, category, item_key):
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.load_photo(file_path, category, item_key)
    
    def on_enter(self, widget):
        """Highlight the frame on mouse enter."""
        widget.configure(bg=self.colors['gray_light'])

    def on_leave(self, widget):
        """Reset the frame color on mouse leave."""
        widget.configure(bg=self.colors['white'])
        
    def load_photo(self, file_path, category, item_key):
        if Image is None:
            messagebox.showerror("Error", "PIL/Pillow is required for photo support. Install with: pip install pillow")
            return
            
        try:
            image = Image.open(file_path)
            
            photo_key = f"{category}_{item_key}"
            self.item_photos[photo_key] = {
                'original': image,
                'path': file_path
            }
            
            self.load_photo_display(category, item_key)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{str(e)}")
            
    def load_photo_display(self, category, item_key):
        """Displays a photo in the photo bucket from a stored image object."""
        if Image is None: return
        
        photo_key = f"{category}_{item_key}"
        if photo_key not in self.item_photos or not self.item_photos[photo_key]:
            return
            
        try:
            image_copy = self.item_photos[photo_key]['original'].copy()
            image_copy.thumbnail((180, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image_copy)
            
            item_info = self.selected_items[category][item_key]
            if item_info["photo_label"]:
                item_info["photo_label"].configure(image=photo, text="")
                item_info["photo_label"].image = photo
                
                remove_btn = tk.Button(item_info["photo_frame"], text="✕", 
                                        font=("Arial", 8, "bold"), bg='red', fg='white',
                                        command=lambda: self.remove_photo(category, item_key))
                remove_btn.place(relx=1.0, rely=0.0, anchor='ne', width=20, height=20)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image:\n{str(e)}")
    
    def remove_photo(self, category, item_key):
        photo_key = f"{category}_{item_key}"
        if photo_key in self.item_photos:
            del self.item_photos[photo_key]
        
        item_info = self.selected_items[category][item_key]
        if item_info["photo_label"]:
            item_info["photo_label"].configure(image="", text="Click to Select Photo")
            item_info["photo_label"].image = None
        
        for widget in item_info["photo_frame"].winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "✕":
                widget.destroy()
    
    def handle_paste(self, category, item_key):
        if Image is None or ImageGrab is None:
            messagebox.showerror("Error", "PIL/Pillow is required for photo support. Install with: pip install pillow")
            return
            
        try:
            image = ImageGrab.grabclipboard()
            
            if image and isinstance(image, Image.Image):
                photo_key = f"{category}_{item_key}"
                self.item_photos[photo_key] = {
                    'original': image,
                    'path': None
                }
                
                self.load_photo_display(category, item_key)
            else:
                messagebox.showinfo("Paste", "No image found in clipboard")
        except:
            messagebox.showinfo("Paste", "No image found in clipboard")
    
    def handle_global_paste(self, event):
        if hasattr(self, 'current_photo_item') and self.current_photo_item:
            category, item_key = self.current_photo_item
            self.handle_paste(category, item_key)
    
    def add_item_instance(self, category, item_name):
        item_data = next((item for item in self.all_items[category] if item['item_name'] == item_name), None)
        if not item_data: return

        if category not in self.item_instances:
            self.item_instances[category] = {}
        if item_name not in self.item_instances[category]:
            self.item_instances[category][item_name] = []
        
        existing_numbers = [inst['instance_id'] for inst in self.item_instances[category][item_name]]
        next_number = max(existing_numbers) + 1 if existing_numbers else 2
        
        new_instance = {
            'instance_id': next_number,
            'display_name': f"{item_name} #{next_number}",
            'key': f"{item_name}_{next_number}"
        }
        
        self.item_instances[category][item_name].append(new_instance)
        
        self.load_items(category)

    def delete_item_instance(self, category, original_name, instance_key):
        if category in self.item_instances and original_name in self.item_instances[category]:
            self.item_instances[category][original_name] = [
                inst for inst in self.item_instances[category][original_name] 
                if inst['key'] != instance_key
            ]
            
            if instance_key in self.selected_items[category]:
                del self.selected_items[category][instance_key]
            
            photo_key = f"{category}_{instance_key}"
            if photo_key in self.item_photos:
                del self.item_photos[photo_key]
        
        self.load_items(category)

    def update_total_and_preview(self, item_info):
        try:
            q_str = item_info["qty"].get().strip().replace(",", "")
            p_str = item_info["unit_price"].get().strip().replace(",", "")
            q = float(q_str) if q_str else 0.0
            p = float(p_str) if p_str else 0.0
            total = round(q * p, 2)
            
            # Check if widget still exists before updating
            if item_info["total_price_label"].winfo_exists():
                item_info["total_price_label"].config(text=f"{total:.2f}")
        except ValueError:
            total = 0.0
            try:
                if item_info["total_price_label"].winfo_exists():
                    item_info["total_price_label"].config(text="0.00")
            except:
                pass
        except:
            # Widget might be destroyed
            total = 0.0

        self.update_live_preview(item_info, total)

    def update_live_preview(self, item, total_price):
        if item["preview_text"] is None:
            return
            
        # Check if widget still exists
        try:
            if not item["preview_text"].winfo_exists():
                return
        except:
            return
            
        # Check if user has manually edited the preview text
        try:
            current_text = item["preview_text"].get("1.0", tk.END).strip()
            if hasattr(item, 'user_edited') and item['user_edited']:
                # User has manually edited, don't overwrite
                return
        except:
            return
            
        qty = item["qty"].get().strip() or "0"
        location = item["location"].get().strip() or "N/A"
        add_info = item["add_info"].get().strip()
        conjunction_key = item["conjunction_key"].get().strip().upper()

        # Safe template formatting with error handling
        try:
            bid_text = item["template"].format(
                quantity=qty,
                location=location,
                info=add_info,
                total=total_price,
                cause=add_info  # Use add_info as cause if needed
            )
        except KeyError as e:
            # Fallback formatting if template has unexpected placeholders
            try:
                # Try with just the basic placeholders
                bid_text = item["template"].format(
                    quantity=qty,
                    location=location,
                    info=add_info,
                    total=total_price
                )
            except:
                # Ultimate fallback - use raw template
                bid_text = item["template"]
        
        conjunction_prefix = ""
        conjunction_suffix = ""

        if conjunction_key and item["selected"]:
            conjuncted_items = [
                i for cat in self.selected_items.values() 
                for i in cat.values() 
                if i["conjunction_key"].get().strip().upper() == conjunction_key and i["selected"]
            ]
            
            if len(conjuncted_items) > 1:
                sorted_conjuncted_items = sorted(conjuncted_items, key=lambda i: i['instance_info']['key'])
                current_instance_key = item['instance_info']['key']
                
                try:
                    index = next(i for i, sub_item in enumerate(sorted_conjuncted_items) if sub_item['instance_info']['key'] == current_instance_key)
                    number = index + 1
                    conjunction_prefix = f"{conjunction_key}{number}: "
                    conjunction_suffix = f"** {conjunction_key}1 to {conjunction_key}{len(conjuncted_items)} must be approved together **"
                except StopIteration:
                    conjunction_prefix = ""
                    conjunction_suffix = ""
                
        final_bid_text = f"{conjunction_prefix}{bid_text}\n{conjunction_suffix}".strip()
        
        # Update the preview text widget with error handling
        try:
            # Store current cursor position and selection
            current_cursor = item["preview_text"].index(tk.INSERT)
            current_selection = item["preview_text"].tag_ranges(tk.SEL)
            
            item["preview_text"].delete("1.0", tk.END)
            item["preview_text"].insert("1.0", final_bid_text)
            
            # Restore cursor position and selection
            try:
                item["preview_text"].mark_set(tk.INSERT, current_cursor)
                if current_selection:
                    item["preview_text"].tag_add(tk.SEL, current_selection[0], current_selection[1])
            except:
                pass
        except:
            # Widget might be destroyed or invalid
            pass

    def toggle_item(self, category, item_key):
        item = self.selected_items[category][item_key]
        item["selected"] = not item["selected"]
        
        if item["button"]:
            item["button"].configure(bg=self.colors['selected'] if item["selected"] else self.colors['white'])
        
        self.update_all_previews()

    def update_all_previews(self):
        for category_items in self.selected_items.values():
            for item_info in category_items.values():
                if item_info["preview_text"]:
                    try:
                        # Check if widgets still exist before updating
                        if item_info["preview_text"].winfo_exists():
                            self.update_total_and_preview(item_info)
                    except:
                        # Widget might be destroyed, skip this item
                        continue
    
    def on_preview_text_change(self, item_info):
        """Handle text changes in the Live Preview and update generated bids if they exist."""
        # Mark this item as user-edited
        item_info['user_edited'] = True
        
        # Update the generated bids section if it has content
        if hasattr(self, 'output_text') and self.output_text.get("1.0", tk.END).strip():
            self.update_generated_bids_from_preview(item_info)
    
    def update_generated_bids_from_preview(self, edited_item):
        """Update the generated bids section when Live Preview text is edited."""
        if not hasattr(self, 'output_text'):
            return
            
        # Get the current content of the output text
        current_content = self.output_text.get("1.0", tk.END)
        if not current_content.strip():
            return
        
        # Find the item in the generated bids and update it
        item_key = edited_item['instance_info']['key']
        item_name = edited_item['original_name']
        
        # Get the edited preview text
        edited_text = edited_item["preview_text"].get("1.0", tk.END).strip()
        
        # Update the generated bids section
        self.output_text.config(state=tk.NORMAL)
        
        # Find and replace the old bid text with the new one
        lines = current_content.split('\n')
        updated_lines = []
        
        for line in lines:
            if item_name in line and item_key in line:
                # This is the line we need to update
                # Extract the bid number and conjunction info if any
                bid_match = re.match(r'(\d+)\.\s*(.*)', line)
                if bid_match:
                    bid_number = bid_match.group(1)
                    # Create new bid text with the edited preview
                    new_bid_text = f"{bid_number}. {edited_text}"
                    updated_lines.append(new_bid_text)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Update the output text
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", '\n'.join(updated_lines))
        
        self.output_text.config(state=tk.DISABLED)
    
    def save_to_docs(self):
        bid_count = 0
        final_bids = []
        bid_photos = []

        # Count selected items across all categories for verification
        total_selected = 0
        selected_by_category = {}
        for category, cat_items in self.selected_items.items():
            selected_count = sum(1 for item in cat_items.values() if item["selected"])
            if selected_count > 0:
                selected_by_category[category] = selected_count
                total_selected += selected_count

        conjunction_groups = {}
        standalone_bids = []
        for category, category_items in self.selected_items.items():
            for item in category_items.values():
                if item["selected"]:
                    conjunction_key = item["conjunction_key"].get().strip().upper()
                    if conjunction_key:
                        if conjunction_key not in conjunction_groups:
                            conjunction_groups[conjunction_key] = []
                        conjunction_groups[conjunction_key].append(item)
                    else:
                        standalone_bids.append(item)
        
        for key in conjunction_groups:
            conjunction_groups[key].sort(key=lambda x: x['instance_info']['key'])
        
        all_selected_items = []
        for key in sorted(conjunction_groups.keys()):
            all_selected_items.extend(conjunction_groups[key])
        all_selected_items.extend(sorted(standalone_bids, key=lambda x: x['instance_info']['key']))

        if not all_selected_items:
            messagebox.showwarning("No Bids Selected", "Please select some bids before saving to document!")
            return
        
        # Show summary of what will be saved if items from multiple categories
        if len(selected_by_category) > 1:
            category_summary = "\n".join([f"• {cat}: {count} item(s)" for cat, count in selected_by_category.items()])
            result = messagebox.askyesno("Multi-Category Document", 
                f"You are about to save bids from multiple categories:\n\n{category_summary}\n\nTotal: {total_selected} items\n\nContinue?")
            if not result:
                return

        for i, item in enumerate(all_selected_items, 1):
            bid_count += 1
            
            # Use the Live Preview text if available, otherwise use template
            bid_text, _ = self._get_item_bid_data(item)
            
            final_bid_text = f"{bid_count}. {bid_text}"

            final_bids.append(final_bid_text)

            instance_key = item['instance_info']['key']
            category_name = next(cat for cat, items in self.selected_items.items() if instance_key in items)
            photo_key = f"{category_name}_{instance_key}"

            if photo_key in self.item_photos and self.item_photos[photo_key]:
                bid_photos.append(self.item_photos[photo_key])
            else:
                bid_photos.append(None)

        try:
            from docx import Document
            from docx.shared import Inches, Cm
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.shared import RGBColor
            use_docx = True
        except ImportError:
            use_docx = False
            messagebox.showinfo("Info", "python-docx not found. Saving as text file instead.\nTo save as Word document, install: pip install python-docx")

        if use_docx:
            doc = Document()
            
            wo_number = self.wo_entry.get().strip()
            if wo_number:
                doc.add_heading(f"Techvengers Bid Proposal - WO# {wo_number}", 0)
            else:
                doc.add_heading('Techvengers Bid Proposal', 0)
            
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            date_paragraph = doc.add_paragraph(f'Date: {datetime.now().strftime("%B %d, %Y")}')
            date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()
            
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            table.autofit = False
            
            table.columns[0].width = Inches(0.5)
            table.columns[1].width = Inches(3.5)
            table.columns[2].width = Inches(2.0)
            
            hdr_cells = table.rows[0].cells
            
            header_color_hex = self.colors['primary_blue'].lstrip('#')
            set_cell_background(hdr_cells[0], header_color_hex)
            set_cell_background(hdr_cells[1], header_color_hex)
            set_cell_background(hdr_cells[2], header_color_hex)

            for cell, text in zip(hdr_cells, ['SL No.', 'Bids', 'Photos']):
                cell.text = text
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.bold = True
            
            for bid_text, photo_data in zip(final_bids, bid_photos):
                row_cells = table.add_row().cells
                match = re.match(r"(\d+)\. ", bid_text)
                if match:
                    row_cells[0].text = match.group(1)
                    row_cells[1].text = bid_text[len(match.group(0)):]
                else:
                    row_cells[0].text = ""
                    row_cells[1].text = bid_text
                
                if photo_data and photo_data['original']:
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                            temp_path = temp_file.name
                            photo_data['original'].save(temp_path)
                        
                        row_cells[2].paragraphs[0].add_run().add_picture(temp_path, width=Inches(1.5))
                        
                        os.remove(temp_path)
                    except Exception as e:
                        print(f"Error adding image: {e}")
                        row_cells[2].text = "Error loading image"
            
            doc.add_paragraph()
            footer = doc.add_paragraph('Generated by Techvengers Bid Writer')
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_run = footer.runs[0]
            footer_run.italic = True
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Techvengers_Bids_{current_time}.docx"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Word Document", "*.docx"), ("All Files", "*.*")],
                initialfile=default_filename,
                title="Save Bids Document"
            )
            
            if file_path:
                doc.save(file_path)
                messagebox.showinfo("Success", f"Bids saved successfully to:\n{file_path}")
                
                if messagebox.askyesno("Open File", "Would you like to open the saved document?"):
                    try:
                        if os.name == 'nt':
                            os.startfile(file_path)
                        elif sys.platform == 'darwin':
                            os.system(f'open "{file_path}"')
                        else:
                            os.system(f'xdg-open "{file_path}"')
                    except Exception as e:
                        messagebox.showinfo("File Saved", f"Document saved successfully!\nLocation: {file_path}")
        
        else:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Techvengers_Bids_{current_time}.txt"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Document", "*.txt"), ("All Files", "*.*")],
                initialfile=default_filename,
                title="Save Bids Document"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("TECHVENGERS BID PROPOSAL\n")
                    file.write("=" * 50 + "\n")
                    file.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n\n")
                    
                    for bid_text, photo_data in zip(final_bids, bid_photos):
                        file.write(f"{bid_text}\n")
                        if photo_data:
                            file.write("[Photo attached - see Word version for images]\n")
                        file.write("\n")
                        if bid_text != final_bids[-1]:
                            file.write("─" * 50 + "\n\n")
                    
                    file.write("\nGenerated by Techvengers Bid Writer\n")
                
                messagebox.showinfo("Success", f"Bids saved successfully to:\n{file_path}")
                
                if messagebox.askyesno("Open File", "Would you like to open the saved document?"):
                    try:
                        if os.name == 'nt':
                            os.startfile(file_path)
                        elif sys.platform == 'darwin':
                            os.system(f'open "{file_path}"')
                        else:
                            os.system(f'xdg-open "{file_path}"')
                    except Exception as e:
                        messagebox.showinfo("File Saved", f"Document saved successfully!\nLocation: {file_path}")
    
    def generate_bids(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.images = [] 
        
        # Check selections across all categories
        total_selected = sum(
            1 for cat_items in self.selected_items.values()
            for item in cat_items.values() if item["selected"]
        )
        if total_selected == 0:
            messagebox.showinfo("No Selections", "No bids selected!")
            self.bid_count_label.config(text="Total Bids: 0")
            self.output_text.config(state=tk.DISABLED)
            return
        
        conjunction_groups = {}
        standalone_bids = []
        
        # Process all categories to collect selected items
        for cat_items in self.selected_items.values():
            for item in cat_items.values():
                if item["selected"]:
                    key = item["conjunction_key"].get().strip().upper()
                    if key:
                        if key not in conjunction_groups:
                            conjunction_groups[key] = []
                        conjunction_groups[key].append(item)
                    else:
                        standalone_bids.append(item)
        
        bid_number = 1
        
        for key in sorted(conjunction_groups.keys()):
            items = conjunction_groups[key]
            sorted_items = sorted(items, key=lambda x: x['instance_info']['key'])
            for item in sorted_items:
                bid_text, photo_key = self._get_item_bid_data(item)
                numbered_bid = f"{bid_number}. {bid_text}"
                self.output_text.insert(tk.END, f"{numbered_bid}\n")
                # Append price line under the bid text
                try:
                    qty_val = float((item["qty"].get() if hasattr(item["qty"], "get") else str(item["qty"])) or 0)
                except Exception:
                    qty_val = 0.0
                try:
                    unit_val = float((item["unit_price"].get() if hasattr(item["unit_price"], "get") else str(item["unit_price"])) or 0)
                except Exception:
                    unit_val = 0.0
                total_val = round(qty_val * unit_val, 2)
                self.output_text.insert(tk.END, f"Price: ${total_val:.2f}\n")
                
                self._insert_photo(photo_key)
                bid_number += 1
        
        for item in sorted(standalone_bids, key=lambda x: x['instance_info']['key']):
            bid_text, photo_key = self._get_item_bid_data(item)
            numbered_bid = f"{bid_number}. {bid_text}"
            self.output_text.insert(tk.END, f"{numbered_bid}\n")
            # Append price line under the bid text
            try:
                qty_val = float((item["qty"].get() if hasattr(item["qty"], "get") else str(item["qty"])) or 0)
            except Exception:
                qty_val = 0.0
            try:
                unit_val = float((item["unit_price"].get() if hasattr(item["unit_price"], "get") else str(item["unit_price"])) or 0)
            except Exception:
                unit_val = 0.0
            total_val = round(qty_val * unit_val, 2)
            self.output_text.insert(tk.END, f"Price: ${total_val:.2f}\n")
            
            self._insert_photo(photo_key)
            bid_number += 1

        if bid_number == 1:
            messagebox.showinfo("No Selections", "No bids selected!")
            
        self.bid_count_label.config(text=f"Total Bids: {bid_number - 1}")
        self.output_text.config(state=tk.DISABLED)

    def _get_item_bid_data(self, item):
        """Return the text to use for an item's bid and the associated photo key.
        
        Prefers the current Live Preview text (including any user edits). Falls back
        to generating text from the item's template if the preview is empty or missing.
        """
        # Find the category this item belongs to
        category = None
        for cat, items in self.selected_items.items():
            if item in items.values():
                category = cat
                break
        
        if category is None:
            # Fallback: try to find by instance key
            instance_key = item['instance_info']['key']
            for cat, items in self.selected_items.items():
                if instance_key in items:
                    category = cat
                    break
        
        instance_key = item['instance_info']['key']
        photo_key = f"{category}_{instance_key}" if category else f"unknown_{instance_key}"

        # Prefer whatever is visible in the Live Preview cell (only if widget still exists)
        preview_widget = item.get("preview_text")
        if preview_widget is not None:
            try:
                if preview_widget.winfo_exists():
                    preview_value = preview_widget.get("1.0", tk.END).strip()
                    if preview_value:
                        return preview_value, photo_key
            except Exception:
                # Widget may have been destroyed when switching categories; fall back to template
                pass

        # Fallback to constructing from the template
        qty = item["qty"].get().strip().replace(",", "")
        unit_price = item["unit_price"].get().strip().replace(",", "")
        location = item["location"].get().strip()
        add_info = item["add_info"].get().strip()

        try:
            total_price = float(qty) * float(unit_price)
        except ValueError:
            total_price = 0.0

        bid_text = item["template"].format(
            quantity=qty or "0",
            location=location or "N/A",
            info=add_info or "",
            total=total_price
        )
        return bid_text, photo_key

    def _insert_photo(self, photo_key):
        if photo_key in self.item_photos and self.item_photos[photo_key]:
            try:
                self.output_text.insert(tk.END, "\n")
                image_data = self.item_photos[photo_key]['original'].copy()
                max_width, max_height = 400, 300
                image_data.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                photo_for_output = ImageTk.PhotoImage(image_data)
                
                self.output_text.image_create(tk.END, image=photo_for_output)
                
                self.output_text.images.append(photo_for_output)
                
                self.output_text.insert(tk.END, "\n\n")
            except Exception as e:
                print(f"Error inserting image: {e}")

    def clear_bids(self):
        """Clears the generated bids section and resets all inputs."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.bid_count_label.config(text="Total Bids: 0")
        
        self.output_text.images = []
        
        for category_items in self.selected_items.values():
            for item_info in category_items.values():
                item_info["selected"] = False
                if item_info["button"]:
                    item_info["button"].configure(bg=self.colors['white'])
                item_info["qty"].set("0")
                
                original_name = item_info['original_name']
                category_name = next(cat for cat, items in self.selected_items.items() 
                                     for key, info in items.items() if info == item_info)
                
                initial_price = self.get_initial_price(category_name, original_name)
                item_info["unit_price"].set(initial_price)
                
                item_info["location"].set("")
                item_info["add_info"].set("")
                item_info["conjunction_key"].set("")
                item_info["user_edited"] = False
                self.update_total_and_preview(item_info)
    
    def get_initial_price(self, category_name, item_name):
        """Helper to find the initial price from the all_items data structure."""
        if category_name in self.all_items and isinstance(self.all_items[category_name], list):
            item_data = next((item_dict for item_dict in self.all_items[category_name] if item_dict.get('item_name') == item_name), None)
            if item_data and 'unit_price' in item_data:
                return item_data['unit_price']
        
        return "0.00"