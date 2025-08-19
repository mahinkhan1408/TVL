# main.py
import tkinter as tk
from tkinter import messagebox
from login import LoginPage
from theme_manager import theme_manager
import time

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Techvengers Universal App")
        self.root.overrideredirect(True) # Remove window decorations

        # Use theme manager for colors
        self.colors = theme_manager.get_current_colors()
        self.root.configure(bg=self.colors['primary_blue'])

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 800
        window_height = 500
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

        welcome_label = tk.Label(self.root, text="Welcome to Techvengers Universe",
                                 font=("Arial", 24, "bold"), fg=self.colors['button_text'],
                                 bg=self.colors['primary_blue'])
        welcome_label.pack(expand=True)
        
        self.root.after(3000, self.open_login_page)

    def open_login_page(self):
        self.root.destroy()
        login_root = tk.Tk()
        LoginPage(login_root)
        login_root.mainloop()

if __name__ == "__main__":
    splash_root = tk.Tk()
    SplashScreen(splash_root)
    splash_root.mainloop()