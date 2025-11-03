#!/usr/bin/env python3
"""
HEIC to PNG Converter
A professional-grade batch image converter with GUI support.

This application converts HEIC/HEIF images to PNG format using multi-threading
for optimal performance. Features include quality control, progress tracking,
and configurable thread pools.

Author: Cafer Tuleyp Demirci
License: MIT
Version: 2.0.0
"""

import os
import sys
import json
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import pillow_heif
from PIL import Image
import time
import queue
import threading

# Try to import drag and drop support (optional)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("tkinterdnd2 not available. Drag-and-drop functionality will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heic_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Register pillow_heif so that Image.open() can handle .heic
pillow_heif.register_heif_opener()

# Default directories
INPUT_DIR = "input"
OUTPUT_DIR = "output"

# Batch size for processing files
BATCH_SIZE = 10

# Queue for thread-safe UI updates
ui_update_queue = queue.Queue()

# Supported formats
SUPPORTED_INPUT_FORMATS = (".heic", ".heif")
SUPPORTED_OUTPUT_FORMATS = {
    "PNG": {"extension": ".png", "options": {"optimize": True}},
    "JPEG": {"extension": ".jpg", "options": {"quality": 90, "optimize": True}},
    "WEBP": {"extension": ".webp", "options": {"quality": 90}},
    "BMP": {"extension": ".bmp", "options": {}},
}

# Configuration file
CONFIG_FILE = "config.json"


class ConfigManager:
    """Manages application configuration settings."""
    
    DEFAULT_CONFIG = {
        "input_dir": INPUT_DIR,
        "output_dir": OUTPUT_DIR,
        "quality": 90,
        "thread_count": max(1, (os.cpu_count() or 1) - 1),
        "batch_size": BATCH_SIZE,
        "output_format": "PNG",
        "window_width": 550,
        "window_height": 500,
        "remember_last_dirs": True
    }
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to handle new config keys
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    logger.info(f"Configuration loaded from {self.config_file}")
                    return config
            except Exception as e:
                logger.warning(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info("No config file found. Using default configuration.")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value


def convert_heic_to_png(heic_path: str, png_path: str, quality: int = 90) -> Tuple[str, str, bool, float, Optional[str]]:
    """
    Convert a single HEIC file to PNG using Pillow (with pillow-heif).
    
    Args:
        heic_path: Path to source HEIC file
        png_path: Path to destination PNG file
        quality: Quality setting for PNG output (1-100)
        
    Returns:
        Tuple containing:
            - heic_path: Original file path
            - png_path: Output file path
            - success: Whether conversion succeeded
            - processing_time: Time taken in seconds
            - error_message: Error message if failed, None otherwise
    """
    start_time = time.time()
    success = False
    error_message = None
    
    try:
        # Validate input file exists
        if not os.path.exists(heic_path):
            error_message = "Input file does not exist"
            logger.error(f"{error_message}: {heic_path}")
            return (heic_path, png_path, success, 0.0, error_message)
        
        # Use a context manager for automatic cleanup
        with Image.open(heic_path) as img:
            # Convert RGBA to RGB if saving as JPEG
            if png_path.lower().endswith('.jpg') or png_path.lower().endswith('.jpeg'):
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            
            # Determine output format and options
            output_format = png_path.split('.')[-1].upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            save_options = SUPPORTED_OUTPUT_FORMATS.get(output_format, {}).get("options", {})
            if "quality" in save_options:
                save_options["quality"] = quality
            
            # Save the image
            img.save(png_path, output_format, **save_options)
            success = True
            logger.debug(f"Successfully converted: {heic_path} -> {png_path}")
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error converting {heic_path}: {error_message}")
        
    processing_time = time.time() - start_time
    return (heic_path, png_path, success, processing_time, error_message)


def batch_process_files(
    file_batch: List[str], 
    input_folder: str, 
    output_folder: str, 
    quality: int,
    output_format: str = "PNG"
) -> List[Tuple[str, str, bool, float, Optional[str]]]:
    """Process a batch of files to reduce per-task overhead.
    
    Args:
        file_batch: List of filenames to process
        input_folder: Source directory path
        output_folder: Destination directory path
        quality: Output quality (1-100)
        output_format: Output format (PNG, JPEG, WEBP, BMP)
        
    Returns:
        List of conversion results
    """
    results = []
    extension = SUPPORTED_OUTPUT_FORMATS.get(output_format, {}).get("extension", ".png")
    
    for heic_file in file_batch:
        heic_path = os.path.join(input_folder, heic_file)
        base_name, _ = os.path.splitext(heic_file)
        output_path = os.path.join(output_folder, base_name + extension)
        result = convert_heic_to_png(heic_path, output_path, quality)
        results.append(result)
    return results


# Base class for GUI depends on whether drag-and-drop is available
if HAS_DND:
    class GUIBase(TkinterDnD.Tk):
        pass
else:
    class GUIBase(tk.Tk):
        pass


class HEICConverterGUI(GUIBase):
    """Main GUI application for HEIC to PNG conversion.
    
    Features:
    - Drag and drop support (if tkinterdnd2 is installed)
    - Multi-threaded conversion
    - Progress tracking
    - Configurable output quality and format
    - Persistent settings
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        super().__init__()
        
        # Load configuration
        self.config_manager = ConfigManager()
        
        # Window setup
        self.title("HEIC Converter Pro v2.0")
        window_width = self.config_manager.get("window_width", 550)
        window_height = self.config_manager.get("window_height", 500)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(500, 450)

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern theme
        self.style.configure("TButton", padding=6)
        self.style.configure("TFrame", padding=10)
        self.style.configure("Success.TLabel", foreground="green")
        self.style.configure("Error.TLabel", foreground="red")

        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Directory selection with drag-and-drop
        self.dir_frame = ttk.LabelFrame(self.main_frame, text="Directories", padding=10)
        self.dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input directory
        ttk.Label(self.dir_frame, text="Input folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(
            value=os.path.abspath(self.config_manager.get("input_dir", INPUT_DIR))
        )
        self.input_entry = ttk.Entry(self.dir_frame, textvariable=self.input_dir_var)
        self.input_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(self.dir_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2)
        
        # Enable drag and drop for input (if available)
        if HAS_DND:
            self.input_entry.drop_target_register(DND_FILES)
            self.input_entry.dnd_bind('<<Drop>>', self.drop_input)
        
        # Output directory
        ttk.Label(self.dir_frame, text="Output folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(
            value=os.path.abspath(self.config_manager.get("output_dir", OUTPUT_DIR))
        )
        self.output_entry = ttk.Entry(self.dir_frame, textvariable=self.output_dir_var)
        self.output_entry.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Button(self.dir_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2)
        
        # Enable drag and drop for output (if available)
        if HAS_DND:
            self.output_entry.drop_target_register(DND_FILES)
            self.output_entry.dnd_bind('<<Drop>>', self.drop_output)
        
        self.dir_frame.columnconfigure(1, weight=1)

        # Settings frame
        self.settings_frame = ttk.LabelFrame(self.main_frame, text="Conversion Settings", padding=10)
        self.settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output format selection
        ttk.Label(self.settings_frame, text="Output Format:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.format_var = tk.StringVar(value=self.config_manager.get("output_format", "PNG"))
        self.format_combo = ttk.Combobox(
            self.settings_frame,
            textvariable=self.format_var,
            values=list(SUPPORTED_OUTPUT_FORMATS.keys()),
            state="readonly",
            width=10
        )
        self.format_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Quality setting
        ttk.Label(self.settings_frame, text="Quality:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.quality_var = tk.IntVar(value=self.config_manager.get("quality", 90))
        self.quality_scale = ttk.Scale(
            self.settings_frame, 
            from_=1, 
            to=100, 
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            length=150
        )
        self.quality_scale.grid(row=0, column=3, sticky=tk.EW, pady=5, padx=5)
        self.quality_label = ttk.Label(self.settings_frame, text="90", width=3)
        self.quality_label.grid(row=0, column=4, sticky=tk.W, pady=5, padx=5)
        
        # Update quality label when scale changes
        self.quality_var.trace_add("write", self.update_quality_label)
        
        self.settings_frame.columnconfigure(3, weight=1)
        
        # Performance settings
        self.perf_frame = ttk.LabelFrame(self.main_frame, text="Performance Settings", padding=10)
        self.perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Thread count selection
        ttk.Label(self.perf_frame, text="Thread count:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Calculate recommended thread count (CPU cores - 1, min 1)
        cpu_count = os.cpu_count() or 1
        recommended_threads = max(1, cpu_count - 1)
        
        self.thread_var = tk.IntVar(value=self.config_manager.get("thread_count", recommended_threads))
        self.thread_spinbox = ttk.Spinbox(
            self.perf_frame,
            from_=1,
            to=cpu_count * 2,  # Allow some oversubscription
            textvariable=self.thread_var,
            width=5
        )
        self.thread_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(self.perf_frame, text=f"(Recommended: {recommended_threads} for {cpu_count} CPU cores)").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )

        # Statistics frame
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Conversion Statistics", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status information
        self.status_label = ttk.Label(self.stats_frame, text="Ready to convert")
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.time_label = ttk.Label(self.stats_frame, text="")
        self.time_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.error_label = ttk.Label(self.stats_frame, text="", style="Error.TLabel")
        self.error_label.grid(row=2, column=0, sticky=tk.W, pady=2)

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
        
        self.open_output_button = ttk.Button(
            self.button_frame,
            text="Open Output Folder",
            command=self.open_output_folder
        )
        self.open_output_button.pack(side=tk.LEFT, padx=5)

        # Thread Pool Executor
        self.executor: Optional[ThreadPoolExecutor] = None
        self.futures: List = []
        self.total_files = 0
        self.completed_count = 0
        self.error_count = 0
        self.is_running = False
        self.start_time = 0.0
        
        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start UI update timer
        self.after(100, self.process_ui_updates)
        
        logger.info("HEIC Converter GUI initialized")

    def drop_input(self, event) -> None:
        """Handle drag and drop for input directory.
        
        Args:
            event: Drop event containing file path
        """
        path = event.data.strip('{}')
        if os.path.isdir(path):
            self.input_dir_var.set(path)
            logger.info(f"Input directory set via drag-drop: {path}")

    def drop_output(self, event) -> None:
        """Handle drag and drop for output directory.
        
        Args:
            event: Drop event containing file path
        """
        path = event.data.strip('{}')
        if os.path.isdir(path):
            self.output_dir_var.set(path)
            logger.info(f"Output directory set via drag-drop: {path}")

    def browse_input(self) -> None:
        """Open directory browser for input directory."""
        directory = filedialog.askdirectory(
            initialdir=self.input_dir_var.get(),
            title="Select Input Directory"
        )
        if directory:
            self.input_dir_var.set(directory)
            logger.info(f"Input directory selected: {directory}")

    def browse_output(self) -> None:
        """Open directory browser for output directory."""
        directory = filedialog.askdirectory(
            initialdir=self.output_dir_var.get(),
            title="Select Output Directory"
        )
        if directory:
            self.output_dir_var.set(directory)
            logger.info(f"Output directory selected: {directory}")

    def update_quality_label(self, *args) -> None:
        """Update the quality label when the slider changes."""
        self.quality_label.config(text=str(self.quality_var.get()))

    def open_output_folder(self) -> None:
        """Open the output folder in file explorer."""
        output_folder = self.output_dir_var.get()
        if os.path.exists(output_folder):
            if sys.platform == 'win32':
                os.startfile(output_folder)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_folder}"')
            else:
                os.system(f'xdg-open "{output_folder}"')
            logger.info(f"Opened output folder: {output_folder}")
        else:
            messagebox.showwarning("Folder Not Found", f"The output folder does not exist:\n{output_folder}")

    def start_conversion(self) -> None:
        """
        Gathers .heic files, creates output dir if not exist,
        and starts the ThreadPoolExecutor to convert them.
        """
        if self.is_running:
            return
            
        self.is_running = True
        self.start_time = time.time()
        self.error_count = 0
        self.error_label.config(text="")
        
        input_folder = self.input_dir_var.get()
        output_folder = self.output_dir_var.get()
        quality = self.quality_var.get()
        thread_count = self.thread_var.get()
        output_format = self.format_var.get()

        # Validate input directory
        if not os.path.isdir(input_folder):
            messagebox.showerror("Error", f"Input directory does not exist:\n{input_folder}")
            self.is_running = False
            logger.error(f"Input directory does not exist: {input_folder}")
            return

        # Create output directory
        try:
            os.makedirs(output_folder, exist_ok=True)
            logger.info(f"Output directory ready: {output_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output directory:\n{e}")
            self.is_running = False
            logger.error(f"Cannot create output directory: {e}")
            return

        # Collect all .heic files
        try:
            all_files = os.listdir(input_folder)
            heic_files = [
                f for f in all_files
                if f.lower().endswith(SUPPORTED_INPUT_FORMATS)
            ]
        except Exception as e:
            messagebox.showerror("Error", f"Error reading directory:\n{e}")
            self.is_running = False
            logger.error(f"Error reading directory {input_folder}: {e}")
            return

        if not heic_files:
            messagebox.showinfo("No Files", "No HEIC/HEIF files found in the input directory.")
            self.is_running = False
            logger.warning(f"No HEIC/HEIF files found in {input_folder}")
            return

        # Setup progress info
        self.total_files = len(heic_files)
        self.progress_var.set(0)
        self.progress_bar.configure(maximum=self.total_files)
        self.completed_count = 0

        # Update UI
        self.status_label.config(
            text=f"Converting {self.total_files} files with {thread_count} threads...",
            style="TLabel"
        )
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        logger.info(f"Starting conversion: {self.total_files} files, {thread_count} threads, format: {output_format}")

        # Save current settings
        self.save_current_settings()

        # Create batches for processing
        batch_size = self.config_manager.get("batch_size", BATCH_SIZE)
        batches = []
        for i in range(0, len(heic_files), batch_size):
            batch = heic_files[i:i + batch_size]
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
                quality,
                output_format
            )
            self.futures.append(future)

        # Start a monitoring thread to avoid blocking the UI
        threading.Thread(target=self.monitor_conversion, daemon=True).start()

    def monitor_conversion(self) -> None:
        """Monitor the conversion progress in a separate thread."""
        total_time = 0.0
        processed_count = 0
        error_count = 0
        
        for future in as_completed(self.futures):
            if not self.is_running:
                break
                
            try:
                results = future.result()
                for result in results:
                    _, _, success, proc_time, error_msg = result
                    if success:
                        processed_count += 1
                        total_time += proc_time
                    else:
                        error_count += 1
                        if error_msg:
                            logger.error(f"Conversion failed: {error_msg}")
                    # Queue an update for the UI thread
                    ui_update_queue.put(("progress", (processed_count, error_count)))
            except Exception as e:
                error_count += 1
                logger.error(f"Batch processing error: {e}")
                ui_update_queue.put(("error", str(e)))
                
        # All done or cancelled
        avg_time = total_time / processed_count if processed_count > 0 else 0
        total_elapsed = time.time() - self.start_time
        
        ui_update_queue.put(("complete", {
            "processed": processed_count,
            "errors": error_count,
            "avg_time": avg_time,
            "total_time": total_elapsed
        }))

    def process_ui_updates(self) -> None:
        """Process UI updates from the queue."""
        try:
            while not ui_update_queue.empty():
                update_type, data = ui_update_queue.get_nowait()
                
                if update_type == "progress":
                    self.update_progress(data[0], data[1])
                elif update_type == "error":
                    self.error_label.config(text=f"Error: {data[:50]}...")
                elif update_type == "complete":
                    self.conversion_complete(data)
        except Exception as e:
            logger.error(f"Error processing UI updates: {e}")
            
        # Schedule the next check
        self.after(100, self.process_ui_updates)

    def update_progress(self, completed_count: int, error_count: int) -> None:
        """Update progress bar and status label.
        
        Args:
            completed_count: Number of successfully converted files
            error_count: Number of failed conversions
        """
        self.completed_count = completed_count
        self.error_count = error_count
        total_processed = completed_count + error_count
        self.progress_var.set(total_processed)
        
        elapsed = time.time() - self.start_time
        self.status_label.config(
            text=f"Converted {completed_count}/{self.total_files} files..."
        )
        self.time_label.config(
            text=f"Time: {elapsed:.1f}s | Errors: {error_count}"
        )
        if error_count > 0:
            self.error_label.config(text=f"{error_count} file(s) failed to convert")

    def conversion_complete(self, data: Dict[str, Any]) -> None:
        """Handle conversion completion.
        
        Args:
            data: Dictionary containing conversion statistics
        """
        processed = data["processed"]
        errors = data["errors"]
        avg_time = data["avg_time"]
        total_time = data["total_time"]
        
        success_msg = f"✓ Successfully converted {processed} files"
        error_msg = f" | ✗ {errors} failed" if errors > 0 else ""
        
        self.status_label.config(
            text=success_msg + error_msg,
            style="Success.TLabel" if errors == 0 else "TLabel"
        )
        self.time_label.config(
            text=f"Total: {total_time:.1f}s | Average: {avg_time*1000:.1f}ms/file"
        )
        
        if errors > 0:
            self.error_label.config(
                text=f"{errors} file(s) failed. Check heic_converter.log for details."
            )
        
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.is_running = False
        
        # Cleanup
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
        
        logger.info(f"Conversion complete: {processed} succeeded, {errors} failed, {total_time:.2f}s total")
        
        # Show completion message
        if errors == 0:
            messagebox.showinfo("Success", f"Successfully converted {processed} files!")
        else:
            messagebox.showwarning(
                "Completed with Errors", 
                f"Converted {processed} files successfully.\n{errors} files failed.\nCheck the log file for details."
            )

    def cancel_conversion(self) -> None:
        """Cancel the conversion process."""
        if not self.is_running:
            return
            
        self.status_label.config(text="Cancelling...")
        self.is_running = False
        logger.info("User cancelled conversion")
        
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
        self.status_label.config(text="Conversion cancelled")

    def save_current_settings(self) -> None:
        """Save current UI settings to configuration."""
        self.config_manager.set("input_dir", self.input_dir_var.get())
        self.config_manager.set("output_dir", self.output_dir_var.get())
        self.config_manager.set("quality", self.quality_var.get())
        self.config_manager.set("thread_count", self.thread_var.get())
        self.config_manager.set("output_format", self.format_var.get())
        self.config_manager.set("window_width", self.winfo_width())
        self.config_manager.set("window_height", self.winfo_height())
        self.config_manager.save_config()

    def on_closing(self) -> None:
        """Handle window close event."""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Conversion in progress. Do you want to cancel and quit?"):
                self.cancel_conversion()
                self.save_current_settings()
                self.destroy()
        else:
            self.save_current_settings()
            self.destroy()
        logger.info("Application closed")


def main():
    app = HEICConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()