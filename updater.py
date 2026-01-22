# updater.py
# Standalone updater executable for Windows
# This script is compiled into updater.exe using PyInstaller
# 
# Usage: updater.exe --url <download_url> --exe <exe_path> [--version <version>]

import sys
import os
import argparse
import time
import shutil
import subprocess
import requests
import hashlib
from pathlib import Path

# Try to import psutil, fallback to Windows API if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            WINDOWS_API_AVAILABLE = True
        except:
            WINDOWS_API_AVAILABLE = False
    else:
        WINDOWS_API_AVAILABLE = False

class Updater:
    """
    Standalone updater that:
    1. Waits for main app to exit
    2. Downloads new EXE
    3. Backs up old EXE
    4. Replaces old with new
    5. Restarts main app
    """
    
    def __init__(self, download_url, exe_path, version=None, expected_checksum=None):
        self.download_url = download_url
        self.exe_path = Path(exe_path)
        self.version = version
        self.expected_checksum = expected_checksum  # SHA256 checksum (hex string)
        self.exe_dir = self.exe_path.parent
        self.exe_name = self.exe_path.name
        self.backup_path = self.exe_dir / f"{self.exe_name}.backup"
        self.temp_download_path = self.exe_dir / f"{self.exe_name}.new"
        
        # Logging
        self.log_file = self.exe_dir / "updater.log"
        self._log("=" * 60)
        self._log(f"Updater started")
        self._log(f"Download URL: {download_url}")
        self._log(f"Target EXE: {exe_path}")
        self._log(f"Version: {version or 'Unknown'}")
        if self.expected_checksum:
            self._log(f"Expected SHA256: {self.expected_checksum[:16]}...")
    
    def _log(self, message):
        """Log message to file."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass
    
    def _is_process_running(self, exe_name):
        """Check if a process with given EXE name is running."""
        try:
            if PSUTIL_AVAILABLE:
                # Use psutil (preferred method)
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if proc.info['exe'] and Path(proc.info['exe']).name.lower() == exe_name.lower():
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                return False
            elif WINDOWS_API_AVAILABLE:
                # Fallback: Use Windows API
                import ctypes
                from ctypes import wintypes
                
                # Create snapshot of all processes
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_READ = 0x0010
                TH32CS_SNAPPROCESS = 0x00000002
                
                kernel32 = ctypes.windll.kernel32
                CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
                Process32First = kernel32.Process32FirstW
                Process32Next = kernel32.Process32NextW
                CloseHandle = kernel32.CloseHandle
                
                class PROCESSENTRY32(ctypes.Structure):
                    _fields_ = [("dwSize", ctypes.c_ulong),
                               ("cntUsage", ctypes.c_ulong),
                               ("th32ProcessID", ctypes.c_ulong),
                               ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                               ("th32ModuleID", ctypes.c_ulong),
                               ("cntThreads", ctypes.c_ulong),
                               ("th32ParentProcessID", ctypes.c_ulong),
                               ("pcPriClassBase", ctypes.c_long),
                               ("dwFlags", ctypes.c_ulong),
                               ("szExeFile", ctypes.c_wchar * 260)]
                
                h_snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
                if h_snapshot == -1:
                    return True  # Assume running if check fails
                
                pe32 = PROCESSENTRY32()
                pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
                
                if Process32First(h_snapshot, ctypes.byref(pe32)):
                    while True:
                        if pe32.szExeFile.lower() == exe_name.lower():
                            CloseHandle(h_snapshot)
                            return True
                        if not Process32Next(h_snapshot, ctypes.byref(pe32)):
                            break
                
                CloseHandle(h_snapshot)
                return False
            else:
                # Last resort: Try to check if file is locked
                try:
                    # Try to open file in exclusive mode
                    test_file = open(self.exe_path, 'r+b')
                    test_file.close()
                    return False  # File is not locked, process not running
                except (IOError, PermissionError):
                    return True  # File is locked, assume process is running
        except Exception as e:
            self._log(f"Error checking process: {e}")
            return True  # Assume running if check fails (safer)
    
    def wait_for_app_exit(self, max_wait_time=60):
        """
        Wait for the main application to exit.
        
        Args:
            max_wait_time: Maximum seconds to wait
        
        Returns:
            True if app exited, False if timeout
        """
        self._log(f"Waiting for {self.exe_name} to exit...")
        
        start_time = time.time()
        check_interval = 0.5  # Check every 500ms
        
        while time.time() - start_time < max_wait_time:
            if not self._is_process_running(self.exe_name):
                self._log(f"{self.exe_name} has exited")
                # Give it a moment to fully release file locks
                time.sleep(1)
                return True
            
            time.sleep(check_interval)
        
        self._log(f"Timeout waiting for {self.exe_name} to exit")
        return False
    
    def download_file(self, url, dest_path, chunk_size=8192):
        """
        Download file from URL with progress tracking and integrity verification.
        
        Args:
            url: Download URL
            dest_path: Destination file path
            chunk_size: Chunk size for streaming
        
        Returns:
            True if successful, False otherwise
        """
        self._log(f"Downloading from {url}...")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Initialize SHA256 hash for checksum verification
            sha256_hash = hashlib.sha256()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        sha256_hash.update(chunk)  # Update hash as we download
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (chunk_size * 10) == 0:  # Log every 10 chunks
                                self._log(f"Downloaded {downloaded}/{total_size} bytes ({percent:.1f}%)")
            
            # Verify file was downloaded
            if not dest_path.exists():
                self._log("Download failed: File does not exist")
                return False
            
            file_size = dest_path.stat().st_size
            if file_size == 0:
                self._log("Download failed: File is empty")
                return False
            
            # Verify file size matches content-length header (if provided)
            if total_size > 0:
                if downloaded != total_size:
                    self._log(f"ERROR: Size mismatch - Expected {total_size} bytes, downloaded {downloaded} bytes")
                    return False
                if file_size != total_size:
                    self._log(f"ERROR: File size mismatch - Expected {total_size} bytes, file is {file_size} bytes")
                    return False
                self._log(f"Size verification passed: {file_size} bytes")
            
            # Calculate and verify SHA256 checksum
            calculated_checksum = sha256_hash.hexdigest()
            self._log(f"Downloaded file SHA256: {calculated_checksum}")
            
            if self.expected_checksum:
                expected_lower = self.expected_checksum.lower().strip()
                calculated_lower = calculated_checksum.lower()
                
                if expected_lower != calculated_lower:
                    self._log(f"ERROR: Checksum mismatch!")
                    self._log(f"  Expected: {expected_lower}")
                    self._log(f"  Calculated: {calculated_lower}")
                    return False
                self._log("Checksum verification passed")
            else:
                self._log("No expected checksum provided, skipping checksum verification")
            
            self._log(f"Download complete: {file_size} bytes")
            return True
                
        except Exception as e:
            self._log(f"Download error: {e}")
            return False
    
    def backup_exe(self):
        """Backup the current EXE file."""
        if not self.exe_path.exists():
            self._log("Warning: Target EXE does not exist, skipping backup")
            return True
        
        try:
            # Remove old backup if exists
            if self.backup_path.exists():
                self.backup_path.unlink()
            
            # Create backup
            shutil.copy2(self.exe_path, self.backup_path)
            self._log(f"Backup created: {self.backup_path}")
            return True
        except Exception as e:
            self._log(f"Backup error: {e}")
            return False
    
    def restore_backup(self):
        """Restore EXE from backup."""
        if not self.backup_path.exists():
            self._log("No backup found to restore")
            return False
        
        try:
            if self.exe_path.exists():
                self.exe_path.unlink()
            shutil.copy2(self.backup_path, self.exe_path)
            self._log("Backup restored successfully")
            return True
        except Exception as e:
            self._log(f"Restore error: {e}")
            return False
    
    def replace_exe(self):
        """Replace old EXE with new downloaded EXE."""
        if not self.temp_download_path.exists():
            self._log("Error: Downloaded file does not exist")
            return False
        
        try:
            # Remove old EXE (should already be closed)
            max_retries = 5
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    if self.exe_path.exists():
                        self.exe_path.unlink()
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        self._log(f"File locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
            # Copy new EXE
            shutil.copy2(self.temp_download_path, self.exe_path)
            self._log(f"EXE replaced successfully")
            
            # Clean up temp file
            try:
                self.temp_download_path.unlink()
            except:
                pass
            
            return True
            
        except Exception as e:
            self._log(f"Replace error: {e}")
            return False
    
    def restart_app(self):
        """Restart the main application."""
        try:
            self._log(f"Restarting {self.exe_name}...")
            subprocess.Popen(
                [str(self.exe_path)],
                cwd=str(self.exe_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            self._log("Application restarted")
            return True
        except Exception as e:
            self._log(f"Restart error: {e}")
            return False
    
    def update_version_file(self):
        """Update version.txt file with new version."""
        if not self.version:
            return
        
        try:
            version_file = self.exe_dir / "version.txt"
            with open(version_file, 'w') as f:
                f.write(self.version)
            self._log(f"Version file updated to {self.version}")
        except Exception as e:
            self._log(f"Error updating version file: {e}")
    
    def run(self):
        """Execute the complete update process."""
        try:
            # Step 1: Wait for app to exit
            if not self.wait_for_app_exit():
                self._log("ERROR: Application did not exit in time")
                return False
            
            # Step 2: Backup current EXE
            if not self.backup_exe():
                self._log("ERROR: Failed to backup current EXE")
                return False
            
            # Step 3: Download new EXE
            if not self.download_file(self.download_url, self.temp_download_path):
                self._log("ERROR: Failed to download new version")
                # Restore backup on download failure
                self.restore_backup()
                return False
            
            # Step 4: Replace EXE
            if not self.replace_exe():
                self._log("ERROR: Failed to replace EXE")
                # Restore backup on replace failure
                self.restore_backup()
                return False
            
            # Step 5: Update version file
            self.update_version_file()
            
            # Step 6: Restart application
            if not self.restart_app():
                self._log("WARNING: Failed to restart application")
                # App might need manual restart, but update succeeded
            
            self._log("Update completed successfully")
            return True
            
        except Exception as e:
            self._log(f"FATAL ERROR: {e}")
            # Try to restore backup on any fatal error
            try:
                self.restore_backup()
            except:
                pass
            return False


def main():
    """Main entry point for updater."""
    parser = argparse.ArgumentParser(description='Preservation Universe App Updater')
    parser.add_argument('--url', required=True, help='Download URL for new EXE')
    parser.add_argument('--exe', required=True, help='Path to main EXE file')
    parser.add_argument('--version', help='Version number of new release')
    parser.add_argument('--checksum', help='Expected SHA256 checksum (hex string)')
    
    args = parser.parse_args()
    
    updater = Updater(args.url, args.exe, args.version, args.checksum)
    success = updater.run()
    
    # Exit silently (no UI)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

