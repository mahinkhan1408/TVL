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
        self.root.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.7)}")
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
        
        self.load_all_pricing_data()
        
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

        self.notebook = ttk.Notebook(self.main_content_frame)
        self.notebook.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.gc_tab = tk.Frame(self.notebook, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        self.roof_tab = tk.Frame(self.notebook, bg=self.colors['white'], padx=15, pady=15, bd=1, relief="solid")
        
        self.notebook.add(self.gc_tab, text='  Grass Cut  ')
        self.notebook.add(self.roof_tab, text='  Roofing  ')

        self.build_gc_frame(self.gc_tab)
        self.build_roof_frame(self.roof_tab)

        self.output_frame = tk.Frame(self.main_content_frame, bg=self.colors['output_bg'], bd=1, relief="solid")
        self.output_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.output_frame, text="Generated Bid:", font=("Arial", 12, "bold"), 
                 bg=self.colors['output_bg'], fg=self.colors['primary_blue']).pack(pady=(10, 5), padx=10, anchor="w")
        
        self.generated_bid_text = tk.Text(self.output_frame, font=("Arial", 11), bg=self.colors['white'], 
                                          wrap=tk.WORD, relief="flat", padx=10, pady=10)
        self.generated_bid_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

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
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        self.live_update_bid()

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

    def live_update_bid(self, event=None):
        try:
            if not hasattr(self, 'notebook') or not self.notebook.winfo_exists() or not self.notebook.select(): return
            active_tab_text = self.notebook.tab(self.notebook.select(), "text").strip()
            self.generated_bid_text.delete("1.0", tk.END)

            if active_tab_text == "Grass Cut":
                try:
                    grass_height_str = self.grass_height_entry.get()
                    maintainable_lot_str = self.maintainable_lot_entry.get()
                    total_lot_str = self.total_lot_entry.get()
                    disclaimer_text_content = self.disclaimer_text.get("1.0", tk.END).strip()
                    grass_height_input = float(grass_height_str) if grass_height_str.replace('.', '', 1).isdigit() else 0.0
                    maintainable_lot = float(maintainable_lot_str) if maintainable_lot_str.replace('.', '', 1).isdigit() else 0.0
                    total_lot = float(total_lot_str) if total_lot_str.replace('.', '', 1).isdigit() else 0.0
                    calculated_price, price_error_msg = self.calculate_grass_cut_price(grass_height_input, maintainable_lot)
                    self.gc_calculated_price_label.config(text=f"${calculated_price:.2f}" if not price_error_msg else price_error_msg)
                    grass_condition_text = "over the allowable" if grass_height_input > 12 else "allowable" if 0 < grass_height_input <= 12 else "[Invalid Height]"
                    pricing_tier = None
                    if 2 <= grass_height_input <= 12: pricing_tier = "2\"-12\""
                    elif 12 < grass_height_input <= 24: pricing_tier = "12\"-24\""
                    elif 24 < grass_height_input <= 36: pricing_tier = "24\"-36\""
                    elif 36 < grass_height_input <= 48: pricing_tier = "36\"-48\""
                    elif grass_height_input > 48: pricing_tier = "Above 48\""
                    bid_template = self.gc_pricing_data.get(pricing_tier, {}).get('template', "")
                    generated_bid = bid_template.format(grass_condition=grass_condition_text, grass_height=grass_height_str, maintainable_lot=maintainable_lot_str, total_lot=total_lot_str, disclaimer=disclaimer_text_content)
                    self.generated_bid_text.insert("1.0", generated_bid)
                except Exception as e:
                    self.generated_bid_text.insert("1.0", f"Error in GC tab: {e}")

            elif active_tab_text == "Roofing":
                try:
                    roof_area = float(self.roof_area_entry.get() or 0)
                    edge_metal = float(self.edge_metal_entry.get() or 0)
                    ridge_cap = float(self.ridge_cap_entry.get() or 0)
                    roof_jack = float(self.roof_jack_entry.get() or 0)
                    storey = int(self.selected_storey.get())
                    client = self.selected_client.get()
                    
                    tarp_price, tarp_error = self.calculate_roof_price("Tarp", roof_area, storey, client)
                    replace_price, replace_error = self.calculate_roof_price("Replace", roof_area, storey, client)

                    self.tarp_price_label.config(text=f"${tarp_price:.2f}" if not tarp_error else tarp_error)
                    self.replacement_price_label.config(text=f"${replace_price:.2f}" if not replace_error else replace_error)

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

                    generated_bid = replace_bid_template.format(
                        roof_area=f"{roof_area:.2f}",
                        edge_metal=f"{edge_metal:.2f}",
                        ice_shield=f"{0.2 * roof_area:.2f}",
                        flashing=f"{0.15 * roof_area:.2f}",
                        ridge_cap=f"{ridge_cap:.2f}",
                        roof_jack=f"{roof_jack:.2f}",
                        price=replace_price
                    ) + "\n\n" + tarp_bid_template.format(
                        roof_area=f"{roof_area:.2f}",
                        price=tarp_price
                    )
                    self.generated_bid_text.insert("1.0", generated_bid)
                except Exception as e:
                    self.generated_bid_text.insert("1.0", f"Error in Roofing tab: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during bid generation: {e}")
            self.generated_bid_text.delete("1.0", tk.END)
            self.generated_bid_text.insert("1.0", f"Error: {e}")

    def generate_bids(self):
        final_bid_text = self.generated_bid_text.get("1.0", tk.END).strip()
        if not final_bid_text or "Error" in final_bid_text:
            messagebox.showwarning("No Valid Bid", "Please correct inputs before generating bid.")
            return
        messagebox.showinfo("Generated Bid", f"Final Bid:\n\n{final_bid_text}")

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