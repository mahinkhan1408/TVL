# admin_module.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional


class AdminModule:
    """Admin module for user management and daily analysis"""
    
    def __init__(self, parent_frame, db, user_id, username, colors=None):
        self.parent_frame = parent_frame
        self.db = db
        self.user_id = user_id
        self.username = username
        self.colors = colors or {}
        
        # Verify user is admin
        if not self.db or not self.db.is_admin(self.user_id):
            messagebox.showerror("Access Denied", "You do not have admin privileges.")
            return
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the admin UI"""
        # Clear parent frame
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Main container
        container = tk.Frame(self.parent_frame, bg=self.colors.get('background', '#F5F7FA'))
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(container, bg=self.colors.get('background', '#F5F7FA'))
        title_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(title_frame, text="Admin Panel", 
                font=("Arial", 24, "bold"), 
                bg=self.colors.get('background', '#F5F7FA'),
                fg=self.colors.get('primary_blue', '#1e3a5f')).pack(side='left')
        
        # Notebook for tabs
        notebook = ttk.Notebook(container)
        notebook.pack(fill='both', expand=True)
        
        # Tab 1: User Management
        user_frame = tk.Frame(notebook, bg=self.colors.get('background', '#F5F7FA'))
        notebook.add(user_frame, text="User Management")
        self.create_user_management_tab(user_frame)
        
        # Tab 2: Daily Analysis
        analysis_frame = tk.Frame(notebook, bg=self.colors.get('background', '#F5F7FA'))
        notebook.add(analysis_frame, text="Daily Analysis")
        self.create_daily_analysis_tab(analysis_frame)
    
    def create_user_management_tab(self, parent):
        """Create user management tab"""
        # Header with Add User button
        header = tk.Frame(parent, bg=self.colors.get('background', '#F5F7FA'))
        header.pack(fill='x', pady=(0, 20))
        
        tk.Label(header, text="Manage Users", 
                font=("Arial", 16, "bold"),
                bg=self.colors.get('background', '#F5F7FA'),
                fg=self.colors.get('text_primary', '#1F2937')).pack(side='left')
        
        add_btn = tk.Button(header, text="+ Add User", 
                           font=("Arial", 11, "bold"),
                           bg=self.colors.get('light_blue', '#3B82F6'),
                           fg='white',
                           relief='flat',
                           cursor='hand2',
                           padx=15, pady=8,
                           command=self.add_user)
        add_btn.pack(side='right')
        
        # Users table
        table_frame = tk.Frame(parent, bg=self.colors.get('background', '#F5F7FA'))
        table_frame.pack(fill='both', expand=True)
        
        # Create treeview
        columns = ('Username', 'Created At', 'Last Login', 'Admin')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('Username', text='Username')
        tree.heading('Created At', text='Created At')
        tree.heading('Last Login', text='Last Login')
        tree.heading('Admin', text='Admin')
        
        tree.column('Username', width=200)
        tree.column('Created At', width=200)
        tree.column('Last Login', width=200)
        tree.column('Admin', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Store tree reference
        self.users_tree = tree
        
        # Delete button
        delete_btn = tk.Button(parent, text="Delete Selected User", 
                              font=("Arial", 11),
                              bg='#dc3545',
                              fg='white',
                              relief='flat',
                              cursor='hand2',
                              padx=15, pady=8,
                              command=lambda: self.delete_user(tree))
        delete_btn.pack(pady=(10, 0))
        
        # Load users
        self.load_users()
    
    def load_users(self):
        """Load all users into the table"""
        if not self.db:
            return
        
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        try:
            users = self.db.get_all_users()
            for user in users:
                username = user.get('username', 'Unknown')
                created_at = user.get('created_at', '')
                last_login = user.get('last_login', 'Never')
                is_admin = 'Yes' if user.get('is_admin', False) else 'No'
                
                # Format dates
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                if last_login and last_login != 'Never':
                    try:
                        dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                        last_login = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                self.users_tree.insert('', 'end', values=(username, created_at, last_login, is_admin), tags=(str(user.get('id')),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {e}")
    
    def add_user(self):
        """Add a new user"""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add New User")
        dialog.geometry("400x200")
        dialog.configure(bg=self.colors.get('background', '#F5F7FA'))
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"400x200+{x}+{y}")
        
        # Username
        tk.Label(dialog, text="Username:", 
                bg=self.colors.get('background', '#F5F7FA'),
                font=("Arial", 11)).pack(pady=(20, 5))
        
        username_entry = tk.Entry(dialog, font=("Arial", 11), width=30)
        username_entry.pack(pady=5)
        username_entry.focus()
        
        # Password
        tk.Label(dialog, text="Password:", 
                bg=self.colors.get('background', '#F5F7FA'),
                font=("Arial", 11)).pack(pady=(10, 5))
        
        password_entry = tk.Entry(dialog, font=("Arial", 11), width=30, show="*")
        password_entry.pack(pady=5)
        
        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not username:
                messagebox.showerror("Error", "Username cannot be empty.")
                return
            
            if not password:
                messagebox.showerror("Error", "Password cannot be empty.")
                return
            
            try:
                self.db.create_user(username, password)
                messagebox.showinfo("Success", f"User '{username}' created successfully.")
                dialog.destroy()
                self.load_users()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create user: {e}")
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors.get('background', '#F5F7FA'))
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Cancel", 
                 command=dialog.destroy,
                 font=("Arial", 10),
                 bg=self.colors.get('gray_light', '#E5E7EB'),
                 padx=15, pady=5).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Create User", 
                 command=save_user,
                 font=("Arial", 10, "bold"),
                 bg=self.colors.get('light_blue', '#3B82F6'),
                 fg='white',
                 padx=15, pady=5).pack(side='left', padx=5)
        
        # Bind Enter key
        username_entry.bind("<Return>", lambda e: password_entry.focus())
        password_entry.bind("<Return>", lambda e: save_user())
    
    def delete_user(self, tree):
        """Delete selected user"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to delete.")
            return
        
        item = selected[0]
        values = tree.item(item, 'values')
        username = values[0]
        
        # Get user ID from tags
        tags = tree.item(item, 'tags')
        user_id = int(tags[0]) if tags else None
        
        if not user_id:
            messagebox.showerror("Error", "Could not determine user ID.")
            return
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Deletion", 
                                     f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.")
        if not result:
            return
        
        try:
            self.db.delete_user(user_id)
            messagebox.showinfo("Success", f"User '{username}' deleted successfully.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {e}")
    
    def create_daily_analysis_tab(self, parent):
        """Create daily analysis tab"""
        # Header with date picker
        header = tk.Frame(parent, bg=self.colors.get('background', '#F5F7FA'))
        header.pack(fill='x', pady=(0, 20))
        
        tk.Label(header, text="Daily Analysis", 
                font=("Arial", 16, "bold"),
                bg=self.colors.get('background', '#F5F7FA'),
                fg=self.colors.get('text_primary', '#1F2937')).pack(side='left')
        
        # Date picker
        date_frame = tk.Frame(header, bg=self.colors.get('background', '#F5F7FA'))
        date_frame.pack(side='right')
        
        tk.Label(date_frame, text="Date:", 
                bg=self.colors.get('background', '#F5F7FA'),
                font=("Arial", 11)).pack(side='left', padx=(0, 5))
        
        date_entry = tk.Entry(date_frame, font=("Arial", 11), width=12)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_entry.pack(side='left', padx=(0, 5))
        
        def load_stats():
            date_str = date_entry.get().strip()
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                self.load_daily_stats(date_str)
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format.")
        
        tk.Button(date_frame, text="Load", 
                 command=load_stats,
                 font=("Arial", 10),
                 bg=self.colors.get('light_blue', '#3B82F6'),
                 fg='white',
                 padx=10, pady=5).pack(side='left')
        
        # Stats display
        stats_frame = tk.Frame(parent, bg=self.colors.get('background', '#F5F7FA'))
        stats_frame.pack(fill='both', expand=True)
        
        # Summary cards
        summary_frame = tk.Frame(stats_frame, bg=self.colors.get('background', '#F5F7FA'))
        summary_frame.pack(fill='x', pady=(0, 20))
        
        self.total_bids_label = tk.Label(summary_frame, text="Total Bids: 0", 
                                         font=("Arial", 14, "bold"),
                                         bg=self.colors.get('primary_blue', '#1e3a5f'),
                                         fg='white',
                                         padx=20, pady=15)
        self.total_bids_label.pack(side='left', padx=10)
        
        self.total_wo_label = tk.Label(summary_frame, text="Total Work Orders: 0", 
                                       font=("Arial", 14, "bold"),
                                       bg=self.colors.get('light_blue', '#3B82F6'),
                                       fg='white',
                                       padx=20, pady=15)
        self.total_wo_label.pack(side='left', padx=10)
        
        # Detailed stats
        details_frame = tk.Frame(stats_frame, bg=self.colors.get('background', '#F5F7FA'))
        details_frame.pack(fill='both', expand=True)
        
        # Left: Bids by user
        bids_frame = tk.LabelFrame(details_frame, text="Bids by User", 
                                   font=("Arial", 12, "bold"),
                                   bg=self.colors.get('background', '#F5F7FA'),
                                   padx=10, pady=10)
        bids_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        bids_text = tk.Text(bids_frame, font=("Arial", 10), wrap='word', height=15)
        bids_text.pack(fill='both', expand=True)
        self.bids_text = bids_text
        
        # Right: Work Orders by user
        wo_frame = tk.LabelFrame(details_frame, text="Work Orders by User", 
                                 font=("Arial", 12, "bold"),
                                 bg=self.colors.get('background', '#F5F7FA'),
                                 padx=10, pady=10)
        wo_frame.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        wo_text = tk.Text(wo_frame, font=("Arial", 10), wrap='word', height=15)
        wo_text.pack(fill='both', expand=True)
        self.wo_text = wo_text
        
        # Load today's stats initially
        self.load_daily_stats(datetime.now().strftime('%Y-%m-%d'))
    
    def load_daily_stats(self, date_str):
        """Load daily statistics"""
        if not self.db:
            return
        
        try:
            stats = self.db.get_daily_stats(date_str)
            
            # Update summary
            self.total_bids_label.config(text=f"Total Bids: {stats['total_bids']}")
            self.total_wo_label.config(text=f"Total Work Orders: {stats['total_work_orders']}")
            
            # Update bids by user
            self.bids_text.delete('1.0', tk.END)
            if stats['bids_by_user']:
                for username, count in sorted(stats['bids_by_user'].items(), key=lambda x: x[1], reverse=True):
                    self.bids_text.insert(tk.END, f"{username}: {count}\n")
            else:
                self.bids_text.insert(tk.END, "No bids found for this date.")
            
            # Update work orders by user
            self.wo_text.delete('1.0', tk.END)
            if stats['work_orders_by_user']:
                for username, count in sorted(stats['work_orders_by_user'].items(), key=lambda x: x[1], reverse=True):
                    self.wo_text.insert(tk.END, f"{username}: {count}\n")
            else:
                self.wo_text.insert(tk.END, "No work orders found for this date.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load daily stats: {e}")

