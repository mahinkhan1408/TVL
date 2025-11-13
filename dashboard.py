# dashboard.py
import tkinter as tk
from theme_manager import theme_manager
from training_module import TrainingModule

class Dashboard:
	"""
	Dashboard window: header toolbar + grid of option cards.
	The Training card is placed before the Settings card.
	"""
	def __init__(self, parent):
		self.win = tk.Toplevel(parent)
		self.win.title("Dashboard")
		try:
			colors = theme_manager.get_current_colors()
		except Exception:
			colors = {}
		bg = colors.get('bg', '#ffffff')
		primary = colors.get('primary_blue', '#1e4f7a')
		secondary = colors.get('secondary_blue', '#2c6aa0')
		btn_text = colors.get('button_text', '#ffffff')
		card_bg = colors.get('card_bg', '#f7f7f7')

		self.win.configure(bg=bg)
		self.win.geometry("900x600")

		# Header / toolbar
		header = tk.Frame(self.win, bg=primary, height=60)
		header.pack(fill="x")
		title = tk.Label(header, text="Dashboard", font=("Segoe UI", 16, "bold"),
						 bg=primary, fg=btn_text)
		title.pack(side="left", padx=16, pady=10)

		# Training opener callback
		def _open_training():
			try:
				TrainingModule(self.win)
			except Exception as e:
				try:
					from tkinter import messagebox
					messagebox.showerror("Error", f"Failed to open Training module:\n{e}")
				except Exception:
					pass

		# Training button in header (optional)
		train_btn = tk.Button(header, text="Training", command=_open_training,
							  bg=secondary, fg=btn_text)
		train_btn.pack(side="right", padx=12, pady=10)

		# Main area with cards
		main = tk.Frame(self.win, bg=bg)
		main.pack(fill="both", expand=True, padx=20, pady=20)

		# Card style/options
		card_opts = {"bd": 1, "relief": "solid", "bg": card_bg, "width": 28, "height": 8}

		# Row 0: example action cards
		newbid = tk.Frame(main, **card_opts)
		newbid.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
		nb_label = tk.Label(newbid, text="New Bid", font=("Arial", 14, "bold"), bg=card_bg)
		nb_label.pack(pady=(20,5))
		nb_desc = tk.Label(newbid, text="Create a new bid", bg=card_bg)
		nb_desc.pack()

		openproj = tk.Frame(main, **card_opts)
		openproj.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
		op_label = tk.Label(openproj, text="Open Project", font=("Arial", 14, "bold"), bg=card_bg)
		op_label.pack(pady=(20,5))
		op_desc = tk.Label(openproj, text="Open existing project", bg=card_bg)
		op_desc.pack()

		# Row 1: TRAINING card inserted BEFORE Settings
		training_card = tk.Frame(main, **card_opts)
		training_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
		tr_label = tk.Label(training_card, text="Training", font=("Arial", 14, "bold"), bg=card_bg)
		tr_label.pack(pady=(20,5))
		tr_desc = tk.Label(training_card, text="Open the training module", bg=card_bg)
		tr_desc.pack()
		for w in (training_card, tr_label, tr_desc):
			w.bind("<Button-1>", lambda e: _open_training())
			w.configure(cursor="hand2")

		# Settings card comes AFTER Training
		settings_card = tk.Frame(main, **card_opts)
		settings_card.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
		s_label = tk.Label(settings_card, text="Settings", font=("Arial", 14, "bold"), bg=card_bg)
		s_label.pack(pady=(20,5))
		s_desc = tk.Label(settings_card, text="Application settings", bg=card_bg)
		s_desc.pack()

		# Layout tweaks
		for c in range(2):
			main.columnconfigure(c, weight=1)
		main.rowconfigure(0, weight=1)
		main.rowconfigure(1, weight=1)