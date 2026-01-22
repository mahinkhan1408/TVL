# main.py
import tkinter as tk
from tkinter import messagebox
from login import LoginPage
from theme_manager import theme_manager
import time
import os

# Initialize update manager (check for updates on startup)
update_manager = None
try:
    from update_manager import UpdateManager
    # Update with your GitHub repository
    # Format: "owner/repository-name"
    GITHUB_REPO = "mahinkhan1408/TVL"  # GitHub repository for automatic updates
    
    # Current app version (semantic versioning: MAJOR.MINOR.PATCH)
    APP_VERSION = "1.0.0"  # TODO: Update this when releasing new versions
except ImportError:
    # Update system not available (development mode or missing dependencies)
    UpdateManager = None
    print("Warning: Update system not available. Install packaging and psutil for update support.")

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Preservation Universe")
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

        welcome_label = tk.Label(self.root, text="Welcome to Preservation Universe",
                                 font=("Arial", 24, "bold"), fg=self.colors['button_text'],
                                 bg=self.colors['primary_blue'])
        welcome_label.pack(expand=True)
        
        # Initialize update manager and check for updates
        self._init_update_system()
        
        self.root.after(3000, self.open_login_page)
    
    def _init_update_system(self):
        """Initialize update system and check for updates."""
        global update_manager
        if UpdateManager:
            try:
                update_manager = UpdateManager(
                    root_window=self.root,
                    current_version=APP_VERSION,
                    github_repo=GITHUB_REPO,
                    check_on_startup=True
                )
                # Check for updates in background (non-blocking)
                update_manager.check_for_updates(show_no_update_message=False)
            except Exception as e:
                print(f"Warning: Could not initialize update system: {e}")
                # App continues normally even if update system fails

    def open_login_page(self):
        self.root.destroy()
        login_root = tk.Tk()
        LoginPage(login_root)

        login_root.mainloop()

if __name__ == "__main__":
    splash_root = tk.Tk()
    SplashScreen(splash_root)
    splash_root.mainloop()