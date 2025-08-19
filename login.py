# login.py
import tkinter as tk
from tkinter import messagebox
import os
import requests
import json
import csv
import io
from dashboard_menu import DashboardMenu # Import the new DashboardMenu
from theme_manager import theme_manager

class LoginPage:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        
        # Use global theme manager
        self.colors = theme_manager.get_current_colors()
        
        # Register for theme updates
        theme_manager.register_theme_callback(self.on_theme_changed)

        master.update_idletasks()
        width = int(master.winfo_screenwidth() * 0.6)
        height = int(master.winfo_screenheight() * 0.6)
        x = (master.winfo_screenwidth() // 2) - (width // 2)
        y = (master.winfo_screenheight() // 2) - (height // 2)
        master.geometry(f'{width}x{height}+{x}+{y}')
        
        master.resizable(False, False)
        
        self.main_frame = tk.Frame(master, bg=self.colors['background'])
        self.main_frame.pack(fill="both", expand=True)

        self.header_frame = tk.Frame(self.main_frame, bg=self.colors['primary_blue'], height=60)
        self.header_frame.pack(fill='x', pady=(0, 20))
        self.header_frame.pack_propagate(False)

        tk.Label(self.header_frame, text="Techvengers Bid Writer",
                 font=("Arial", 18, "bold"), fg='white',
                 bg=self.colors['primary_blue']).pack(side="left", expand=True)
        
        refresh_button_frame = self.create_shadow_button(
            self.header_frame,
            "Refresh Credentials",
            self.refresh_credentials,
            self.colors['light_blue'],
            'white',
            self.colors['shadow_gray'],
            pady=2
        )
        refresh_button_frame.pack(side="right", padx=10, pady=(10, 10))

        self.login_frame = tk.Frame(self.main_frame, bg=self.colors['background'])
        self.login_frame.pack(expand=True)
        
        tk.Label(self.login_frame, text="Secure Login",
                 font=("Arial", 14, "bold"), bg=self.colors['background']).pack(pady=(0, 10))
        
        tk.Label(self.login_frame, text="Username:", font=("Arial", 11), bg=self.colors['background']).pack(pady=2)
        self.username_entry = tk.Entry(self.login_frame, width=30, font=("Arial", 11), relief="solid", bd=1)
        self.username_entry.pack(pady=(0, 10))
        
        tk.Label(self.login_frame, text="Password:", font=("Arial", 11), bg=self.colors['background']).pack(pady=2)
        self.password_entry = tk.Entry(self.login_frame, show="*", width=30, font=("Arial", 11), relief="solid", bd=1)
        self.password_entry.pack(pady=(0, 10))

        checkbox_frame = tk.Frame(self.login_frame, bg=self.colors['background'])
        checkbox_frame.pack(pady=(0, 10))
        
        self.show_password_var = tk.IntVar()
        self.show_password_checkbox = tk.Checkbutton(checkbox_frame, text="Show Password", font=("Arial", 9), bg=self.colors['background'], variable=self.show_password_var, command=self.toggle_password)
        self.show_password_checkbox.pack(side="left", padx=5)

        self.save_password_var = tk.IntVar()
        self.save_password_checkbox = tk.Checkbutton(checkbox_frame, text="Save Password", font=("Arial", 9), bg=self.colors['background'], variable=self.save_password_var)
        self.save_password_checkbox.pack(side="left", padx=5)
        
        login_button_frame = self.create_shadow_button(
            self.login_frame, 
            "Login", 
            self.login_check, 
            self.colors['light_blue'], 
            'white', 
            self.colors['shadow_gray']
        )
        login_button_frame.pack(pady=10)
        
        self.credentials_url = "https://docs.google.com/spreadsheets/d/17ckYvmA47Sa5PJ0-KyqvlyoODMK2bLQWrZx1KofOvrc/gviz/tq?tqx=out:csv&sheet=Sheet1"
        
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.credentials_file = os.path.join(self.app_data_dir, "credentials.json")

        self.load_saved_credentials()
        self.credentials = self.load_credentials_from_url(self.credentials_url)
    
    def create_shadow_button(self, parent, text, command, button_bg, button_fg, shadow_bg, padx=10, pady=5):
        shadow_frame = tk.Frame(parent, bg=shadow_bg, bd=1, relief="solid")
        button = tk.Button(
            shadow_frame, 
            text=text, 
            command=command,
            font=("Arial", 12, "bold"), 
            bg=button_bg, 
            fg=button_fg, 
            relief="flat", 
            bd=0, 
            cursor="hand2",
            padx=padx,
            pady=pady
        )
        button.pack(padx=2, pady=2)
        return shadow_frame
        
    def load_credentials_from_url(self, url):
        credentials_dict = {}
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            for row in reader:
                if 'Username' in row and 'Password' in row:
                    credentials_dict[row['Username'].strip()] = row['Password'].strip()
            return credentials_dict
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not connect to online credentials file. Please check your internet connection.\nError: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse credentials file.\nError: {e}")
            return None

    def refresh_credentials(self):
        self.credentials = self.load_credentials_from_url(self.credentials_url)
        if self.credentials:
            messagebox.showinfo("Refresh Complete", "Credentials have been refreshed successfully.")
    
    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def save_password(self, username, password):
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump({"username": username, "password": password}, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save password: {e}")

    def load_saved_credentials(self):
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                    self.username_entry.insert(0, data.get("username", ""))
                    self.password_entry.insert(0, data.get("password", ""))
                    self.save_password_var.set(1)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def login_check(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if self.credentials and username in self.credentials and self.credentials[username] == password:
            if self.save_password_var.get():
                self.save_password(username, password)
            else:
                if os.path.exists(self.credentials_file):
                    os.remove(self.credentials_file)
            
            self.master.destroy()
            
            # Create a new root window for the dashboard menu
            dashboard_root = tk.Tk()
            app = DashboardMenu(dashboard_root, username=username) 
            dashboard_root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def on_theme_changed(self, theme_name, colors):
        """Called when theme is changed globally."""
        self.colors = colors
        # Update login page elements with new theme
        self.master.configure(bg=self.colors['background'])