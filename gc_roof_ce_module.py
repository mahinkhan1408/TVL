# gc_roof_ce_module.py
import tkinter as tk
from tkinter import messagebox, ttk
import math
import requests
import csv
import io
import re

class GCRoofCEModule:
    def __init__(self, root):
        self.root = root
        self.root.title("GC/Roof CE - Cost Estimator")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.85)}")
        self.root.configure(bg='#f8f9fa')

        self.colors = {
            'primary_blue': '#1e3a5f',
            'light_blue': '#3498db',
            'background': '#f8f9fa',
            'white': '#ffffff',
            'gray_light': '#e9ecef',
            'gray_medium': '#6c757d',
            'gray_dark': '#495057',
            'green': '#28a745',
            'result_bg': '#d4edda',
            'output_bg': '#ffffff'
        }
        
        self.gc_pricing_data = {}
        self.roof_pricing_data = {}
        self.combined_pricing_data_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRJEpqzTtW-2qqxzkI_QMkwwaYIEEHid_3j1blvxwovK7aVXWB0411eBZVjKZCEKFYaQ8VcLdPe_IU6/pub?output=csv"
        
        self.title_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=60)
        self.title_frame.pack(fill='x', pady=(0, 10))
        self.title_frame.pack_propagate(False)
        
        tk.Label(self.title_frame, text="GC/Roof Cost Estimator", 
                 font=("Arial", 18, "bold"), fg='white', 
                 bg=self.colors['primary_blue']).pack(side="left", expand=True, padx=20)

        self.refresh_button = tk.Button(self.title_frame, text="Refresh Prices",
                                        font=("Arial", 10, "bold"), bg=self.colors['light_blue'], 
                                        fg="white", relief="flat", cursor="hand2",
                                        command=self.load_all_pricing_data)
        self.refresh_button.pack(side="right", padx=(0, 20))
        
        self.main_content_frame = tk.Frame(self.root, bg=self.colors['background'], padx=20, pady=10)
        self.main_content_frame.pack(fill="both", expand=True)

        # Left side: Scrollable container for both sections
        left_container = tk.Frame(self.main_content_frame, bg=self.colors['background'])
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Canvas and scrollbar for scrollable content
        self.left_canvas = tk.Canvas(left_container, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)
        self.scrollable_content = tk.Frame(self.left_canvas, bg=self.colors['background'])

        def update_scroll_region(event=None):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

        self.scrollable_content.bind("<Configure>", update_scroll_region)

        canvas_window = self.left_canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.left_canvas.configure(yscrollcommand=scrollbar.set)

        # Update canvas window width when canvas is resized
        def configure_canvas_width(event):
            canvas_width = event.width
            self.left_canvas.itemconfig(canvas_window, width=canvas_width)
        self.left_canvas.bind('<Configure>', configure_canvas_width)

        scrollbar.pack(side="right", fill="y")
        self.left_canvas.pack(side="left", fill="both", expand=True)

        # Bind mouse wheel
        def on_mousewheel(event):
            try:
                if hasattr(self, 'left_canvas') and self.left_canvas.winfo_exists():
                    self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # Widget was destroyed, ignore
        self.left_canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Grass Cut Section
        gc_section_label = tk.Label(self.scrollable_content, text="Grass Cut", 
                                     font=("Arial", 16, "bold"), bg=self.colors['background'], 
                                     fg=self.colors['primary_blue'])
        gc_section_label.pack(anchor="w", pady=(0, 10))

        self.gc_tab = tk.Frame(self.scrollable_content, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        self.gc_tab.pack(fill="x", pady=(0, 15))
        self.build_gc_frame(self.gc_tab)

        # Buttons for Grass Cut section
        gc_buttons_frame = tk.Frame(self.scrollable_content, bg=self.colors['background'])
        gc_buttons_frame.pack(fill="x", pady=(0, 20))

        self.gc_generate_button = tk.Button(gc_buttons_frame, text="Generate Bids", command=self.generate_bids,
                                            font=("Arial", 12, "bold"), bg=self.colors['green'], 
                                            fg="white", height=1, width=20, relief="solid", bd=1, cursor="hand2")
        self.gc_generate_button.pack(side="left", padx=(0, 10))
        
        self.gc_clear_button = tk.Button(gc_buttons_frame, text="Clear Bids", command=self.clear_bids,
                                          font=("Arial", 12, "bold"), bg="#dc3545",
                                          fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.gc_clear_button.pack(side="left", padx=(0, 10))

        # Stairs and Rail Section
        stairs_rail_section_label = tk.Label(self.scrollable_content, text="Stairs and Rail", 
                                             font=("Arial", 16, "bold"), bg=self.colors['background'], 
                                             fg=self.colors['primary_blue'])
        stairs_rail_section_label.pack(anchor="w", pady=(20, 10))
        
        self.stairs_rail_tab = tk.Frame(self.scrollable_content, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        self.stairs_rail_tab.pack(fill="x", pady=(0, 15))
        self.build_stairs_rail_frame(self.stairs_rail_tab)
        
        # Buttons for Stairs and Rail section
        stairs_rail_buttons_frame = tk.Frame(self.scrollable_content, bg=self.colors['background'])
        stairs_rail_buttons_frame.pack(fill="x", pady=(0, 20))
        
        self.stairs_rail_generate_button = tk.Button(stairs_rail_buttons_frame, text="Generate Bids", command=self.generate_bids,
                                                      font=("Arial", 12, "bold"), bg=self.colors['green'], 
                                                      fg="white", height=1, width=20, relief="solid", bd=1, cursor="hand2")
        self.stairs_rail_generate_button.pack(side="left", padx=(0, 10))
        
        self.stairs_rail_clear_button = tk.Button(stairs_rail_buttons_frame, text="Clear Bids", command=self.clear_stairs_rail_bids,
                                                  font=("Arial", 12, "bold"), bg="#dc3545",
                                                  fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.stairs_rail_clear_button.pack(side="left", padx=(0, 10))
        
        # Fence Section
        fence_section_label = tk.Label(self.scrollable_content, text="Fence", 
                                       font=("Arial", 16, "bold"), bg=self.colors['background'], 
                                       fg=self.colors['primary_blue'])
        fence_section_label.pack(anchor="w", pady=(0, 10))
        
        self.fence_tab = tk.Frame(self.scrollable_content, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        self.fence_tab.pack(fill="x", pady=(0, 15))
        self.build_fence_frame(self.fence_tab)
        
        # Buttons for Fence section
        fence_buttons_frame = tk.Frame(self.scrollable_content, bg=self.colors['background'])
        fence_buttons_frame.pack(fill="x", pady=(0, 20))
        
        self.fence_generate_button = tk.Button(fence_buttons_frame, text="Generate Bids", command=self.generate_bids,
                                               font=("Arial", 12, "bold"), bg=self.colors['green'], 
                                               fg="white", height=1, width=20, relief="solid", bd=1, cursor="hand2")
        self.fence_generate_button.pack(side="left", padx=(0, 10))
        
        self.fence_clear_button = tk.Button(fence_buttons_frame, text="Clear Bids", command=self.clear_fence_bids,
                                            font=("Arial", 12, "bold"), bg="#dc3545",
                                            fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.fence_clear_button.pack(side="left", padx=(0, 10))

        # Roofing Section
        roof_section_label = tk.Label(self.scrollable_content, text="Roofing", 
                                       font=("Arial", 16, "bold"), bg=self.colors['background'], 
                                       fg=self.colors['primary_blue'])
        roof_section_label.pack(anchor="w", pady=(0, 10))

        self.roof_tab = tk.Frame(self.scrollable_content, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        self.roof_tab.pack(fill="x", pady=(0, 15))
        self.build_roof_frame(self.roof_tab)

        # Buttons for Roofing section
        roof_buttons_frame = tk.Frame(self.scrollable_content, bg=self.colors['background'])
        roof_buttons_frame.pack(fill="x", pady=(0, 10))

        self.roof_generate_button = tk.Button(roof_buttons_frame, text="Generate Bids", command=self.generate_bids,
                                               font=("Arial", 12, "bold"), bg=self.colors['green'], 
                                               fg="white", height=1, width=20, relief="solid", bd=1, cursor="hand2")
        self.roof_generate_button.pack(side="left", padx=(0, 10))
        
        self.roof_clear_button = tk.Button(roof_buttons_frame, text="Clear Bids", command=self.clear_bids,
                                           font=("Arial", 12, "bold"), bg="#dc3545",
                                           fg="white", height=1, width=15, relief="solid", bd=1, cursor="hand2")
        self.roof_clear_button.pack(side="left", padx=(0, 10))

        # Right side: Output frame
        self.output_frame = tk.Frame(self.main_content_frame, bg=self.colors['output_bg'], bd=1, relief="solid")
        self.output_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.output_frame, text="Generated Bid:", font=("Arial", 12, "bold"), 
                 bg=self.colors['output_bg'], fg=self.colors['primary_blue']).pack(pady=(10, 5), padx=10, anchor="w")
        
        self.generated_bid_text = tk.Text(self.output_frame, font=("Arial", 11), bg=self.colors['white'], 
                                          wrap=tk.WORD, relief="flat", padx=10, pady=10)
        self.generated_bid_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Load pricing data after UI is created
        self.load_all_pricing_data()

    def build_gc_frame(self, parent_frame):
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)

        tk.Label(parent_frame, text="Grass Height (inches):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.grass_height_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.grass_height_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        self.grass_height_entry.insert(0, "0")
        
        tk.Label(parent_frame, text="Maintainable Lot (SF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.maintainable_lot_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.maintainable_lot_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        self.maintainable_lot_entry.insert(0, "0")
        
        tk.Label(parent_frame, text="Total Lot (SF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.total_lot_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.total_lot_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        self.total_lot_entry.insert(0, "0")
        
        tk.Label(parent_frame, text="Disclaimer:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=3, column=0, sticky="nw", pady=5, padx=5)
        self.disclaimer_text = tk.Text(parent_frame, font=("Arial", 11), relief="solid", bd=1, height=3, wrap=tk.WORD, width=20)
        self.disclaimer_text.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        tk.Label(parent_frame, text="Calculated Price:", font=("Arial", 12, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=4, column=0, sticky="w", pady=15, padx=5)
        self.gc_calculated_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), 
                                               bg=self.colors['result_bg'], fg=self.colors['primary_blue'],
                                               relief="solid", bd=1, padx=10, pady=5)
        self.gc_calculated_price_label.grid(row=4, column=1, sticky="ew", pady=15, padx=5)

        self.grass_height_entry.bind("<KeyRelease>", self.live_update_bid)
        self.maintainable_lot_entry.bind("<KeyRelease>", self.live_update_bid)
        self.total_lot_entry.bind("<KeyRelease>", self.live_update_bid)
        self.disclaimer_text.bind("<KeyRelease>", self.live_update_bid)

    def build_stairs_rail_frame(self, parent_frame):
        """Build UI for Stairs and Rail group (Staircase, Handrail, Guardrail)"""
        # Create notebook for Stairs and Rail tabs
        self.stairs_rail_notebook = ttk.Notebook(parent_frame)
        self.stairs_rail_notebook.pack(fill='both', expand=True)
        
        # Tab 1: Staircase Installation
        staircase_frame = tk.Frame(self.stairs_rail_notebook, bg=self.colors['white'], padx=15, pady=15)
        self.stairs_rail_notebook.add(staircase_frame, text="Staircase")
        self.build_staircase_frame(staircase_frame)
        
        # Tab 2: Handrail & Posts
        handrail_frame = tk.Frame(self.stairs_rail_notebook, bg=self.colors['white'], padx=15, pady=15)
        self.stairs_rail_notebook.add(handrail_frame, text="Handrail & Posts")
        self.build_handrail_frame(handrail_frame)
        
        # Tab 3: Guardrail Installation
        guardrail_frame = tk.Frame(self.stairs_rail_notebook, bg=self.colors['white'], padx=15, pady=15)
        self.stairs_rail_notebook.add(guardrail_frame, text="Guardrail")
        self.build_guardrail_frame(guardrail_frame)
    
    def build_staircase_frame(self, parent_frame):
        """Build UI for Staircase Installation"""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        tk.Label(parent_frame, text="Stair Count:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.stair_count_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.stair_count_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        self.stair_count_entry.insert(0, "0")
        row += 1
        
        tk.Label(parent_frame, text="Step Width (LF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.step_width_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.step_width_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        self.step_width_entry.insert(0, "0")
        row += 1
        
        tk.Label(parent_frame, text="Location:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.staircase_location_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.staircase_location_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        row += 1
        
        # Calculated fields (read-only)
        tk.Label(parent_frame, text="Calculated Fields:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
        row += 1
        
        self.staircase_calc_label = tk.Label(parent_frame, text="", font=("Arial", 10), 
                                              bg=self.colors['white'], fg=self.colors['gray_dark'], justify='left')
        self.staircase_calc_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        row += 1
        
        tk.Label(parent_frame, text="Total Price:", font=("Arial", 12, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=15, padx=5)
        self.staircase_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), 
                                               bg=self.colors['result_bg'], fg=self.colors['primary_blue'],
                                               relief="solid", bd=1, padx=10, pady=5)
        self.staircase_price_label.grid(row=row, column=1, sticky="ew", pady=15, padx=5)
        
        self.stair_count_entry.bind("<KeyRelease>", self.live_update_bid)
        self.step_width_entry.bind("<KeyRelease>", self.live_update_bid)
        self.staircase_location_entry.bind("<KeyRelease>", self.live_update_bid)
    
    def build_handrail_frame(self, parent_frame):
        """Build UI for Handrail & Posts"""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        tk.Label(parent_frame, text="Handrail Length (LF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.handrail_lf_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.handrail_lf_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        self.handrail_lf_entry.insert(0, "0")
        row += 1
        
        tk.Label(parent_frame, text="Location:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.handrail_location_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.handrail_location_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        row += 1
        
        # Calculated fields
        tk.Label(parent_frame, text="Calculated Fields:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
        row += 1
        
        self.handrail_calc_label = tk.Label(parent_frame, text="", font=("Arial", 10), 
                                             bg=self.colors['white'], fg=self.colors['gray_dark'], justify='left')
        self.handrail_calc_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        row += 1
        
        tk.Label(parent_frame, text="Total Price:", font=("Arial", 12, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=15, padx=5)
        self.handrail_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), 
                                             bg=self.colors['result_bg'], fg=self.colors['primary_blue'],
                                             relief="solid", bd=1, padx=10, pady=5)
        self.handrail_price_label.grid(row=row, column=1, sticky="ew", pady=15, padx=5)
        
        self.handrail_lf_entry.bind("<KeyRelease>", self.live_update_bid)
        self.handrail_location_entry.bind("<KeyRelease>", self.live_update_bid)
    
    def build_guardrail_frame(self, parent_frame):
        """Build UI for Guardrail Installation"""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        tk.Label(parent_frame, text="Guardrail Length (LF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.guardrail_lf_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.guardrail_lf_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        self.guardrail_lf_entry.insert(0, "0")
        row += 1
        
        tk.Label(parent_frame, text="Location:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.guardrail_location_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.guardrail_location_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        row += 1
        
        # Calculated fields
        tk.Label(parent_frame, text="Calculated Fields:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
        row += 1
        
        self.guardrail_calc_label = tk.Label(parent_frame, text="", font=("Arial", 10), 
                                              bg=self.colors['white'], fg=self.colors['gray_dark'], justify='left')
        self.guardrail_calc_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        row += 1
        
        tk.Label(parent_frame, text="Total Price:", font=("Arial", 12, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=15, padx=5)
        self.guardrail_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), 
                                               bg=self.colors['result_bg'], fg=self.colors['primary_blue'],
                                               relief="solid", bd=1, padx=10, pady=5)
        self.guardrail_price_label.grid(row=row, column=1, sticky="ew", pady=15, padx=5)
        
        self.guardrail_lf_entry.bind("<KeyRelease>", self.live_update_bid)
        self.guardrail_location_entry.bind("<KeyRelease>", self.live_update_bid)
    
    def build_fence_frame(self, parent_frame):
        """Build UI for Wood Fence Replacement"""
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        tk.Label(parent_frame, text="Fence Length (LF):", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.fence_lf_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.fence_lf_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        self.fence_lf_entry.insert(0, "0")
        row += 1
        
        tk.Label(parent_frame, text="Location:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=5, padx=5)
        self.fence_location_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=15)
        self.fence_location_entry.grid(row=row, column=1, sticky="w", pady=5, padx=5)
        row += 1
        
        # Calculated fields
        tk.Label(parent_frame, text="Calculated Fields:", font=("Arial", 11, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, columnspan=2, sticky="w", pady=(15, 5), padx=5)
        row += 1
        
        self.fence_calc_label = tk.Label(parent_frame, text="", font=("Arial", 10), 
                                         bg=self.colors['white'], fg=self.colors['gray_dark'], justify='left')
        self.fence_calc_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        row += 1
        
        tk.Label(parent_frame, text="Total Price:", font=("Arial", 12, "bold"), 
                 bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=row, column=0, sticky="w", pady=15, padx=5)
        self.fence_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), 
                                          bg=self.colors['result_bg'], fg=self.colors['primary_blue'],
                                          relief="solid", bd=1, padx=10, pady=5)
        self.fence_price_label.grid(row=row, column=1, sticky="ew", pady=15, padx=5)
        
        self.fence_lf_entry.bind("<KeyRelease>", self.live_update_bid)
        self.fence_location_entry.bind("<KeyRelease>", self.live_update_bid)

    def build_roof_frame(self, parent_frame):
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        parent_frame.grid_columnconfigure(2, weight=1)
        parent_frame.grid_columnconfigure(3, weight=1)

        tk.Label(parent_frame, text="Roof Area (SF):", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.roof_area_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.roof_area_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        self.roof_area_entry.insert(0, "0")

        tk.Label(parent_frame, text="Edge Metal (LF):", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.edge_metal_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.edge_metal_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        self.edge_metal_entry.insert(0, "0")

        tk.Label(parent_frame, text="Ridge Cap (LF):", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=0, column=2, sticky="w", pady=5, padx=5)
        self.ridge_cap_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.ridge_cap_entry.grid(row=0, column=3, sticky="w", pady=5, padx=5)
        self.ridge_cap_entry.insert(0, "0")

        tk.Label(parent_frame, text="Roof Jack (EA):", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=1, column=2, sticky="w", pady=5, padx=5)
        self.roof_jack_entry = tk.Entry(parent_frame, font=("Arial", 11), relief="solid", bd=1, width=10)
        self.roof_jack_entry.grid(row=1, column=3, sticky="w", pady=5, padx=5)
        self.roof_jack_entry.insert(0, "0")

        tk.Label(parent_frame, text="Storey:", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.storey_options = ["1", "2"]
        self.selected_storey = tk.StringVar(self.root)
        self.selected_storey.set(self.storey_options[0])
        self.storey_menu = tk.OptionMenu(parent_frame, self.selected_storey, *self.storey_options)
        self.storey_menu.config(font=("Arial", 11), bg=self.colors['white'], relief="solid", bd=1, width=8)
        self.storey_menu.grid(row=2, column=1, sticky="w", pady=5, padx=5)

        tk.Label(parent_frame, text="Client:", font=("Arial", 11, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.client_options = ["Flat Fee", "SLFS", "SCFS"]
        self.selected_client = tk.StringVar(self.root)
        self.selected_client.set(self.client_options[0])
        self.client_menu = tk.OptionMenu(parent_frame, self.selected_client, *self.client_options)
        self.client_menu.config(font=("Arial", 11), bg=self.colors['white'], relief="solid", bd=1, width=8)
        self.client_menu.grid(row=3, column=1, sticky="w", pady=5, padx=5)

        tk.Label(parent_frame, text="Tarp Price:", font=("Arial", 12, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=4, column=0, sticky="w", pady=15, padx=5)
        self.tarp_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), bg=self.colors['result_bg'], fg=self.colors['primary_blue'], relief="solid", bd=1, padx=10, pady=5)
        self.tarp_price_label.grid(row=4, column=1, sticky="ew", pady=15, padx=5)

        tk.Label(parent_frame, text="Replacement Price:", font=("Arial", 12, "bold"), bg=self.colors['white'], fg=self.colors['primary_blue']).grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.replacement_price_label = tk.Label(parent_frame, text="$0.00", font=("Arial", 14, "bold"), bg=self.colors['result_bg'], fg=self.colors['primary_blue'], relief="solid", bd=1, padx=10, pady=5)
        self.replacement_price_label.grid(row=5, column=1, sticky="ew", pady=5, padx=5)

        self.roof_area_entry.bind("<KeyRelease>", self.live_update_bid)
        self.edge_metal_entry.bind("<KeyRelease>", self.live_update_bid)
        self.ridge_cap_entry.bind("<KeyRelease>", self.live_update_bid)
        self.roof_jack_entry.bind("<KeyRelease>", self.live_update_bid)
        self.selected_storey.trace("w", lambda *args: self.live_update_bid())
        self.selected_client.trace("w", lambda *args: self.live_update_bid())

    def load_all_pricing_data(self):
        try:
            response = requests.get(self.combined_pricing_data_url, timeout=10)
            response.raise_for_status()
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            self.gc_pricing_data = {}
            self.roof_pricing_data = {}

            for row in reader:
                service_type = row.get('Service Type', '').strip()
                if service_type == 'Grass Cut':
                    try:
                        base_price = float(re.sub(r'[^\d.]', '', row['Base Price']))
                        additional_price = float(re.sub(r'[^\d.]', '', row['Additional Price per 1000 SF']))
                        template = row.get('Template', "")
                        self.gc_pricing_data[row['Grass Height']] = {'base': base_price, 'additional': additional_price, 'template': template}
                    except (ValueError, KeyError) as e:
                        messagebox.showwarning("GC Data Error", f"Failed to parse GC pricing data for a row. Check column names and values. Error: {e}")
                        self.gc_pricing_data = {}
                        break
                elif service_type == 'Roofing':
                    try:
                        service = row['Service']
                        storey = int(row['Storey'])
                        client = row['Client']
                        rate = float(row['Rate'])
                        if service not in self.roof_pricing_data: self.roof_pricing_data[service] = {}
                        if storey not in self.roof_pricing_data[service]: self.roof_pricing_data[service][storey] = {}
                        self.roof_pricing_data[service][storey][client] = rate
                    except (ValueError, KeyError) as e:
                        messagebox.showwarning("Roof Data Error", f"Failed to parse Roof pricing data for a row. Check column names and values. Error: {e}")
                        self.roof_pricing_data = {}
                        break
            
            if not self.gc_pricing_data and not self.roof_pricing_data:
                messagebox.showwarning("Data Error", "Both pricing data sheets are empty or have incorrect headers. Using default fallback.")
                self.set_default_fallback_data()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not load pricing data. Please check the URL and internet connection. Error: {e}")
            self.set_default_fallback_data()
        
        # Only update bid if UI elements exist
        if hasattr(self, 'generated_bid_text') and self.generated_bid_text.winfo_exists():
            self.live_update_bid()

    def set_default_fallback_data(self):
        self.gc_pricing_data = {
            "2\"-12\"": {"base": 79.68, "additional": 8.74, "template": "Perform initial grass cut of [{grass_condition}] grass measuring up to {grass_height} inch on {maintainable_lot} sq ft area. Price includes equipment, labor and removal of generated debris. (Total lot size: {total_lot} SF, Maintainable area: {maintainable_lot} SF) {disclaimer}"},
            "12\"-24\"": {"base": 111.55, "additional": 15.22, "template": "Perform initial grass cut of [{grass_condition}] grass measuring up to {grass_height} inch on {maintainable_lot} sq ft area. Price includes equipment, labor and removal of generated debris. (Total lot size: {total_lot} SF, Maintainable area: {maintainable_lot} SF) {disclaimer}"},
            "24\"-36\"": {"base": 152.90, "additional": 22.63, "template": "Perform initial grass cut of [{grass_condition}] grass measuring up to {grass_height} inch on {maintainable_lot} sq ft area. Price includes equipment, labor and removal of generated debris. (Total lot size: {total_lot} SF, Maintainable area: {maintainable_lot} SF) {disclaimer}"},
            "36\"-48\"": {"base": 204.84, "additional": 30.02, "template": "Perform initial grass cut of [{grass_condition}] grass measuring up to {grass_height} inch on {maintainable_lot} sq ft area. Price includes equipment, labor and removal of generated debris. (Total lot size: {total_lot} SF, Maintainable area: {maintainable_lot} SF) {disclaimer}"},
            "Above 48\"": {"base": 253.42, "additional": 37.07, "template": "Perform initial grass cut of [{grass_condition}] grass measuring up to {grass_height} inch on {maintainable_lot} sq ft area. Price includes equipment, labor and removal of generated debris. (Total lot size: {total_lot} SF, Maintainable area: {maintainable_lot} SF) {disclaimer}"}
        }
        self.roof_pricing_data = {
            "Tarp": {1: {"Flat Fee": 1.00, "SLFS": 1.25, "SCFS": 1.30}, 2: {"Flat Fee": 1.35, "SLFS": 1.68, "SCFS": 1.75}},
            "Replace": {1: {"Flat Fee": 8.50, "SLFS": 9.50, "SCFS": 10.00}, 2: {"Flat Fee": 9.00, "SLFS": 10.00, "SCFS": 10.50}}
        }

    def calculate_grass_cut_price(self, grass_height_input, maintainable_lot_size):
        if not self.gc_pricing_data: return 0.0, "[GC pricing data not loaded]"
        pricing_tier = None
        if 2 <= grass_height_input <= 12: pricing_tier = "2\"-12\""
        elif 12 < grass_height_input <= 24: pricing_tier = "12\"-24\""
        elif 24 < grass_height_input <= 36: pricing_tier = "24\"-36\""
        elif 36 < grass_height_input <= 48: pricing_tier = "36\"-48\""
        elif grass_height_input > 48: pricing_tier = "Above 48\""
        else: return 0.0, "[Invalid Grass Height Input]"
        if pricing_tier not in self.gc_pricing_data: return 0.0, f"[Pricing data missing for {pricing_tier}]"
        base_price = self.gc_pricing_data[pricing_tier]['base']
        additional_cost_per_1000_sf = self.gc_pricing_data[pricing_tier]['additional']
        total_price = base_price if maintainable_lot_size <= 5000 else base_price + (math.ceil((maintainable_lot_size - 5000) / 1000) * additional_cost_per_1000_sf)
        return total_price, ""

    def calculate_roof_price(self, service, roof_area, storey, client):
        try:
            rate = self.roof_pricing_data[service][storey][client]
            price = rate * roof_area
            return price, ""
        except KeyError:
            return 0.0, f"[Pricing missing for {service}, {storey} storey, {client}]"
        except (ValueError, TypeError):
            return 0.0, "[Invalid numerical input]"
    
    def calculate_staircase_price(self, stair_count, step_width_lf):
        """Calculate price for Staircase Installation - LOGIC 1"""
        try:
            RATE_PER_LF = 18
            stair_count = float(stair_count)
            step_width_lf = float(step_width_lf)
            
            if stair_count <= 0 or step_width_lf <= 0:
                return 0.0, {}, ""
            
            STRINGER_COUNT = math.ceil(step_width_lf / 2) + 1
            STRINGER_LENGTH_LF = stair_count
            TOTAL_STRINGER_LF = STRINGER_COUNT * STRINGER_LENGTH_LF
            TOTAL_STEP_LF = stair_count * step_width_lf
            
            STRINGER_COST = TOTAL_STRINGER_LF * RATE_PER_LF
            STEP_COST = TOTAL_STEP_LF * RATE_PER_LF
            TOTAL_PRICE = STRINGER_COST + STEP_COST
            
            calc_data = {
                'STRINGER_COUNT': STRINGER_COUNT,
                'STRINGER_LENGTH_LF': STRINGER_LENGTH_LF,
                'TOTAL_STRINGER_LF': TOTAL_STRINGER_LF,
                'TOTAL_STEP_LF': TOTAL_STEP_LF
            }
            
            calc_text = f"Stringer Count: {STRINGER_COUNT}\nStringer Length: {int(STRINGER_LENGTH_LF)} LF\nTotal Stringer LF: {int(TOTAL_STRINGER_LF)} LF\nTotal Step LF: {int(TOTAL_STEP_LF)} LF"
            
            return TOTAL_PRICE, calc_data, calc_text
        except (ValueError, TypeError):
            return 0.0, {}, "[Invalid input]"
    
    def calculate_handrail_price(self, handrail_lf):
        """Calculate price for Handrail & Posts - LOGIC 2"""
        try:
            RATE_PER_LF = 18
            handrail_lf = float(handrail_lf)
            
            if handrail_lf <= 0:
                return 0.0, {}, ""
            
            if handrail_lf <= 5:
                POST_COUNT = 2
            elif handrail_lf <= 10:
                POST_COUNT = 3
            elif handrail_lf <= 20:
                POST_COUNT = 5
            else:
                POST_COUNT = math.ceil(handrail_lf / 4)  # For > 20, use ceil(handrail_lf/4)
            
            POST_LENGTH_LF = 5
            TOTAL_POST_LF = POST_COUNT * POST_LENGTH_LF
            TOTAL_PROJECT_LF = handrail_lf + TOTAL_POST_LF
            TOTAL_PRICE = TOTAL_PROJECT_LF * RATE_PER_LF
            
            calc_data = {
                'POST_COUNT': POST_COUNT,
                'POST_LENGTH_LF': POST_LENGTH_LF,
                'TOTAL_POST_LF': TOTAL_POST_LF,
                'TOTAL_PROJECT_LF': TOTAL_PROJECT_LF
            }
            
            calc_text = f"Post Count: {POST_COUNT}\nPost Length: {int(POST_LENGTH_LF)} LF\nTotal Post LF: {int(TOTAL_POST_LF)} LF\nTotal Project LF: {int(TOTAL_PROJECT_LF)} LF"
            
            return TOTAL_PRICE, calc_data, calc_text
        except (ValueError, TypeError):
            return 0.0, {}, "[Invalid input]"
    
    def calculate_guardrail_price(self, guardrail_lf):
        """Calculate price for Guardrail Installation - LOGIC 3"""
        try:
            RATE_PER_LF = 18
            guardrail_lf = float(guardrail_lf)
            
            if guardrail_lf <= 0:
                return 0.0, {}, ""
            
            TOP_RAIL_LF = guardrail_lf
            MIDDLE_RAIL_LF = guardrail_lf
            TOTAL_RAIL_LF = guardrail_lf * 2
            POST_COUNT = math.ceil(guardrail_lf / 5)
            POST_LENGTH_LF = 5
            TOTAL_POST_LF = POST_COUNT * POST_LENGTH_LF
            TOTAL_MATERIAL_LF = TOTAL_RAIL_LF + TOTAL_POST_LF
            TOTAL_PRICE = TOTAL_MATERIAL_LF * RATE_PER_LF
            
            calc_data = {
                'TOP_RAIL_LF': TOP_RAIL_LF,
                'MIDDLE_RAIL_LF': MIDDLE_RAIL_LF,
                'TOTAL_RAIL_LF': TOTAL_RAIL_LF,
                'POST_COUNT': POST_COUNT,
                'POST_LENGTH_LF': POST_LENGTH_LF,
                'TOTAL_POST_LF': TOTAL_POST_LF,
                'TOTAL_MATERIAL_LF': TOTAL_MATERIAL_LF
            }
            
            calc_text = f"Top Rail: {int(TOP_RAIL_LF)} LF\nMiddle Rail: {int(MIDDLE_RAIL_LF)} LF\nTotal Rail: {int(TOTAL_RAIL_LF)} LF\nPost Count: {POST_COUNT}\nPost Length: {int(POST_LENGTH_LF)} LF\nTotal Post LF: {int(TOTAL_POST_LF)} LF\nTotal Material LF: {int(TOTAL_MATERIAL_LF)} LF"
            
            return TOTAL_PRICE, calc_data, calc_text
        except (ValueError, TypeError):
            return 0.0, {}, "[Invalid input]"
    
    def calculate_fence_price(self, fence_lf):
        """Calculate price for Wood Fence Replacement - LOGIC 4"""
        try:
            POST_UNIT_PRICE = 133.62
            FENCE_PRICE_PER_LF = 18
            fence_lf = float(fence_lf)
            
            if fence_lf <= 0:
                return 0.0, {}, ""
            
            POST_COUNT = math.ceil(fence_lf / 8) + 1
            POST_COST = POST_COUNT * POST_UNIT_PRICE
            FENCE_PANEL_COST = fence_lf * FENCE_PRICE_PER_LF
            TOTAL_PRICE = POST_COST + FENCE_PANEL_COST
            
            calc_data = {
                'POST_COUNT': POST_COUNT
            }
            
            calc_text = f"Post Count: {POST_COUNT}"
            
            return TOTAL_PRICE, calc_data, calc_text
        except (ValueError, TypeError):
            return 0.0, {}, "[Invalid input]"

    def live_update_bid(self, event=None):
        try:
            # Check if UI elements exist before trying to use them
            if not hasattr(self, 'generated_bid_text') or not self.generated_bid_text.winfo_exists():
                return
            
            self.generated_bid_text.delete("1.0", tk.END)
            bid_parts = []

            # Update Grass Cut section
            try:
                if hasattr(self, 'grass_height_entry') and self.grass_height_entry.winfo_exists():
                    grass_height_str = self.grass_height_entry.get()
                    maintainable_lot_str = self.maintainable_lot_entry.get()
                    total_lot_str = self.total_lot_entry.get()
                    disclaimer_text_content = self.disclaimer_text.get("1.0", tk.END).strip()
                    grass_height_input = float(grass_height_str) if grass_height_str.replace('.', '', 1).isdigit() else 0.0
                    maintainable_lot = float(maintainable_lot_str) if maintainable_lot_str.replace('.', '', 1).isdigit() else 0.0
                    total_lot = float(total_lot_str) if total_lot_str.replace('.', '', 1).isdigit() else 0.0
                    
                    # Always calculate and update price label
                    calculated_price, price_error_msg = self.calculate_grass_cut_price(grass_height_input, maintainable_lot)
                    if hasattr(self, 'gc_calculated_price_label') and self.gc_calculated_price_label.winfo_exists():
                        self.gc_calculated_price_label.config(text=f"${calculated_price:.2f}" if not price_error_msg else price_error_msg)
                    
                    # Only generate bid text if there's valid input
                    if grass_height_input > 0 or maintainable_lot > 0:
                        grass_condition_text = "over the allowable" if grass_height_input > 12 else "allowable" if 0 < grass_height_input <= 12 else "[Invalid Height]"
                        pricing_tier = None
                        if 2 <= grass_height_input <= 12: pricing_tier = "2\"-12\""
                        elif 12 < grass_height_input <= 24: pricing_tier = "12\"-24\""
                        elif 24 < grass_height_input <= 36: pricing_tier = "24\"-36\""
                        elif 36 < grass_height_input <= 48: pricing_tier = "36\"-48\""
                        elif grass_height_input > 48: pricing_tier = "Above 48\""
                        bid_template = self.gc_pricing_data.get(pricing_tier, {}).get('template', "")
                        if bid_template:
                            # Convert SF values to integers (no decimals)
                            maintainable_lot_int = int(float(maintainable_lot_str)) if maintainable_lot_str.replace('.', '', 1).isdigit() else maintainable_lot_str
                            total_lot_int = int(float(total_lot_str)) if total_lot_str.replace('.', '', 1).isdigit() else total_lot_str
                            gc_bid = bid_template.format(grass_condition=grass_condition_text, grass_height=grass_height_str, maintainable_lot=maintainable_lot_int, total_lot=total_lot_int, disclaimer=disclaimer_text_content)
                            bid_parts.append(("GRASS CUT", gc_bid))
            except Exception as e:
                pass

            # Update Serial Bid Templates section
            try:
                # Staircase Installation
                if hasattr(self, 'stair_count_entry') and self.stair_count_entry.winfo_exists():
                    stair_count = float(self.stair_count_entry.get() or 0)
                    step_width_lf = float(self.step_width_entry.get() or 0)
                    location = self.staircase_location_entry.get().strip()
                    
                    if stair_count > 0 and step_width_lf > 0:
                        price, calc_data, calc_text = self.calculate_staircase_price(stair_count, step_width_lf)
                        if hasattr(self, 'staircase_price_label'):
                            self.staircase_price_label.config(text=f"${price:.2f}")
                        if hasattr(self, 'staircase_calc_label'):
                            self.staircase_calc_label.config(text=calc_text)
                        
                        if location:
                            template = ("Install a {STAIR_COUNT}-step staircase at the {LOCATION} of the property. "
                                       "Scope of work includes installation of {STRINGER_COUNT} stringers ({STRINGER_LENGTH_LF} LF each, "
                                       "Total – {TOTAL_STRINGER_LF} LF) and {STAIR_COUNT} steps ({STEP_WIDTH_LF} LF each, "
                                       "Total – {TOTAL_STEP_LF} LF). Price includes material, labor, time, and removal of generated debris.\n"
                                       "Price: ${price:.2f}")
                            
                            bid_text = template.format(
                                STAIR_COUNT=int(stair_count),
                                LOCATION=location,
                                STRINGER_COUNT=int(calc_data['STRINGER_COUNT']),
                                STRINGER_LENGTH_LF=int(calc_data['STRINGER_LENGTH_LF']),
                                TOTAL_STRINGER_LF=int(calc_data['TOTAL_STRINGER_LF']),
                                STEP_WIDTH_LF=int(step_width_lf),
                                TOTAL_STEP_LF=int(calc_data['TOTAL_STEP_LF']),
                                price=price
                            )
                            bid_parts.append(("STAIRCASE INSTALLATION", bid_text))
                
                # Handrail & Posts
                if hasattr(self, 'handrail_lf_entry') and self.handrail_lf_entry.winfo_exists():
                    handrail_lf = float(self.handrail_lf_entry.get() or 0)
                    location = self.handrail_location_entry.get().strip()
                    
                    if handrail_lf > 0:
                        price, calc_data, calc_text = self.calculate_handrail_price(handrail_lf)
                        if hasattr(self, 'handrail_price_label'):
                            self.handrail_price_label.config(text=f"${price:.2f}")
                        if hasattr(self, 'handrail_calc_label'):
                            self.handrail_calc_label.config(text=calc_text)
                        
                        if location:
                            template = ("Install {TOTAL_POST_LF} LF ({POST_LENGTH_LF} LF each – {POST_COUNT} posts) of posts and "
                                       "{HANDRAIL_LF} LF of handrail (Total – {TOTAL_PROJECT_LF} LF) at the {LOCATION} of the property. "
                                       "Price includes time, labor, and equipment.\nPrice: ${price:.2f}")
                            
                            bid_text = template.format(
                                TOTAL_POST_LF=int(calc_data['TOTAL_POST_LF']),
                                POST_LENGTH_LF=int(calc_data['POST_LENGTH_LF']),
                                POST_COUNT=int(calc_data['POST_COUNT']),
                                HANDRAIL_LF=int(handrail_lf),
                                TOTAL_PROJECT_LF=int(calc_data['TOTAL_PROJECT_LF']),
                                LOCATION=location,
                                price=price
                            )
                            bid_parts.append(("HANDRAIL & POSTS", bid_text))
                
                # Guardrail Installation
                if hasattr(self, 'guardrail_lf_entry') and self.guardrail_lf_entry.winfo_exists():
                    guardrail_lf = float(self.guardrail_lf_entry.get() or 0)
                    location = self.guardrail_location_entry.get().strip()
                    
                    if guardrail_lf > 0:
                        price, calc_data, calc_text = self.calculate_guardrail_price(guardrail_lf)
                        if hasattr(self, 'guardrail_price_label'):
                            self.guardrail_price_label.config(text=f"${price:.2f}")
                        if hasattr(self, 'guardrail_calc_label'):
                            self.guardrail_calc_label.config(text=calc_text)
                        
                        if location:
                            template = ("Install guardrail in a {GUARDRAIL_LF} LF area. Scope of work includes installation of "
                                       "{TOP_RAIL_LF} LF of top rail and {MIDDLE_RAIL_LF} LF of middle rail (Total – {TOTAL_RAIL_LF} LF, "
                                       "2x4 wood will be used), along with {POST_COUNT} posts ({POST_LENGTH_LF} LF each – Total {TOTAL_POST_LF} LF, "
                                       "2x4 wood will be used) to secure the guardrail and prevent trip hazards at the {LOCATION} of the property. "
                                       "Total of {TOTAL_MATERIAL_LF} LF of 2x4 wood will be used. Price includes time, labor, equipment, and material.\n"
                                       "Price: ${price:.2f}")
                            
                            bid_text = template.format(
                                GUARDRAIL_LF=int(guardrail_lf),
                                TOP_RAIL_LF=int(calc_data['TOP_RAIL_LF']),
                                MIDDLE_RAIL_LF=int(calc_data['MIDDLE_RAIL_LF']),
                                TOTAL_RAIL_LF=int(calc_data['TOTAL_RAIL_LF']),
                                POST_COUNT=int(calc_data['POST_COUNT']),
                                POST_LENGTH_LF=int(calc_data['POST_LENGTH_LF']),
                                TOTAL_POST_LF=int(calc_data['TOTAL_POST_LF']),
                                LOCATION=location,
                                TOTAL_MATERIAL_LF=int(calc_data['TOTAL_MATERIAL_LF']),
                                price=price
                            )
                            bid_parts.append(("GUARDRAIL INSTALLATION", bid_text))
                
                # Wood Fence Replacement
                if hasattr(self, 'fence_lf_entry') and self.fence_lf_entry.winfo_exists():
                    fence_lf = float(self.fence_lf_entry.get() or 0)
                    location = self.fence_location_entry.get().strip()
                    
                    if fence_lf > 0:
                        price, calc_data, calc_text = self.calculate_fence_price(fence_lf)
                        if hasattr(self, 'fence_price_label'):
                            self.fence_price_label.config(text=f"${price:.2f}")
                        if hasattr(self, 'fence_calc_label'):
                            self.fence_calc_label.config(text=calc_text)
                        
                        if location:
                            template = ("Install {FENCE_LF} LF of damaged wood fence at the {LOCATION} of the property. "
                                       "Scope of work includes installation of {POST_COUNT} wooden fence posts, set in concrete. "
                                       "Permit will be pulled and invoiced as needed. Price includes equipment, labor, and removal of generated debris.\n"
                                       "Price: ${price:.2f}")
                            
                            bid_text = template.format(
                                FENCE_LF=int(fence_lf),
                                LOCATION=location,
                                POST_COUNT=int(calc_data['POST_COUNT']),
                                price=price
                            )
                            bid_parts.append(("WOOD FENCE REPLACEMENT", bid_text))
            except Exception as e:
                pass

            # Update Roofing section
            try:
                if hasattr(self, 'roof_area_entry') and self.roof_area_entry.winfo_exists():
                    roof_area = float(self.roof_area_entry.get() or 0)
                    edge_metal = float(self.edge_metal_entry.get() or 0)
                    ridge_cap = float(self.ridge_cap_entry.get() or 0)
                    roof_jack = float(self.roof_jack_entry.get() or 0)
                    storey = int(self.selected_storey.get())
                    client = self.selected_client.get()
                    
                    # Always calculate and update price labels
                    tarp_price, tarp_error = self.calculate_roof_price("Tarp", roof_area, storey, client)
                    replace_price, replace_error = self.calculate_roof_price("Replace", roof_area, storey, client)

                    if hasattr(self, 'tarp_price_label') and self.tarp_price_label.winfo_exists():
                        self.tarp_price_label.config(text=f"${tarp_price:.2f}" if not tarp_error else tarp_error)
                    if hasattr(self, 'replacement_price_label') and self.replacement_price_label.winfo_exists():
                        self.replacement_price_label.config(text=f"${replace_price:.2f}" if not replace_error else replace_error)
                    
                    # Only generate bid text if there's valid input
                    if roof_area > 0:

                        replace_bid_template = (
                            "Remove and replace approximately {roof_area} SF Roof. Includes removal and replacement of {roof_area} SF asphalt shingles, "
                            "removal and replacement of {roof_area} SF area of felt, removal and replacement of {edge_metal} LF of edge metal, "
                            "removal and replacement of {ice_shield} SF of ice and water shield, removal and replacement of {flashing} LF of flashing, "
                            "removal and replacement of {ridge_cap} LF ridge cap, {roof_jack} roof jack. Permit will be pulled an invoiced if needed. "
                            "If additional damage is found in the roof decking, $175.00 will be needed for each 32 SF of decking* May take 5-6 weeks to complete. "
                            "Price includes time, labor, materials and the removal of the generated debris.\nPrice: ${price:.2f}"
                        )
                        
                        tarp_bid_template = (
                            "Install heavy duty brown/black {roof_area} SF tarp on a leaking roof. The tarp must be secured with furring strips around the perimeter and slope of the roof. "
                            "Secure the tarp with an adequate number of furring strips throughout the roof to hold the tarp during heavy wind. "
                            "*Note: This is a temporary solution only, roof replacement is recommended.\nPrice: ${price:.2f}"
                        )

                        roof_bid = replace_bid_template.format(
                            roof_area=int(roof_area),
                            edge_metal=int(edge_metal),
                            ice_shield=int(0.2 * roof_area),
                            flashing=int(0.15 * roof_area),
                            ridge_cap=int(ridge_cap),
                            roof_jack=int(roof_jack),
                            price=replace_price
                        ) + "\n\n" + tarp_bid_template.format(
                            roof_area=int(roof_area),
                            price=tarp_price
                        )
                        bid_parts.append(("ROOFING", roof_bid))
            except Exception as e:
                pass

            # Display combined bids
            if bid_parts:
                combined_bid = "\n\n".join([f"=== {title} ===\n{content}" for title, content in bid_parts])
                self.generated_bid_text.insert("1.0", combined_bid)
            else:
                self.generated_bid_text.insert("1.0", "Enter details to generate bid...")
        except Exception as e:
            # Only show error if UI elements exist
            if hasattr(self, 'generated_bid_text') and self.generated_bid_text.winfo_exists():
                messagebox.showerror("Error", f"An unexpected error occurred during bid generation: {e}")
                self.generated_bid_text.delete("1.0", tk.END)
                self.generated_bid_text.insert("1.0", f"Error: {e}")

    def generate_bids(self):
        # Simply update the bid display - no popup needed
        # The bid is already displayed in the right side section via live_update_bid
        self.live_update_bid()

    def clear_bids(self):
        self.grass_height_entry.delete(0, tk.END); self.grass_height_entry.insert(0, "0")
        self.maintainable_lot_entry.delete(0, tk.END); self.maintainable_lot_entry.insert(0, "0")
        self.total_lot_entry.delete(0, tk.END); self.total_lot_entry.insert(0, "0")
        self.disclaimer_text.delete("1.0", tk.END)
        self.gc_calculated_price_label.config(text="$0.00")
        self.roof_area_entry.delete(0, tk.END); self.roof_area_entry.insert(0, "0")
        self.edge_metal_entry.delete(0, tk.END); self.edge_metal_entry.insert(0, "0")
        self.ridge_cap_entry.delete(0, tk.END); self.ridge_cap_entry.insert(0, "0")
        self.roof_jack_entry.delete(0, tk.END); self.roof_jack_entry.insert(0, "0")
        self.tarp_price_label.config(text="$0.00")
        self.replacement_price_label.config(text="$0.00")
        self.generated_bid_text.delete("1.0", tk.END); self.generated_bid_text.insert("1.0", "Enter details to generate bid...")
    
    def clear_stairs_rail_bids(self):
        """Clear all Stairs and Rail bid template fields"""
        try:
            if hasattr(self, 'stair_count_entry') and self.stair_count_entry.winfo_exists():
                self.stair_count_entry.delete(0, tk.END)
                self.stair_count_entry.insert(0, "0")
                self.step_width_entry.delete(0, tk.END)
                self.step_width_entry.insert(0, "0")
                self.staircase_location_entry.delete(0, tk.END)
                if hasattr(self, 'staircase_price_label'):
                    self.staircase_price_label.config(text="$0.00")
                if hasattr(self, 'staircase_calc_label'):
                    self.staircase_calc_label.config(text="")
            
            if hasattr(self, 'handrail_lf_entry') and self.handrail_lf_entry.winfo_exists():
                self.handrail_lf_entry.delete(0, tk.END)
                self.handrail_lf_entry.insert(0, "0")
                self.handrail_location_entry.delete(0, tk.END)
                if hasattr(self, 'handrail_price_label'):
                    self.handrail_price_label.config(text="$0.00")
                if hasattr(self, 'handrail_calc_label'):
                    self.handrail_calc_label.config(text="")
            
            if hasattr(self, 'guardrail_lf_entry') and self.guardrail_lf_entry.winfo_exists():
                self.guardrail_lf_entry.delete(0, tk.END)
                self.guardrail_lf_entry.insert(0, "0")
                self.guardrail_location_entry.delete(0, tk.END)
                if hasattr(self, 'guardrail_price_label'):
                    self.guardrail_price_label.config(text="$0.00")
                if hasattr(self, 'guardrail_calc_label'):
                    self.guardrail_calc_label.config(text="")
            
            self.live_update_bid()
        except Exception as e:
            pass
    
    def clear_fence_bids(self):
        """Clear all Fence bid template fields"""
        try:
            if hasattr(self, 'fence_lf_entry') and self.fence_lf_entry.winfo_exists():
                self.fence_lf_entry.delete(0, tk.END)
                self.fence_lf_entry.insert(0, "0")
                self.fence_location_entry.delete(0, tk.END)
                if hasattr(self, 'fence_price_label'):
                    self.fence_price_label.config(text="$0.00")
                if hasattr(self, 'fence_calc_label'):
                    self.fence_calc_label.config(text="")
            
            self.live_update_bid()
        except Exception as e:
            pass