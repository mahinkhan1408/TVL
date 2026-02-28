# client_allowables_module.py
import tkinter as tk
from tkinter import messagebox
import requests
import csv
import io
import re

class ClientAllowablesModule:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Allowables")
        self.root.geometry("800x600")  # Standard window size (matching Vendor Price)
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
            'text_primary': '#212529',
            'category_header_bg': '#e6d5b8',  # Light orange/brown for category headers (matching image)
            'item_row_bg_even': '#ffffff',  # White for even rows
            'item_row_bg_odd': '#f9f9f9'  # Very light gray for odd rows
        }

        # Module Title
        self.module_title_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=60)
        self.module_title_frame.pack(fill='x', pady=(0, 10))
        self.module_title_frame.pack_propagate(False)
        
        tk.Label(self.module_title_frame, text="Client Allowables", 
                 font=("Arial", 18, "bold"), fg='white', 
                 bg=self.colors['primary_blue']).pack(side="left", padx=20)
        
        self.refresh_button = tk.Button(self.module_title_frame, text="Refresh Prices",
                                        font=("Arial", 10, "bold"), bg=self.colors['light_blue'], 
                                        fg="white", relief="flat", cursor="hand2",
                                        activebackground=self.colors['primary_blue'],
                                        command=self.refresh_prices)
        self.refresh_button.pack(side="right", padx=(0, 20))

        # Search/Filter Frame - Improved Design
        self.filter_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 10))

        # Modern search container with rounded appearance
        search_container = tk.Frame(self.filter_frame, bg=self.colors['white'], relief="solid", bd=1)
        search_container.pack(fill="x", padx=0, pady=0)
        
        # Search icon label (using text as icon)
        search_icon_label = tk.Label(search_container, text="🔍", font=("Arial", 14), 
                                     bg=self.colors['white'], fg=self.colors['gray_medium'])
        search_icon_label.pack(side="left", padx=(12, 8), pady=8)
        
        # Search entry with placeholder functionality
        self.search_entry = tk.Entry(search_container, font=("Arial", 12), 
                                     bg=self.colors['white'], fg=self.colors['text_primary'],
                                     relief="flat", bd=0, width=50)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        self.search_entry.insert(0, "Search items...")
        self.search_entry.config(fg=self.colors['gray_medium'])
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        
        # Clear button (X) - appears when there's text
        self.clear_button = tk.Button(search_container, text="✕", font=("Arial", 10, "bold"),
                                      bg=self.colors['white'], fg=self.colors['gray_medium'],
                                      relief="flat", bd=0, cursor="hand2", width=2,
                                      command=self.clear_search, state="disabled")
        self.clear_button.pack(side="right", padx=(0, 8), pady=8)

        # Bind Ctrl+F and F3 to open/focus the search box
        try:
            self.root.bind_all('<Control-f>', self.open_search)
            self.root.bind_all('<Control-F>', self.open_search)
            self.root.bind_all('<F3>', self.open_search)
        except Exception:
            pass

        # Price List Content Frame (with scrollbar) - matching Vendor Price layout
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

        # Bind mouse wheel scrolling
        self._bind_mousewheel_global()

        # Data URL
        self.data_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBOgCE9etWQ6ndxE7G7HTx7R8LIAqQ4ipMB3dKh0IuGs-XaSalP_1ptaBi13s2HeLTYhW7CKPxy4cL/pub?gid=0&single=true&output=csv"
        self.all_data = {}
        
        # Search debouncing
        self._search_after_id = None
        self._debounce_delay = 300  # milliseconds
        
        self.load_prices()


    def refresh_prices(self):
        self.load_prices()
        messagebox.showinfo("Refresh Complete", "Client Allowables have been refreshed successfully.")

    def _parse_csv_data(self, url, data_dict):
        """Parse CSV data from URL and populate data dictionary."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)

            # Normalize header names
            header_map = {fn.strip().lower(): fn for fn in (reader.fieldnames or [])}

            # Detect column keys
            category_key = None
            item_key = None
            price_key = None
            unit_key = None
            unit_qty_key = None

            for n in header_map:
                if n in ('category', 'cat'):
                    category_key = header_map[n]
                if n in ('item description', 'item', 'description', 'line item', 'line_item'):
                    item_key = header_map[n]
                if n.startswith('unit price') or ('unit' in n and 'price' in n):
                    price_key = header_map[n]
                elif n.startswith('price') or 'price' in n:
                    price_key = header_map[n]
                if n in ('uom', 'unit of measure', 'unit'):
                    unit_key = header_map[n]
                if n in ('unit qty', 'unit qty.', 'quantity', 'qty'):
                    unit_qty_key = header_map[n]

            # Fallback to capitalized defaults
            if not category_key and 'Category' in (reader.fieldnames or []):
                category_key = 'Category'
            if not item_key and 'Item Description' in (reader.fieldnames or []):
                item_key = 'Item Description'
            if not price_key and 'Unit Price' in (reader.fieldnames or []):
                price_key = 'Unit Price'
            if not unit_key and 'UOM' in (reader.fieldnames or []):
                unit_key = 'UOM'
            if not unit_qty_key and 'Unit Qty' in (reader.fieldnames or []):
                unit_qty_key = 'Unit Qty'

            for row in reader:
                if not (category_key and item_key and price_key):
                    continue

                raw_category = row.get(category_key, '')
                raw_item = row.get(item_key, '')
                raw_price = row.get(price_key, '')
                raw_unit = row.get(unit_key, '') if unit_key else ''
                raw_unit_qty = row.get(unit_qty_key, '') if unit_qty_key else '1'

                category = raw_category.strip() if raw_category else ''
                item_name = raw_item.strip() if raw_item else ''
                price_str = raw_price.strip() if raw_price else ''
                unit = raw_unit.strip() if raw_unit else ''
                unit_qty = raw_unit_qty.strip() if raw_unit_qty else '1'

                # Skip empty rows
                if not category and not item_name:
                    continue

                # Clean price string
                cleaned = price_str.replace('\u00A0', '').strip()
                if ',' in cleaned and '.' in cleaned:
                    cleaned = cleaned.replace(',', '')
                elif ',' in cleaned and '.' not in cleaned:
                    cleaned = cleaned.replace(',', '.')

                cleaned_price_str = re.sub(r"[^0-9.\-]", '', cleaned)

                try:
                    if cleaned_price_str in ('', '.', '-', None):
                        raise ValueError('empty')
                    price = float(cleaned_price_str)
                except (ValueError, TypeError):
                    price = "N/A"
                    print(f"Warning: Could not parse price for item '{item_name}'. Raw value was: '{price_str}'")

                # Total is just the Unit Price (Unit Qty is typically 1)
                # Store both for display
                if category not in data_dict:
                    data_dict[category] = []
                data_dict[category].append({
                    'item': item_name,
                    'uom': unit,
                    'unit_qty': unit_qty,
                    'unit_price': price,
                    'total': price  # Total is the Unit Price
                })
            
            return True
        except requests.exceptions.RequestException as e:
            print(f"Network error loading data from {url}: {e}")
            return False
        except Exception as e:
            print(f"Error parsing data from {url}: {e}")
            return False

    def load_prices(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.all_data = {}

        # Load data
        success = self._parse_csv_data(self.data_url, self.all_data)
        if not success:
            self.display_error_message(self.scrollable_frame, "Network Error", 
                                     "Failed to load client allowables due to network issues.")
            return

        # Display data
        self.display_prices(self.all_data)

    def display_prices(self, data_to_display):
        """Display prices in categorized sections matching the image format."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not data_to_display:
            tk.Label(self.scrollable_frame, text="No items found.",
                     font=("Arial", 12), bg=self.colors['white'], fg=self.colors['gray_medium']).pack(pady=20)
            return

        # Calculate column widths across all categories
        all_items = []
        all_uoms = []
        all_units = []
        all_totals = []
        
        for items in data_to_display.values():
            for it in items:
                all_items.append(it.get('item', '') or '')
                all_uoms.append(it.get('uom', '') or '')
                all_units.append(str(it.get('unit_qty', '')) or '')
                total_val = it.get('total', '')
                if isinstance(total_val, float):
                    all_totals.append(f"${total_val:,.2f}")
                else:
                    all_totals.append(str(total_val) or '')

        if not all_items:
            all_items = ['Item Description']
        if not all_uoms:
            all_uoms = ['UOM']
        if not all_units:
            all_units = ['Unit']
        if not all_totals:
            all_totals = ['Total']

        # Approximate character width (7 px per char for Arial 11)
        char_px = 7
        padding_px = 24

        max_item_chars = max(len(s) for s in all_items)
        max_uom_chars = max(len(s) for s in all_uoms)
        max_unit_chars = max(len(s) for s in all_units)
        max_total_chars = max(len(s) for s in all_totals)

        # Column widths - matching Vendor Price calculation
        col0_px = max(200, int(max_item_chars * char_px) + padding_px)
        col1_px = max(80, int(max_uom_chars * char_px) + padding_px)
        col2_px = max(80, int(max_unit_chars * char_px) + padding_px)
        col3_px = max(100, int(max_total_chars * char_px) + padding_px)

        # Display each category
        for category, items in data_to_display.items():
            # Category header - matching Vendor Price style
            category_frame = tk.Frame(self.scrollable_frame, bg=self.colors['category_header_bg'], bd=1, relief="solid")
            category_frame.pack(fill="x", padx=5, pady=(10, 6))
            tk.Label(category_frame, text=category, font=("Arial", 14, "bold"), 
                     bg=self.colors['category_header_bg'], fg=self.colors['primary_blue'], 
                     anchor="w", padx=8, pady=6).pack(fill='x')

            # Table frame for this category
            table_frame = tk.Frame(self.scrollable_frame, bg=self.colors['white'])
            table_frame.pack(fill="x", padx=5, pady=(0, 8))
            
            # Set consistent column widths
            table_frame.columnconfigure(0, minsize=col0_px)
            table_frame.columnconfigure(1, minsize=col1_px)
            table_frame.columnconfigure(2, minsize=col2_px)
            table_frame.columnconfigure(3, minsize=col3_px)

            # Header row with borders - matching Vendor Price style
            tk.Label(table_frame, text="Item Description", font=("Arial", 11, "bold"), 
                    bg=self.colors['gray_light'], fg=self.colors['gray_dark'], 
                    bd=1, relief='solid').grid(row=0, column=0, sticky='nsew')
            tk.Label(table_frame, text="UOM", font=("Arial", 11, "bold"), 
                    bg=self.colors['gray_light'], fg=self.colors['gray_dark'], 
                    bd=1, relief='solid').grid(row=0, column=1, sticky='nsew')
            tk.Label(table_frame, text="Unit", font=("Arial", 11, "bold"), 
                    bg=self.colors['gray_light'], fg=self.colors['gray_dark'], 
                    bd=1, relief='solid').grid(row=0, column=2, sticky='nsew')
            tk.Label(table_frame, text="Total", font=("Arial", 11, "bold"), 
                    bg=self.colors['gray_light'], fg=self.colors['gray_dark'], 
                    bd=1, relief='solid').grid(row=0, column=3, sticky='nsew')

            # Data rows - using Labels like Vendor Price
            for i, item_data in enumerate(items):
                row_bg = self.colors['item_row_bg_even'] if i % 2 == 0 else self.colors['item_row_bg_odd']

                # Item Description cell
                li = tk.Label(table_frame, text=item_data['item'], font=("Arial", 11), 
                            bg=row_bg, fg=self.colors['gray_dark'], bd=1, relief='solid', 
                            anchor='w', padx=6)
                li.grid(row=i+1, column=0, sticky='nsew')

                # UOM cell
                uom_text = item_data.get('uom', '') if item_data.get('uom') else ''
                uom = tk.Label(table_frame, text=uom_text, font=("Arial", 11), 
                             bg=row_bg, fg=self.colors['gray_medium'], bd=1, relief='solid', 
                             anchor='center')
                uom.grid(row=i+1, column=1, sticky='nsew')

                # Unit cell
                unit_text = str(item_data.get('unit_qty', '')) if item_data.get('unit_qty') else ''
                unit = tk.Label(table_frame, text=unit_text, font=("Arial", 11), 
                              bg=row_bg, fg=self.colors['gray_medium'], bd=1, relief='solid', 
                              anchor='center')
                unit.grid(row=i+1, column=2, sticky='nsew')

                # Total cell (right-aligned, bold, green)
                total_val = item_data.get('total', '')
                if isinstance(total_val, float):
                    total_display = f"${total_val:,.2f}"
                else:
                    total_display = str(total_val)
                total = tk.Label(table_frame, text=total_display, font=("Arial", 11, "bold"), 
                               bg=row_bg, fg=self.colors['green'], bd=1, relief='solid', 
                               anchor='e')
                total.grid(row=i+1, column=3, sticky='nsew')

    def _on_search_key_release(self, event=None):
        """Handle search key release with debouncing."""
        # Cancel existing scheduled filter
        if self._search_after_id:
            self.root.after_cancel(self._search_after_id)
            self._search_after_id = None
        
        # Update clear button state immediately
        search_text = self.search_entry.get().strip()
        if search_text and search_text != "Search items...":
            self.clear_button.config(state="normal")
        else:
            self.clear_button.config(state="disabled")
            # If search is empty, immediately show all data (no debounce needed)
            if not search_text or search_text == "Search items...":
                self.filter_prices()
                return
        
        # Schedule filter after debounce delay
        self._search_after_id = self.root.after(self._debounce_delay, self._execute_filter)
    
    def _execute_filter(self):
        """Execute the filter (called after debounce delay)."""
        self._search_after_id = None
        self.filter_prices()

    def filter_prices(self, event=None):
        """Filter prices based on search term."""
        # Cancel any pending debounce when manually calling filter
        if self._search_after_id:
            self.root.after_cancel(self._search_after_id)
            self._search_after_id = None
        
        search_text = self.search_entry.get().strip()
        search_term = search_text.lower() if search_text and search_text != "Search items..." else ""
        
        # Always clear the display first to avoid sticky results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not search_term:
            # Show all data
            self.display_prices(self.all_data)
            return

        # Filter data
        filtered_data = {}
        for category, items in self.all_data.items():
            filtered_items = []
            for item_data in items:
                # Search in item description
                if search_term in item_data['item'].lower():
                    filtered_items.append(item_data)
                # Also search in category name
                elif search_term in category.lower():
                    filtered_items.append(item_data)
            
            if filtered_items:
                filtered_data[category] = filtered_items
        
        # Display filtered results
        if filtered_data:
            self.display_prices(filtered_data)
        else:
            tk.Label(self.scrollable_frame, text="No items found matching your search.",
                     font=("Arial", 12), bg=self.colors['white'], fg=self.colors['gray_medium']).pack(pady=20)

    def _on_search_focus_in(self, event):
        """Handle search entry focus in."""
        if self.search_entry.get() == "Search items...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=self.colors['text_primary'])

    def _on_search_focus_out(self, event):
        """Handle search entry focus out."""
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Search items...")
            self.search_entry.config(fg=self.colors['gray_medium'])
            self.clear_button.config(state="disabled")
        else:
            self.clear_button.config(state="normal")

    def clear_search(self):
        """Clear the search entry and reset the display."""
        # Cancel any pending debounce
        if self._search_after_id:
            self.root.after_cancel(self._search_after_id)
            self._search_after_id = None
        
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Search items...")
        self.search_entry.config(fg=self.colors['gray_medium'])
        self.clear_button.config(state="disabled")
        # Immediately show all data without debounce
        self.filter_prices()

    def open_search(self, event=None):
        """Focus the search entry."""
        try:
            self.search_entry.focus_set()
            if self.search_entry.get() == "Search items...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(fg=self.colors['text_primary'])
            else:
                self.search_entry.selection_range(0, 'end')
        except Exception:
            pass

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        try:
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return
        except Exception:
            pass

        if hasattr(event, 'num'):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _bind_mousewheel_global(self):
        """Bind mouse wheel scrolling to the entire window."""
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)
        
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-5>", self._on_mousewheel)


    def display_error_message(self, scrollable_frame, title, message):
        """Display error message."""
        error_frame = tk.Frame(scrollable_frame, bg="#f8d7da", bd=2, relief="groove", padx=15, pady=10)
        error_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(error_frame, text=title, font=("Arial", 14, "bold"), fg="#721c24", bg="#f8d7da").pack(fill="x")
        tk.Label(error_frame, text=message, font=("Arial", 11), fg="#721c24", bg="#f8d7da").pack(fill="x", pady=(5,0))
