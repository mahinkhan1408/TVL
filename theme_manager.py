# theme_manager.py
import os
import json
from typing import Dict, Any

class ThemeManager:
    """Global theme manager for the entire Techvengers application."""
    
    def __init__(self):
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".techvengers_bidwriter")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.current_theme = self.load_theme_preference()
        self.theme_callbacks = []
    
    def get_theme_colors(self, theme_name: str) -> Dict[str, str]:
        """Return color scheme based on theme name."""
        themes = {
            'light': {
                'primary_blue': '#1e3a5f',
                'secondary_blue': '#2c476c',
                'light_blue': '#3498db',
                'background': '#f8f9fa',
                'white': '#ffffff',
                'gray_light': '#e9ecef',
                'gray_medium': '#6c757d',
                'gray_dark': '#495057',
                'green': '#28a745',
                'selected': '#d4edda',
                'preview_bg': '#f8f9fa',
                'active_category_color': '#3A648F',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'border': '#dee2e6',
                'button_text': '#ffffff',
                'nav_fg': 'white',
                'nav_hover': '#3a648f',
                'shadow_gray': '#aaaaaa'
            },
            'dark': {
                'primary_blue': '#2c5282',
                'secondary_blue': '#3d4852',
                'light_blue': '#4299e1',
                'background': '#1a202c',
                'white': '#2d3748',
                'gray_light': '#4a5568',
                'gray_medium': '#718096',
                'gray_dark': '#e2e8f0',
                'green': '#38a169',
                'selected': '#2d5016',
                'preview_bg': '#2d3748',
                'active_category_color': '#4299e1',
                'text_primary': '#f7fafc',
                'text_secondary': '#cbd5e0',
                'border': '#4a5568',
                'button_text': '#ffffff',
                'nav_fg': '#f7fafc',
                'nav_hover': '#4299e1',
                'shadow_gray': '#4a5568'
            }
        }
        return themes.get(theme_name, themes['light'])

    def load_theme_preference(self) -> str:
        """Load theme preference from settings file."""
        try:
            settings_file = os.path.join(self.app_data_dir, "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('theme', 'light')
        except:
            pass
        return 'light'

    def save_theme_preference(self, theme_name: str):
        """Save theme preference to settings file."""
        try:
            settings_file = os.path.join(self.app_data_dir, "settings.json")
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            
            settings['theme'] = theme_name
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving theme preference: {e}")

    def switch_theme(self, theme_name: str):
        """Switch to a different theme and notify all subscribers."""
        self.current_theme = theme_name
        self.save_theme_preference(theme_name)
        
        # Notify all registered callbacks
        for callback in self.theme_callbacks:
            try:
                callback(theme_name, self.get_theme_colors(theme_name))
            except Exception as e:
                print(f"Error in theme callback: {e}")

    def register_theme_callback(self, callback):
        """Register a callback to be called when theme changes."""
        self.theme_callbacks.append(callback)

    def unregister_theme_callback(self, callback):
        """Unregister a theme callback."""
        if callback in self.theme_callbacks:
            self.theme_callbacks.remove(callback)

    def get_current_colors(self) -> Dict[str, str]:
        """Get the current theme colors."""
        return self.get_theme_colors(self.current_theme)

# Global theme manager instance
theme_manager = ThemeManager()
