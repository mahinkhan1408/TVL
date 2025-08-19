# dashboard_menu.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from bid_writer_module import BidWriterApp
from notice_board_module import NoticeBoardModule
from vendor_price_module import VendorPriceModule
from gc_roof_ce_module import GCRoofCEModule
from todo_module import ToDoModule
from letterhead_bid_module import LetterheadBidModule
from theme_manager import theme_manager
import time
import os
import re
from datetime import datetime
import json
import shutil

class DashboardMenu:
    def __init__(self, root, username):
        self.root = root
        self.root.title("Techvengers Universal App - Dashboard")
        
        self.username = username
        self.current_module_instance = None

        # Use theme manager for colors
        self.colors = theme_manager.get_current_colors()
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)
        
        self.root.update_idletasks()
        width = int(self.root.winfo_screenwidth() * 0.9)
        height = int(self.root.winfo_screenheight() * 0.9)
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.configure(bg=self.colors['background'])
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
        for btn_text, btn in self.nav_buttons.items():
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
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()

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
        # Notice Boards, To-Do, Note, Approval, Settings
        cards = [
            ("New Bid", "Create a new bid", "🆕", self.create_new_bid),
            ("Open Project", "Continue your saved work", "📂", self.show_bid_writer_dashboard),
            ("Templates", "Bid templates", "📄", lambda: self.show_placeholder("Templates")),
            ("GC/Roof CE", "GC/Roof change orders", "🏗️", self.open_gc_roof_ce),
            ("Vendor Price", "Vendor pricing", "💲", self.open_vendor_price),
            ("Letterheads", "Letterhead bids", "📝", self.open_letterhead_bid),
            ("Notice Boards", "Announcements", "📢", self.open_notice_board),
            ("To-Do", "Tasks & reminders", "✅", self.open_todo),
            ("Note", "Notes (coming soon)", "🗒️", lambda: self.show_placeholder("Note")),
            ("Approval", "Approval workflow", "✔️", lambda: self.show_placeholder("Approval")),
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
        
        tk.Label(recent_header_frame, text="Recent Bids", font=("Arial", 14, "bold"), bg=self.colors['gray_light'], fg=self.colors['primary_blue']).pack(side='left', anchor='w', pady=(0, 10))

        # Search bar
        self.search_entry = tk.Entry(recent_header_frame, width=20, font=("Arial", 11), relief="solid", bd=1)
        self.search_entry.pack(side='right', padx=(0, 5), pady=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.load_recent_bids(search_term=self.search_entry.get()))

        search_button = tk.Button(recent_header_frame, text="Search", command=lambda: self.load_recent_bids(search_term=self.search_entry.get()), font=("Arial", 10), bg=self.colors['light_blue'], fg="white", relief="flat", cursor="hand2")
        search_button.pack(side='right', pady=(0, 10))


        # Scrollable list for recent bids
        recent_canvas = tk.Canvas(recent_frame, bg=self.colors['white'], highlightthickness=0)
        recent_scrollbar = tk.Scrollbar(recent_frame, orient="vertical", command=recent_canvas.yview)
        recent_scrollable_frame = tk.Frame(recent_canvas, bg=self.colors['white'])

        recent_scrollable_frame.bind(
            "<Configure>",
            lambda e: recent_canvas.configure(scrollregion=recent_canvas.bbox("all"))
        )

        recent_canvas.create_window((0, 0), window=recent_scrollable_frame, anchor="nw")
        recent_canvas.configure(yscrollcommand=recent_scrollbar.set)
        
        recent_scrollbar.pack(side="right", fill="y")
        recent_canvas.pack(side="left", fill="both", expand=True)
        
        self.recent_bids_list = recent_scrollable_frame
        
        # Initial load of bids
        self.load_recent_bids()

    def load_recent_bids(self, search_term=""):
        for widget in self.recent_bids_list.winfo_children():
            widget.destroy()

        # Create table headers with more spacing and the new "Export" column
        header_frame = tk.Frame(self.recent_bids_list, bg=self.colors['primary_blue'])
        header_frame.pack(fill='x')
        
        headers = ['WO', 'Bid Count', 'Last Modified', 'Delete', 'Export']
        header_frame.grid_columnconfigure(0, weight=2)
        header_frame.grid_columnconfigure(1, weight=2)
        header_frame.grid_columnconfigure(2, weight=3)
        header_frame.grid_columnconfigure(3, weight=1)
        header_frame.grid_columnconfigure(4, weight=1)

        for i, header in enumerate(headers):
            tk.Label(header_frame, text=header, font=("Arial", 11, "bold"), fg='white', bg=self.colors['primary_blue']).grid(row=0, column=i, sticky='nsew', padx=5, pady=5)

        try:
            files = [f for f in os.listdir(self.app_data_dir) if f.startswith("WO_") and f.endswith(".json")]

            # Filter files based on search term
            if search_term:
                files = [f for f in files if search_term.lower() in f.lower()]

            files.sort(key=lambda f: os.path.getmtime(os.path.join(self.app_data_dir, f)), reverse=True)
            
            if not files:
                tk.Label(self.recent_bids_list, text="No matching bids found.", bg=self.colors['white'], fg=self.colors['gray_dark'], font=("Arial", 10, "italic")).pack(padx=10, pady=10)
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
                
                # Bind the entire row to open the bid
                row_frame.bind("<Button-1>", lambda e, wo=wo_number: self.open_existing_bid(wo))

                # Create clickable labels for each cell
                tk.Label(row_frame, text=wo_number, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['primary_blue'], anchor='w', cursor="hand2").grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
                tk.Label(row_frame, text=bid_count, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2").grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
                tk.Label(row_frame, text=modified_time, font=("Arial", 10), bg=self.colors['white'], fg=self.colors['gray_dark'], anchor='w', cursor="hand2").grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
                
                # Delete button
                delete_button = tk.Button(row_frame, text="Delete", command=lambda wo=wo_number: self.delete_bid_state(wo), font=("Arial", 9), bg='#dc3545', fg='white', relief='flat')
                delete_button.grid(row=0, column=3, sticky='nsew', padx=5, pady=2)

                # Export button
                export_button = tk.Button(row_frame, text="Export", command=lambda wo=wo_number: self.export_bid_state(wo), font=("Arial", 9), bg=self.colors['primary_blue'], fg='white', relief='flat')
                export_button.grid(row=0, column=4, sticky='nsew', padx=5, pady=2)
                
                row_frame.grid_columnconfigure(0, weight=2)
                row_frame.grid_columnconfigure(1, weight=2)
                row_frame.grid_columnconfigure(2, weight=3)
                row_frame.grid_columnconfigure(3, weight=1)
                row_frame.grid_columnconfigure(4, weight=1)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recent bids: {e}")

    # --- Dashboard Card Helper ---
    def _create_dashboard_card(self, parent, row, col, icon, title, subtitle, command):
        card_bg = self.colors['white'] if 'white' in self.colors else '#FFFFFF'
        card = tk.Frame(parent, bg=card_bg, relief='flat', bd=0, highlightthickness=1,
                        highlightbackground=self.colors['gray_light'])
        card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        parent.grid_rowconfigure(row, weight=1)

        # Hover effects
        def on_enter(e):
            card.configure(highlightbackground=self.colors.get('nav_hover', self.colors['primary_blue']),
                           highlightthickness=2)
        def on_leave(e):
            card.configure(highlightbackground=self.colors['gray_light'], highlightthickness=1)
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)

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

        # Click handler for all card area
        def handle_click(_e=None):
            try:
                command()
            except Exception as ex:
                messagebox.showerror("Action", f"Failed to open: {ex}")

        for w in (card, inner):
            w.bind('<Button-1>', handle_click)

    def delete_bid_state(self, wo_number):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete the bid for WO# {wo_number}?"):
            file_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
            try:
                os.remove(file_path)
                messagebox.showinfo("Success", f"Bid for WO# {wo_number} has been deleted.")
                self.load_recent_bids()
            except FileNotFoundError:
                messagebox.showerror("Error", f"File not found for WO# {wo_number}.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")

    def export_bid_state(self, wo_number):
        source_path = os.path.join(self.app_data_dir, f"WO_{wo_number}.json")
        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"File for WO# {wo_number} not found.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("All Files", "*.*")],
            initialfile=f"WO_{wo_number}.json",
            title="Export Bid State"
        )
        
        if file_path:
            try:
                shutil.copyfile(source_path, file_path)
                messagebox.showinfo("Success", f"Bid for WO# {wo_number} exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export file: {e}")

    def create_new_bid(self):
        new_window = tk.Toplevel(self.root)
        BidWriterApp(new_window, self.username, on_save_callback=self.load_recent_bids)
        
    def open_existing_bid(self, wo_number):
        new_window = tk.Toplevel(self.root)
        BidWriterApp(new_window, self.username, wo_number, on_save_callback=self.load_recent_bids)

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

    def open_todo(self):
        new_window = tk.Toplevel(self.root)
        ToDoModule(new_window)

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