#!/usr/bin/env python3

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
import pillow_heif
from PIL import Image
import time
import queue
import threading

# Register pillow_heif so that Image.open() can handle .heic
pillow_heif.register_heif_opener()

# Default directories
INPUT_DIR = "input"
OUTPUT_DIR = "output"

# Batch size for processing files
BATCH_SIZE = 10

# Queue for thread-safe UI updates
ui_update_queue = queue.Queue()


def convert_heic_to_png(heic_path: str, png_path: str, quality: int = 90) -> tuple:
    """
    Convert a single HEIC file to PNG using Pillow (with pillow-heif).
    
    Args:
        heic_path: Path to source HEIC file
        png_path: Path to destination PNG file
        quality: Quality setting for PNG output (1-100)
        
    Returns:
        tuple: (heic_path, png_path, success, processing_time)
    """
    start_time = time.time()
    success = False
    
    try:
        # Use a context manager for automatic cleanup
        with Image.open(heic_path) as img:
            # Use optimize=True for better compression
            img.save(png_path, "PNG", optimize=True, quality=quality)
            success = True
    except Exception as e:
        print(f"Error converting {heic_path}: {e}")
        
    processing_time = time.time() - start_time
    return (heic_path, png_path, success, processing_time)


def batch_process_files(file_batch, input_folder, output_folder, quality):
    """Process a batch of files to reduce per-task overhead"""
    results = []
    for heic_file in file_batch:
        heic_path = os.path.join(input_folder, heic_file)
        base_name, _ = os.path.splitext(heic_file)
        png_path = os.path.join(output_folder, base_name + ".png")
        result = convert_heic_to_png(heic_path, png_path, quality)
        results.append(result)
    return results


class HEICConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HEIC to PNG Converter")
        self.geometry("450x350")  # Slightly larger window

        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("TFrame", padding=10)

        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Directory selection
        self.dir_frame = ttk.Frame(self.main_frame)
        self.dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.dir_frame, text="Input folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=os.path.abspath(INPUT_DIR))
        ttk.Entry(self.dir_frame, textvariable=self.input_dir_var).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(self.dir_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2)
        
        ttk.Label(self.dir_frame, text="Output folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=os.path.abspath(OUTPUT_DIR))
        ttk.Entry(self.dir_frame, textvariable=self.output_dir_var).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Button(self.dir_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2)
        
        self.dir_frame.columnconfigure(1, weight=1)

        # Quality setting
        self.quality_frame = ttk.Frame(self.main_frame)
        self.quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.quality_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.IntVar(value=90)
        self.quality_scale = ttk.Scale(
            self.quality_frame, 
            from_=1, 
            to=100, 
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            length=200
        )
        self.quality_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.quality_label = ttk.Label(self.quality_frame, text="90")
        self.quality_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Update quality label when scale changes
        self.quality_var.trace_add("write", self.update_quality_label)
        
        # Performance settings
        self.perf_frame = ttk.LabelFrame(self.main_frame, text="Performance Settings")
        self.perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Thread count selection
        ttk.Label(self.perf_frame, text="Thread count:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Calculate recommended thread count (CPU cores - 1, min 1)
        cpu_count = os.cpu_count() or 1
        recommended_threads = max(1, cpu_count - 1)
        
        self.thread_var = tk.IntVar(value=recommended_threads)
        self.thread_spinbox = ttk.Spinbox(
            self.perf_frame,
            from_=1,
            to=cpu_count * 2,  # Allow some oversubscription
            textvariable=self.thread_var,
            width=5
        )
        self.thread_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(self.perf_frame, text=f"(Recommended: {recommended_threads})").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Status information
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side=tk.RIGHT)

        # Progress Bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='determinate', 
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(
            self.button_frame, 
            text="Start Conversion", 
            command=self.start_conversion
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            self.button_frame, 
            text="Cancel", 
            command=self.cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Thread Pool Executor
        self.executor = None
        self.futures = []
        self.total_files = 0
        self.completed_count = 0
        self.is_running = False
        self.start_time = 0
        
        # Start UI update timer
        self.after(100, self.process_ui_updates)

    def browse_input(self):
        """Open directory browser for input directory"""
        directory = filedialog.askdirectory(
            initialdir=self.input_dir_var.get(),
            title="Select Input Directory"
        )
        if directory:
            self.input_dir_var.set(directory)

    def browse_output(self):
        """Open directory browser for output directory"""
        directory = filedialog.askdirectory(
            initialdir=self.output_dir_var.get(),
            title="Select Output Directory"
        )
        if directory:
            self.output_dir_var.set(directory)

    def update_quality_label(self, *args):
        """Update the quality label when the slider changes"""
        self.quality_label.config(text=str(self.quality_var.get()))

    def start_conversion(self):
        """
        Gathers .heic files, creates output dir if not exist,
        and starts the ThreadPoolExecutor to convert them.
        """
        if self.is_running:
            return
            
        self.is_running = True
        self.start_time = time.time()
        
        input_folder = self.input_dir_var.get()
        output_folder = self.output_dir_var.get()
        quality = self.quality_var.get()
        thread_count = self.thread_var.get()

        if not os.path.isdir(input_folder):
            self.status_label.config(text=f"Error: '{input_folder}' does not exist")
            self.is_running = False
            return

        os.makedirs(output_folder, exist_ok=True)

        # Collect all .heic files
        try:
            all_files = os.listdir(input_folder)
            heic_files = [
                f for f in all_files
                if f.lower().endswith((".heic", ".heif"))
            ]
        except Exception as e:
            self.status_label.config(text=f"Error reading directory: {e}")
            self.is_running = False
            return

        if not heic_files:
            self.status_label.config(text="No HEIC/HEIF files found")
            self.is_running = False
            return

        # Setup progress info
        self.total_files = len(heic_files)
        self.progress_var.set(0)
        self.progress_bar.configure(maximum=self.total_files)
        self.completed_count = 0

        # Update UI
        self.status_label.config(text=f"Converting {self.total_files} files with {thread_count} threads...")
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

        # Create batches for processing
        batches = []
        for i in range(0, len(heic_files), BATCH_SIZE):
            batch = heic_files[i:i + BATCH_SIZE]
            batches.append(batch)

        # Create executor
        self.executor = ThreadPoolExecutor(max_workers=thread_count)
        self.futures = []

        # Submit batch conversion tasks
        for batch in batches:
            future = self.executor.submit(
                batch_process_files, 
                batch, 
                input_folder, 
                output_folder, 
                quality
            )
            self.futures.append(future)

        # Start a monitoring thread to avoid blocking the UI
        threading.Thread(target=self.monitor_conversion, daemon=True).start()

    def monitor_conversion(self):
        """Monitor the conversion progress in a separate thread"""
        total_time = 0
        processed_count = 0
        
        for future in as_completed(self.futures):
            if not self.is_running:
                break
                
            try:
                results = future.result()
                for result in results:
                    _, _, success, proc_time = result
                    if success:
                        processed_count += 1
                        total_time += proc_time
                        # Queue an update for the UI thread
                        ui_update_queue.put(("progress", processed_count))
            except Exception as e:
                ui_update_queue.put(("error", str(e)))
                
        # All done or cancelled
        avg_time = total_time / processed_count if processed_count > 0 else 0
        total_elapsed = time.time() - self.start_time
        
        ui_update_queue.put(("complete", {
            "processed": processed_count,
            "avg_time": avg_time,
            "total_time": total_elapsed
        }))

    def process_ui_updates(self):
        """Process UI updates from the queue"""
        try:
            while not ui_update_queue.empty():
                update_type, data = ui_update_queue.get_nowait()
                
                if update_type == "progress":
                    self.update_progress(data)
                elif update_type == "error":
                    self.status_label.config(text=f"Error: {data}")
                elif update_type == "complete":
                    self.conversion_complete(data)
        except Exception as e:
            print(f"Error processing UI updates: {e}")
            
        # Schedule the next check
        self.after(100, self.process_ui_updates)

    def update_progress(self, completed_count):
        """Update progress bar and status label"""
        self.completed_count = completed_count
        self.progress_var.set(completed_count)
        
        elapsed = time.time() - self.start_time
        self.status_label.config(
            text=f"Converted {completed_count}/{self.total_files} files..."
        )
        self.time_label.config(
            text=f"Time: {elapsed:.1f}s"
        )

    def conversion_complete(self, data):
        """Handle conversion completion"""
        processed = data["processed"]
        avg_time = data["avg_time"]
        total_time = data["total_time"]
        
        self.status_label.config(
            text=f"Conversion Complete! Processed {processed} files"
        )
        self.time_label.config(
            text=f"Total: {total_time:.1f}s (avg: {avg_time*1000:.1f}ms/file)"
        )
        
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.is_running = False
        
        # Cleanup
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

    def cancel_conversion(self):
        """Cancel the conversion process"""
        if not self.is_running:
            return
            
        self.status_label.config(text="Cancelling...")
        self.is_running = False
        
        # Cancel all pending futures
        for future in self.futures:
            if not future.done():
                future.cancel()
                
        # Shutdown the executor
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
            
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)


def main():
    app = HEICConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()