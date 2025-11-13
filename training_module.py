import tkinter as tk
from tkinter import ttk
import threading
import time

class TrainingModule:
	def __init__(self, parent):
		self.win = tk.Toplevel(parent)
		self.win.title("Training Module")
		self.win.geometry("600x400")

		header = tk.Label(self.win, text="Training Module", font=("Arial", 16, "bold"))
		header.pack(pady=10)

		desc = tk.Label(self.win, text="This module will guide you through training tasks.\nClick Start to simulate a training session.")
		desc.pack(pady=10)

		self.log = tk.Text(self.win, height=10, state="disabled")
		self.log.pack(fill="both", expand=True, padx=10, pady=10)

		btn_frame = tk.Frame(self.win)
		btn_frame.pack(pady=8)
		self.start_btn = tk.Button(btn_frame, text="Start Training", command=self.start_training)
		self.start_btn.pack(side="left", padx=5)
		close_btn = tk.Button(btn_frame, text="Close", command=self.win.destroy)
		close_btn.pack(side="left", padx=5)

	def _append_log(self, text):
		self.log.configure(state="normal")
		self.log.insert("end", text + "\n")
		self.log.see("end")
		self.log.configure(state="disabled")

	def start_training(self):
		self.start_btn.configure(state="disabled")
		threading.Thread(target=self._run_training, daemon=True).start()

	def _run_training(self):
		# Simulate training steps
		for i in range(1, 6):
			self._append_log(f"Starting step {i}...")
			time.sleep(1)  # simulate work
			self._append_log(f"Completed step {i}")
		self._append_log("Training finished.")
		self.start_btn.configure(state="normal")
