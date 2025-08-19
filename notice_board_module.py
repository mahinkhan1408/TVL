# notice_board_module.py
import tkinter as tk
from tkinter import messagebox
import requests
import csv
import io
from datetime import datetime

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showwarning("Missing Module", "PIL/Pillow is required for photo support. Install with: pip install pillow")
    Image = None
    ImageTk = None

class NoticeBoardModule:
    def __init__(self, root):
        self.root = root
        self.root.title("Notice Board")
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
            'notice_bg': '#e0f7fa' # Light cyan for notice background
        }

        # Module Title
        self.module_title_frame = tk.Frame(self.root, bg=self.colors['primary_blue'], height=60)
        self.module_title_frame.pack(fill='x', pady=(0, 10))
        self.module_title_frame.pack_propagate(False)
        
        tk.Label(self.module_title_frame, text="Company Notice Board", 
                 font=("Arial", 18, "bold"), fg='white', 
                 bg=self.colors['primary_blue']).pack(side="left", padx=20)
        
        self.refresh_button = tk.Button(self.module_title_frame, text="Refresh Notices",
                                        font=("Arial", 10, "bold"), bg=self.colors['light_blue'], 
                                        fg="white", relief="flat", cursor="hand2",
                                        activebackground=self.colors['primary_blue'],
                                        command=self.refresh_notices)
        self.refresh_button.pack(side="right", padx=(0, 20))

        # Notice Board Content Frame (with scrollbar)
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

        self.notice_data_url = "https://docs.google.com/spreadsheets/d/1lnX9OO9Qq5v6KZmeYTiy5ChwJ8SSDYHyFkIZuxmNABw/edit?usp=sharing" # <<< REPLACE WITH YOUR GOOGLE SHEET URL
        self.load_notices()

    def refresh_notices(self):
        self.load_notices()
        messagebox.showinfo("Refresh Complete", "Notice board has been refreshed successfully.")

    def load_notices(self):
        # Clear existing notices
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            response = requests.get(self.notice_data_url, timeout=10)
            response.raise_for_status()
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)

            notices_found = False
            for row in reader:
                if 'Title' in row and 'Time' in row and 'Notice' in row:
                    title = row['Title']
                    notice_time = row['Time']
                    notice_text = row['Notice']
                    photo_url = row.get('PhotoURL', '').strip() # Optional photo URL

                    self.display_notice(title, notice_time, notice_text, photo_url)
                    notices_found = True
            
            if not notices_found:
                tk.Label(self.scrollable_frame, text="No notices available.", 
                         font=("Arial", 12), bg=self.colors['white'], fg=self.colors['gray_medium']).pack(pady=20)

        except requests.exceptions.RequestException as e:
            messagebox.showwarning("Network Error", f"Could not load notices from online. Please check internet connection.\nError: {e}")
            self.display_error_notice("Network Error", "Failed to load notices due to network issues.")
        except Exception as e:
            messagebox.showwarning("Error", f"Failed to parse notice data.\nError: {e}")
            self.display_error_notice("Data Error", "Failed to load notices due to data parsing issues.")

    def display_notice(self, title, notice_time, notice_text, photo_url=None):
        notice_frame = tk.Frame(self.scrollable_frame, bg=self.colors['notice_bg'], 
                                bd=2, relief="groove", padx=15, pady=10)
        notice_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(notice_frame, text=title, font=("Arial", 14, "bold"), 
                 bg=self.colors['notice_bg'], fg=self.colors['primary_blue'], anchor="w").pack(fill="x")
        
        tk.Label(notice_frame, text=f"Time: {notice_time}", font=("Arial", 10, "italic"), 
                 bg=self.colors['notice_bg'], fg=self.colors['gray_medium'], anchor="w").pack(fill="x", pady=(2, 5))
        
        tk.Label(notice_frame, text=notice_text, font=("Arial", 11), wraplength=self.root.winfo_width() - 80,
                 bg=self.colors['notice_bg'], fg=self.colors['gray_dark'], justify="left", anchor="w").pack(fill="x")

        if photo_url and Image and ImageTk:
            self.load_and_display_photo(notice_frame, photo_url)

    def load_and_display_photo(self, parent_frame, photo_url):
        try:
            response = requests.get(photo_url, stream=True, timeout=5)
            response.raise_for_status()
            
            # Read image data into a BytesIO object
            image_data = io.BytesIO(response.content)
            img = Image.open(image_data)
            
            # Resize image to fit, maintaining aspect ratio
            max_width = 300
            max_height = 200
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(parent_frame, image=photo, bg=self.colors['notice_bg'])
            img_label.image = photo # Keep a reference!
            img_label.pack(pady=10)
        except Exception as e:
            tk.Label(parent_frame, text=f"Could not load image: {e}", 
                     font=("Arial", 9, "italic"), fg="red", bg=self.colors['notice_bg']).pack(pady=5)

    def display_error_notice(self, title, message):
        error_frame = tk.Frame(self.scrollable_frame, bg="#f8d7da", bd=2, relief="groove", padx=15, pady=10) # Light red background
        error_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(error_frame, text=title, font=("Arial", 14, "bold"), fg="#721c24", bg="#f8d7da").pack(fill="x")
        tk.Label(error_frame, text=message, font=("Arial", 11), fg="#721c24", bg="#f8d7da").pack(fill="x", pady=(5,0))