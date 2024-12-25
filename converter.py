#!/usr/bin/env python3

import os
import sys
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, Future
import pillow_heif
from PIL import Image

# Register pillow_heif so that Image.open() can handle .heic
pillow_heif.register_heif_opener()

INPUT_DIR = "input"
OUTPUT_DIR = "output"


def convert_heic_to_png(heic_path: str, png_path: str) -> None:
    """
    Convert a single HEIC file to PNG using Pillow (with pillow-heif).
    """
    with Image.open(heic_path) as img:
        img.load()  # Ensure the HEIC data is read
        img.save(png_path, "PNG")
    # Returning is optional; no special result needed here.


class HEICConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HEIC to PNG Converter")

        # Main frame
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="Press 'Start Conversion' to begin.")
        self.status_label.pack(pady=(0, 10))

        # Progress Bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='determinate', 
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=(0, 10))

        # Start button
        self.start_button = ttk.Button(self.main_frame, text="Start Conversion", command=self.start_conversion)
        self.start_button.pack()

        # Thread Pool Executor (we'll create it on demand)
        self.executor = None
        self.futures = []
        self.total_files = 0
        self.completed_count = 0

    def start_conversion(self):
        """
        Gathers .heic files in 'input/', creates 'output/' if not exist,
        and starts the ThreadPoolExecutor to convert them.
        """
        input_folder = os.path.abspath(INPUT_DIR)
        output_folder = os.path.abspath(OUTPUT_DIR)

        if not os.path.isdir(input_folder):
            self.status_label.config(text=f"[Error] '{input_folder}' does not exist.")
            return

        os.makedirs(output_folder, exist_ok=True)

        # Collect all .heic files
        heic_files = [
            f for f in os.listdir(input_folder)
            if f.lower().endswith(".heic")
        ]

        if not heic_files:
            self.status_label.config(text="[Info] No .heic files found.")
            return

        # Setup progress info
        self.total_files = len(heic_files)
        self.progress_var.set(0)
        self.progress_bar.configure(maximum=self.total_files)
        self.completed_count = 0

        # Determine thread count (CPU cores - 1, but at least 1)
        cpu_count = os.cpu_count() or 1
        num_threads = max(1, cpu_count - 1)

        self.status_label.config(text=f"Converting {self.total_files} files with {num_threads} threads...")

        # Create executor
        self.executor = ThreadPoolExecutor(max_workers=num_threads)

        # Submit conversion tasks
        for heic_file in heic_files:
            heic_path = os.path.join(input_folder, heic_file)
            base_name, _ = os.path.splitext(heic_file)
            png_path = os.path.join(output_folder, base_name + ".png")

            future = self.executor.submit(convert_heic_to_png, heic_path, png_path)
            future.add_done_callback(self.task_done_callback)
            self.futures.append(future)

    def task_done_callback(self, future: Future):
        """
        Called automatically when each future finishes.
        We increment completed_count and update the UI.
        """
        # We must schedule UI updates on the main thread via 'after()'
        self.after(0, self.update_progress)

    def update_progress(self):
        """
        Increments the progress bar's value and updates status label.
        Called from the main thread (via after()).
        """
        self.completed_count += 1
        self.progress_var.set(self.completed_count)

        # Update label
        self.status_label.config(
            text=f"Converted {self.completed_count}/{self.total_files} files..."
        )

        # If done, show completion message
        if self.completed_count == self.total_files:
            self.status_label.config(text="Conversion Complete!")
            # We can optionally shutdown the executor
            if self.executor:
                self.executor.shutdown(wait=False)


def main():
    app = HEICConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
