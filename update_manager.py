# update_manager.py
# Robust automatic update system for Preservation Universe App
# Uses GitHub Releases as update source

import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import sys
import subprocess
import requests
import re
from packaging import version
from pathlib import Path

class UpdateManager:
    """
    Manages automatic updates from GitHub Releases.
    Handles version checking, update dialogs, and launching updater.
    """
    
    def __init__(self, root_window, current_version="1.0.0", 
                 github_repo="your-org/your-repo",  # Update with your repo
                 check_on_startup=True):
        """
        Initialize UpdateManager.
        
        Args:
            root_window: Tkinter root window
            current_version: Current app version (semantic versioning)
            github_repo: GitHub repository in format "owner/repo"
            check_on_startup: Whether to check for updates on startup
        """
        self.root = root_window
        self.current_version = current_version
        self.github_repo = github_repo
        self.check_on_startup = check_on_startup
        
        # Get app directory and paths
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            self.app_dir = Path(sys.executable).parent
            self.app_exe = Path(sys.executable).name
        else:
            # Running as script
            self.app_dir = Path(__file__).parent
            self.app_exe = "PreservationApp.exe"  # Default name
        
        self.version_file = self.app_dir / "version.txt"
        self.updater_exe = self.app_dir / "updater.exe"
        
        # Load version from file if exists, otherwise use provided version
        self._load_version()
        
        # GitHub API endpoints
        self.github_api_base = f"https://api.github.com/repos/{github_repo}"
        self.releases_url = f"{self.github_api_base}/releases/latest"
        
        # Update check state
        self.update_check_thread = None
        self.latest_version_info = None
        
        # Logging
        self.log_file = self.app_dir / "update.log"
        self._log(f"UpdateManager initialized. Current version: {self.current_version}")
    
    def _load_version(self):
        """Load version from version.txt file if it exists."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    saved_version = f.read().strip()
                    if saved_version:
                        self.current_version = saved_version
        except Exception as e:
            self._log(f"Error loading version file: {e}")
    
    def _save_version(self, version_str):
        """Save version to version.txt file."""
        try:
            with open(self.version_file, 'w') as f:
                f.write(version_str)
            self.current_version = version_str
        except Exception as e:
            self._log(f"Error saving version file: {e}")
    
    def _log(self, message):
        """Log message to file."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass  # Silently fail if logging fails
    
    def check_for_updates(self, show_no_update_message=False):
        """
        Check for updates in background thread.
        
        Args:
            show_no_update_message: If True, show message when no update is available
        """
        if self.update_check_thread and self.update_check_thread.is_alive():
            self._log("Update check already in progress, skipping...")
            return
        
        self.update_check_thread = threading.Thread(
            target=self._check_updates_thread,
            args=(show_no_update_message,),
            daemon=True
        )
        self.update_check_thread.start()
    
    def _check_updates_thread(self, show_no_update_message):
        """Background thread to check for updates."""
        try:
            self._log("Checking for updates...")
            
            # Fetch latest release from GitHub
            response = requests.get(
                self.releases_url,
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            if response.status_code == 404:
                self._log("Repository or releases not found")
                if show_no_update_message:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Update Check",
                        "Update server not found. Please check your internet connection."
                    ))
                return
            
            response.raise_for_status()
            release_data = response.json()
            
            # Extract version and download URL
            latest_version = release_data.get('tag_name', '').lstrip('v')
            download_url = None
            exe_asset_name = None
            checksum = None
            
            # Find Windows EXE asset and checksum file
            assets = release_data.get('assets', [])
            for asset in assets:
                asset_name = asset.get('name', '')
                if asset_name.endswith('.exe'):
                    download_url = asset.get('browser_download_url')
                    exe_asset_name = asset_name
                elif asset_name.endswith('.sha256') or asset_name.endswith('.sha256sum'):
                    # Try to fetch checksum from .sha256 file
                    try:
                                checksum_url = asset.get('browser_download_url')
                                if checksum_url:
                                    checksum_response = requests.get(checksum_url, timeout=10)
                                    if checksum_response.status_code == 200:
                                        # Parse checksum file (format: "checksum  filename" or just "checksum")
                                        checksum_text = checksum_response.text.strip()
                                        # Extract first 64-char hex string (SHA256)
                                        checksum_match = re.search(r'([a-fA-F0-9]{64})', checksum_text)
                                if checksum_match:
                                    checksum = checksum_match.group(1)
                                    self._log(f"Found checksum file: {asset_name}")
                    except Exception as e:
                        self._log(f"Could not fetch checksum file: {e}")
            
            if not download_url:
                self._log("No EXE asset found in release")
                if show_no_update_message:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Update Check",
                        "No update package found."
                    ))
                return
            
            # If no checksum file found, try to extract from release notes
            if not checksum:
                release_notes = release_data.get('body', '')
                if release_notes:
                    # Look for SHA256 checksum in release notes (format: SHA256: abc123... or checksum: abc123...)
                    checksum_patterns = [
                        r'SHA256[:\s]+([a-fA-F0-9]{64})',
                        r'checksum[:\s]+([a-fA-F0-9]{64})',
                        r'([a-fA-F0-9]{64})',  # Any 64-char hex string
                    ]
                    for pattern in checksum_patterns:
                        match = re.search(pattern, release_notes, re.IGNORECASE)
                        if match:
                            checksum = match.group(1)
                            self._log(f"Extracted checksum from release notes")
                            break
            
            self.latest_version_info = {
                'version': latest_version,
                'download_url': download_url,
                'release_notes': release_data.get('body', ''),
                'published_at': release_data.get('published_at', ''),
                'checksum': checksum  # SHA256 checksum if available
            }
            
            if checksum:
                self._log(f"Checksum available for verification: {checksum[:16]}...")
            else:
                self._log("No checksum found - download will proceed without checksum verification")
            
            self._log(f"Latest version found: {latest_version}")
            
            # Compare versions
            try:
                if version.parse(latest_version) > version.parse(self.current_version):
                    self._log(f"Update available: {self.current_version} -> {latest_version}")
                    # Show update dialog in main thread
                    self.root.after(0, self._show_update_dialog)
                else:
                    self._log("App is up to date")
                    if show_no_update_message:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Update Check",
                            f"You are running the latest version ({self.current_version})."
                        ))
            except Exception as e:
                self._log(f"Error comparing versions: {e}")
                
        except requests.exceptions.RequestException as e:
            self._log(f"Network error checking for updates: {e}")
            # Silent failure - app continues normally
            if show_no_update_message:
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Check",
                    f"Could not check for updates:\n{str(e)}\n\nApp will continue normally."
                ))
        except Exception as e:
            self._log(f"Unexpected error checking for updates: {e}")
    
    def _show_update_dialog(self):
        """Show update available dialog."""
        if not self.latest_version_info:
            return
        
        latest_version = self.latest_version_info['version']
        release_notes = self.latest_version_info.get('release_notes', 'No release notes available.')
        
        # Create custom dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Available")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        width = 500
        height = 400
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Update Available",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Version info
        version_label = tk.Label(
            main_frame,
            text=f"Current Version: {self.current_version}\n"
                 f"Latest Version: {latest_version}",
            font=("Arial", 11),
            justify='left'
        )
        version_label.pack(pady=(0, 10))
        
        # Release notes
        notes_label = tk.Label(
            main_frame,
            text="Release Notes:",
            font=("Arial", 10, "bold"),
            anchor='w'
        )
        notes_label.pack(fill='x', pady=(10, 5))
        
        # Scrollable text for release notes
        notes_frame = tk.Frame(main_frame)
        notes_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        notes_text = tk.Text(
            notes_frame,
            wrap=tk.WORD,
            width=50,
            height=10,
            font=("Arial", 9),
            relief=tk.SOLID,
            borderwidth=1
        )
        notes_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(notes_frame, command=notes_text.yview)
        scrollbar.pack(side='right', fill='y')
        notes_text.config(yscrollcommand=scrollbar.set)
        
        notes_text.insert('1.0', release_notes[:1000])  # Limit to 1000 chars
        notes_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        def on_update_now():
            dialog.destroy()
            self._start_update()
        
        def on_later():
            dialog.destroy()
            self._log("User postponed update")
        
        update_button = tk.Button(
            button_frame,
            text="Update Now",
            command=on_update_now,
            bg='#2196F3',
            fg='white',
            font=("Arial", 11),
            padx=20,
            pady=5
        )
        update_button.pack(side='right', padx=(10, 0))
        
        later_button = tk.Button(
            button_frame,
            text="Later",
            command=on_later,
            font=("Arial", 11),
            padx=20,
            pady=5
        )
        later_button.pack(side='right')
        
        # Focus on dialog
        dialog.focus_set()
    
    def _start_update(self):
        """Start the update process by launching updater.exe."""
        if not self.latest_version_info:
            messagebox.showerror("Update Error", "Update information not available.")
            return
        
        # Check if updater exists
        if not self.updater_exe.exists():
            messagebox.showerror(
                "Update Error",
                f"Updater not found: {self.updater_exe}\n\n"
                "Please download the latest version manually."
            )
            return
        
        download_url = self.latest_version_info['download_url']
        app_exe_path = self.app_dir / self.app_exe
        
        self._log(f"Starting update process. Download URL: {download_url}")
        
        try:
            # Launch updater with arguments
            # updater.exe --url <download_url> --exe <exe_name> [--checksum <sha256>]
            cmd = [
                str(self.updater_exe),
                '--url', download_url,
                '--exe', str(app_exe_path),
                '--version', self.latest_version_info['version']
            ]
            
            # Add checksum if available
            checksum = self.latest_version_info.get('checksum')
            if checksum:
                cmd.extend(['--checksum', checksum])
                self._log(f"Checksum verification enabled: {checksum[:16]}...")
            
            self._log(f"Launching updater: {' '.join(cmd)}")
            
            # Launch updater (detached process)
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
                cwd=str(self.app_dir)
            )
            
            # Close the application
            self._log("Closing application for update...")
            self.root.after(100, self.root.quit)
            
        except Exception as e:
            self._log(f"Error launching updater: {e}")
            messagebox.showerror(
                "Update Error",
                f"Failed to start update process:\n{str(e)}"
            )

