# vendor_price_module.py
import tkinter as tk
from tkinter import messagebox
import requests
import csv
import io
import re

class VendorPriceModule:
    def __init__(self, root):
        self.root = root
        self.root.title("Vendor Price List")
        self.root.geometry("800x600")
        self.root.configure(bg='#f8f9fa') # Light gray background

        self.colors = {
            'primary_blue': '#1e3a5f',
            'light_blue': '#3498db',
            'background': '#f8f9fa',
            'white': '#ffffff',
            'gray_light': '#e9ecef',
            'gray_medium': '#6c757d',
            'gray_dark': '#495057',
            'green': '#28a745',
            'category_header_bg': '#d1ecf1', # Light blue for category headers
            'item_row_bg_even': '#f0f8ff', # Alice blue for even rows
            'item_row_bg_odd': '#ffffff' # White for odd rows
        }

        # Module Title
        self.module_title_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=60)
        self.module_title_frame.pack(fill='x', pady=(0, 10))
        self.module_title_frame.pack_propagate(False)
        
        tk.Label(self.module_title_frame, text="Vendor Price List", 
                 font=("Arial", 18, "bold"), fg='white', 
                 bg=self.colors['primary_blue']).pack(side="left", padx=20)
        
        self.refresh_button = tk.Button(self.module_title_frame, text="Refresh Prices",
                                        font=("Arial", 10, "bold"), bg=self.colors['light_blue'], 
                                        fg="white", relief="flat", cursor="hand2",
                                        activebackground=self.colors['primary_blue'],
                                        command=self.refresh_prices)
        self.refresh_button.pack(side="right", padx=(0, 20))

        # Search/Filter Frame
        self.filter_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 10))

        tk.Label(self.filter_frame, text="Search Item:", font=("Arial", 10), bg=self.colors['background']).pack(side="left", padx=(0, 5))
        # make the search bar bigger per request
        self.search_entry = tk.Entry(self.filter_frame, font=("Arial", 12), width=50, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_prices)

        # Bind Ctrl+F and F3 to open/focus the search box for quick searching
        # Use bind_all so it works regardless of which widget currently has focus
        try:
            self.root.bind_all('<Control-f>', self.open_search)
            self.root.bind_all('<Control-F>', self.open_search)
            self.root.bind_all('<F3>', self.open_search)
        except Exception:
            # ignore if binding fails for some reason
            pass

        # Price List Content Frame (with scrollbar)
        self.canvas_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors['white'], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['white'])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # bind mouse wheel scrolling when cursor is over the canvas
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        self.vendor_data_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQv3sHuJQ_wjPViqn8-b3pNz8QBH_l-wAllPa-RhCZ8Vlaf9bRltG-WguziYKYn1SMj4D3snIZfn-9w/pub?output=csv" 
        self.all_vendor_data = {}
        self.load_prices()

    def refresh_prices(self):
        self.load_prices()
        messagebox.showinfo("Refresh Complete", "Vendor price list has been refreshed successfully.")

    def load_prices(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.all_vendor_data = {}

        try:
            response = requests.get(self.vendor_data_url, timeout=10)
            response.raise_for_status()
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)

            # Normalize header names to be more flexible (accept 'Price ($)', lower/upper case, etc.)
            if reader.fieldnames:
                normalized = [fn.strip().lower() for fn in reader.fieldnames]
            else:
                normalized = []

            # build a mapping from normalized name -> original header
            header_map = {fn.strip().lower(): fn for fn in (reader.fieldnames or [])}

            # possible header keys
            category_key = None
            item_key = None
            price_key = None
            unit_key = None

            for n in header_map:
                if n in ('category', 'cat'):
                    category_key = header_map[n]
                if n in ('item', 'item name', 'description', 'line item', 'line_item'):
                    item_key = header_map[n]
                if n.startswith('price') or 'price' in n:
                    price_key = header_map[n]
                if n in ('unit', 'units', 'uom', 'measure'):
                    unit_key = header_map[n]

            # fallback: try capitalized defaults if mapping not found
            if not category_key and 'Category' in (reader.fieldnames or []):
                category_key = 'Category'
            if not item_key and 'Item' in (reader.fieldnames or []):
                item_key = 'Item'
            if not price_key and 'Price' in (reader.fieldnames or []):
                price_key = 'Price'
            if not unit_key and 'Unit' in (reader.fieldnames or []):
                unit_key = 'Unit'

            for row in reader:
                # ensure keys exist in row
                if not (category_key and item_key and price_key):
                    # skip rows if we couldn't detect headers
                    continue

                raw_category = row.get(category_key, '')
                raw_item = row.get(item_key, '')
                raw_price = row.get(price_key, '')
                raw_unit = row.get(unit_key, '') if unit_key else ''

                category = raw_category.strip() if raw_category is not None else ''
                item_name = raw_item.strip() if raw_item is not None else ''
                price_str = raw_price.strip() if raw_price is not None else ''
                unit = raw_unit.strip() if raw_unit is not None else ''

                # --- BEGIN DATA CLEANING LOGIC ---
                # Remove currency symbols, commas, parentheses and any characters except digits and dot
                # Handle values like "$1,234.56", "1.234,56" (decimal comma) or "(1,234.56)"
                # First convert common decimal-comma format to dot when there are both commas and dots
                cleaned = price_str.replace('\u00A0', '').strip()  # remove non-breaking spaces
                # if string contains ',' and '.' and the last ',' occurs before the last '.', assume standard thousands commas
                if ',' in cleaned and '.' in cleaned:
                    # remove commas
                    cleaned = cleaned.replace(',', '')
                else:
                    # if contains comma but no dot, treat comma as decimal separator
                    if ',' in cleaned and '.' not in cleaned:
                        cleaned = cleaned.replace(',', '.')

                # remove currency symbols, parentheses and other non-digit/dot/hyphen
                cleaned_price_str = re.sub(r"[^0-9.\-]", '', cleaned)

                try:
                    # handle negative prices in parentheses or with leading '-'
                    if cleaned_price_str in ('', '.', '-', None):
                        raise ValueError('empty')
                    price = float(cleaned_price_str)
                except (ValueError, TypeError):
                    price = "N/A"
                    print(f"Warning: Could not parse price for item '{item_name}'. Raw value was: '{price_str}'")
                # --- END DATA CLEANING LOGIC ---

                if category not in self.all_vendor_data:
                    self.all_vendor_data[category] = []
                self.all_vendor_data[category].append({'item': item_name, 'price': price, 'unit': unit})
            
            self.display_prices(self.all_vendor_data)

        except requests.exceptions.RequestException as e:
            messagebox.showwarning("Network Error", f"Could not load vendor prices from online. Please check internet connection.\nError: {e}")
            self.display_error_message("Network Error", "Failed to load vendor prices due to network issues.")
        except Exception as e:
            messagebox.showwarning("Error", f"Failed to parse vendor price data.\nError: {e}")
            self.display_error_message("Data Error", "Failed to load vendor prices due to data parsing issues.")

    def display_prices(self, data_to_display):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not data_to_display:
            tk.Label(self.scrollable_frame, text="No items found matching your search.",
                     font=("Arial", 12), bg=self.colors['white'], fg=self.colors['gray_medium']).pack(pady=20)
            return

        # Calculate global column widths (in characters) across all categories so columns align vertically
        all_items = []
        all_prices = []
        all_units = []
        for items in data_to_display.values():
            for it in items:
                all_items.append(it.get('item', '') or '')
                price_str = f"${it['price']:.2f}" if isinstance(it.get('price'), float) else str(it.get('price') or '')
                all_prices.append(price_str)
                all_units.append(it.get('unit', '') or '')

        # fallback if empty
        if not all_items:
            all_items = ['Line Item']
        if not all_prices:
            all_prices = ['Price']
        if not all_units:
            all_units = ['Unit']

        # approximate character width in pixels for the chosen font (Arial 11) — estimate 7 px per char
        char_px = 7
        padding_px = 24

        max_item_chars = max(len(s) for s in all_items)
        max_price_chars = max(len(s) for s in all_prices)
        max_unit_chars = max(len(s) for s in all_units)

        col0_px = max(200, int(max_item_chars * char_px) + padding_px)
        col1_px = max(80, int(max_price_chars * char_px) + padding_px)
        col2_px = max(80, int(max_unit_chars * char_px) + padding_px)

        row_counter = 0
        for category, items in data_to_display.items():
            # Category header
            category_frame = tk.Frame(self.scrollable_frame, bg=self.colors['category_header_bg'], bd=1, relief="solid")
            category_frame.pack(fill="x", padx=5, pady=(10, 6))
            tk.Label(category_frame, text=category, font=("Arial", 14, "bold"), 
                     bg=self.colors['category_header_bg'], fg=self.colors['primary_blue'], anchor="w", padx=8, pady=6).pack(fill='x')

            # Table frame for this category: use grid so columns align consistently per section
            table_frame = tk.Frame(self.scrollable_frame, bg=self.colors['white'])
            table_frame.pack(fill="x", padx=5, pady=(0, 8))
            # Set consistent minsize per column so columns align across sections
            table_frame.columnconfigure(0, minsize=col0_px)
            table_frame.columnconfigure(1, minsize=col1_px)
            table_frame.columnconfigure(2, minsize=col2_px)

            # Header row with borders
            tk.Label(table_frame, text="Line Item", font=("Arial", 11, "bold"), bg=self.colors['gray_light'], fg=self.colors['gray_dark'], bd=1, relief='solid').grid(row=0, column=0, sticky='nsew')
            tk.Label(table_frame, text="Price", font=("Arial", 11, "bold"), bg=self.colors['gray_light'], fg=self.colors['gray_dark'], bd=1, relief='solid').grid(row=0, column=1, sticky='nsew')
            tk.Label(table_frame, text="Unit", font=("Arial", 11, "bold"), bg=self.colors['gray_light'], fg=self.colors['gray_dark'], bd=1, relief='solid').grid(row=0, column=2, sticky='nsew')

            for i, item_data in enumerate(items):
                row_bg = self.colors['item_row_bg_even'] if i % 2 == 0 else self.colors['item_row_bg_odd']

                # Line Item cell
                li = tk.Label(table_frame, text=item_data['item'], font=("Arial", 11), bg=row_bg, fg=self.colors['gray_dark'], bd=1, relief='solid', anchor='w', padx=6)
                li.grid(row=i+1, column=0, sticky='nsew')

                # Price cell (right-aligned)
                price_display = f"${item_data['price']:.2f}" if isinstance(item_data['price'], float) else str(item_data['price'])
                p = tk.Label(table_frame, text=price_display, font=("Arial", 11, "bold"), bg=row_bg, fg=self.colors['green'], bd=1, relief='solid', anchor='e')
                p.grid(row=i+1, column=1, sticky='nsew')

                # Unit cell
                unit_text = item_data.get('unit', '') if item_data.get('unit') else ''
                u = tk.Label(table_frame, text=unit_text, font=("Arial", 11), bg=row_bg, fg=self.colors['gray_medium'], bd=1, relief='solid', anchor='center')
                u.grid(row=i+1, column=2, sticky='nsew')

                row_counter += 1

    def filter_prices(self, event=None):
        search_term = self.search_entry.get().strip().lower()
        filtered_data = {}

        if not search_term:
            self.display_prices(self.all_vendor_data)
            return

        for category, items in self.all_vendor_data.items():
            for item_data in items:
                if search_term in item_data['item'].lower():
                    if category not in filtered_data:
                        filtered_data[category] = []
                    filtered_data[category].append(item_data)
        
        self.display_prices(filtered_data)

    def open_search(self, event=None):
        """Focus the search entry and select its contents so the user can type immediately.

        Bound to Ctrl+F and F3.
        """
        try:
            self.search_entry.focus_set()
            # select all text for immediate replacement
            self.search_entry.selection_range(0, 'end')
        except Exception:
            pass

    # Mouse wheel binding helpers for cross-platform scrolling when cursor is over the canvas
    def _on_mousewheel(self, event):
        # Windows and macOS: event.delta (positive/negative), Linux may use Button-4/5
        try:
            if event.delta:
                # On Windows, delta is multiple of 120
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return
        except Exception:
            pass

        # Linux scroll events
        if hasattr(event, 'num'):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _bind_mousewheel(self, event=None):
        # bind both the modern MouseWheel and the older Button-4/5 events
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    def display_error_message(self, title, message):
        error_frame = tk.Frame(self.scrollable_frame, bg="#f8d7da", bd=2, relief="groove", padx=15, pady=10)
        error_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(error_frame, text=title, font=("Arial", 14, "bold"), fg="#721c24", bg="#f8d7da").pack(fill="x")
        tk.Label(error_frame, text=message, font=("Arial", 11), fg="#721c24", bg="#f8d7da").pack(fill="x", pady=(5,0))