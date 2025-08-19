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
        self.search_entry = tk.Entry(self.filter_frame, font=("Arial", 10), width=30, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_prices)

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

            for row in reader:
                if 'Category' in row and 'Item' in row and 'Price' in row:
                    category = row['Category'].strip()
                    item_name = row['Item'].strip()
                    price_str = row['Price'].strip()
                    
                    # --- BEGIN DATA CLEANING LOGIC ---
                    # Remove any non-numeric characters except for a dot, and handle empty strings
                    cleaned_price_str = re.sub(r'[^\d.]', '', price_str)
                    
                    try:
                        price = float(cleaned_price_str)
                    except (ValueError, TypeError):
                        # If conversion fails, default to 0.0 or a descriptive string
                        price = "N/A"
                        # Print an error message to the console for debugging
                        print(f"Warning: Could not parse price for item '{item_name}'. Raw value was: '{price_str}'")
                    # --- END DATA CLEANING LOGIC ---

                    if category not in self.all_vendor_data:
                        self.all_vendor_data[category] = []
                    self.all_vendor_data[category].append({'item': item_name, 'price': price})
            
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

        row_counter = 0
        for category, items in data_to_display.items():
            category_frame = tk.Frame(self.scrollable_frame, bg=self.colors['category_header_bg'], bd=1, relief="solid")
            category_frame.pack(fill="x", padx=5, pady=(10, 2))
            tk.Label(category_frame, text=category, font=("Arial", 13, "bold"), 
                     bg=self.colors['category_header_bg'], fg=self.colors['primary_blue'], anchor="w").pack(padx=10, pady=5)
            
            for i, item_data in enumerate(items):
                bg_color = self.colors['item_row_bg_even'] if i % 2 == 0 else self.colors['item_row_bg_odd']
                item_frame = tk.Frame(self.scrollable_frame, bg=bg_color, bd=1, relief="solid")
                item_frame.pack(fill="x", padx=5, pady=0)

                tk.Label(item_frame, text=item_data['item'], font=("Arial", 10), 
                         bg=bg_color, fg=self.colors['gray_dark'], anchor="w").pack(side="left", padx=10, pady=5, expand=True, fill="x")
                
                # Display price, handling non-numeric values
                price_display = f"${item_data['price']:.2f}" if isinstance(item_data['price'], float) else str(item_data['price'])
                tk.Label(item_frame, text=price_display, font=("Arial", 10, "bold"), 
                         bg=bg_color, fg=self.colors['green'], anchor="e").pack(side="right", padx=10, pady=5)
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

    def display_error_message(self, title, message):
        error_frame = tk.Frame(self.scrollable_frame, bg="#f8d7da", bd=2, relief="groove", padx=15, pady=10)
        error_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(error_frame, text=title, font=("Arial", 14, "bold"), fg="#721c24", bg="#f8d7da").pack(fill="x")
        tk.Label(error_frame, text=message, font=("Arial", 11), fg="#721c24", bg="#f8d7da").pack(fill="x", pady=(5,0))