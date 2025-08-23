import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
from pathlib import Path
import threading
import time

class DeDupeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeDupe - Video Frame Deduplication Tool")
        self.root.geometry("800x600")
        
        # Video properties
        self.video_path = None
        self.video_cap = None
        self.total_frames = 0
        self.fps = 30
        self.similarity_threshold = 95.0
        
        # Selective Area properties
        self.selective_area_enabled = False
        self.selected_region = None  # (x, y, width, height)
        
        # Processing state
        self.is_processing = False
        self.processed_frames = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="DeDupe", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        ttk.Label(main_frame, text="Video File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(main_frame, textvariable=self.file_path_var, width=50)
        file_entry.grid(row=1, column=1, pady=5)
        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # Video info
        self.info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="10")
        self.info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.video_info_label = ttk.Label(self.info_frame, text="No video selected")
        self.video_info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # FPS setting
        ttk.Label(settings_frame, text="Frames per second:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.IntVar(value=30)
        fps_spinbox = ttk.Spinbox(settings_frame, from_=1, to=60, textvariable=self.fps_var, width=10)
        fps_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Similarity threshold
        ttk.Label(settings_frame, text="Similarity threshold (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.similarity_var = tk.DoubleVar(value=95.0)
        similarity_scale = ttk.Scale(settings_frame, from_=50.0, to=100.0, 
                                   variable=self.similarity_var, orient=tk.HORIZONTAL, length=250)
        similarity_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        self.similarity_label = ttk.Label(settings_frame, text="95.0%")
        self.similarity_label.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # Bind similarity scale update
        similarity_scale.configure(command=self.update_similarity_label)
        
        # Selective Area feature
        self.selective_area_var = tk.BooleanVar(value=False)
        selective_area_check = ttk.Checkbutton(settings_frame, text="Enable Selective Area", 
                                             variable=self.selective_area_var, 
                                             command=self.on_selective_area_toggle)
        selective_area_check.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Selective Area status
        self.selective_area_status = ttk.Label(settings_frame, text="", foreground="gray")
        self.selective_area_status.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Clear selection button
        self.clear_selection_btn = ttk.Button(settings_frame, text="Clear Selection", 
                                            command=self.clear_selective_area, state=tk.DISABLED)
        self.clear_selection_btn.grid(row=2, column=2, padx=(10, 0), pady=5)
        
        # Output directory
        ttk.Label(settings_frame, text="Output directory:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(settings_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        output_btn = ttk.Button(settings_frame, text="Browse", command=self.browse_output)
        output_btn.grid(row=3, column=2, padx=(5, 0), pady=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path = file_path
            self.file_path_var.set(file_path)
            self.load_video_info()
            
    def browse_output(self):
        output_path = filedialog.askdirectory(title="Select Output Directory")
        if output_path:
            self.output_var.set(output_path)
            
    def load_video_info(self):
        if self.video_path and os.path.exists(self.video_path):
            self.video_cap = cv2.VideoCapture(self.video_path)
            if self.video_cap.isOpened():
                self.total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
                duration = self.total_frames / video_fps if video_fps > 0 else 0
                
                info_text = f"Total frames: {self.total_frames:,}\n"
                info_text += f"Video FPS: {video_fps:.2f}\n"
                info_text += f"Duration: {duration:.2f} seconds\n"
                info_text += f"Extraction FPS: {self.fps_var.get()}"
                
                self.video_info_label.config(text=info_text)
                
                # Set default output directory
                if not self.output_var.get():
                    video_dir = Path(self.video_path).parent
                    output_dir = video_dir / "DeDupe_Output"
                    self.output_var.set(str(output_dir))
                
                # Reset selective area when new video is loaded
                if self.selective_area_enabled:
                    self.selected_region = None
                    self.selective_area_var.set(False)
                    self.selective_area_enabled = False
                
                # Update selective area status
                self.update_selective_area_status()
                    
    def update_similarity_label(self, value):
        self.similarity_threshold = float(value)
        self.similarity_label.config(text=f"{self.similarity_threshold:.1f}%")
        
    def on_selective_area_toggle(self):
        """Handle selective area checkbox toggle"""
        self.selective_area_enabled = self.selective_area_var.get()
        if self.selective_area_enabled and not self.video_path:
            messagebox.showwarning("Warning", "Please select a video file first to enable Selective Area feature.")
            self.selective_area_var.set(False)
            self.selective_area_enabled = False
        else:
            self.update_selective_area_status()
    
    def update_selective_area_status(self):
        """Update the selective area status display"""
        if self.selective_area_enabled:
            if self.selected_region:
                x, y, w, h = self.selected_region
                self.selective_area_status.config(
                    text=f"Region: ({x},{y}) {w}×{h}", 
                    foreground="green"
                )
            else:
                self.selective_area_status.config(
                    text="Click 'Start Processing' to select area", 
                    foreground="blue"
                )
        else:
            self.selective_area_status.config(text="", foreground="gray")
        
        # Update clear selection button state
        if self.selective_area_enabled and self.selected_region:
            self.clear_selection_btn.config(state=tk.NORMAL)
        else:
            self.clear_selection_btn.config(state=tk.DISABLED)
    
    def clear_selective_area(self):
        """Clear the selected area"""
        self.selected_region = None
        self.update_selective_area_status()
    
    def show_area_selection_window(self):
        """Show the area selection window"""
        AreaSelectionWindow(self.root, self.video_path, self.on_area_selected)
    
    def on_area_selected(self, selected_region):
        """Callback when area is selected"""
        self.selected_region = selected_region
        self.update_selective_area_status()
        # Continue with processing
        self.start_processing()
        
    def start_processing(self):
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file first!")
            return
            
        if not self.output_var.get():
            messagebox.showerror("Error", "Please select an output directory!")
            return
            
        # Handle selective area selection if enabled
        if self.selective_area_enabled:
            if not self.selected_region:
                self.show_area_selection_window()
                return
            else:
                # Confirm the selected region
                result = messagebox.askyesno("Confirm Region", 
                    f"Process video with selected region?\n"
                    f"X: {self.selected_region[0]}, Y: {self.selected_region[1]}\n"
                    f"Width: {self.selected_region[2]}, Height: {self.selected_region[3]}")
                if not result:
                    return
        
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.start()
        
    def stop_processing(self):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def process_video(self):
        try:
            output_dir = Path(self.output_var.get())
            output_dir.mkdir(exist_ok=True)
            
            # Calculate frame interval
            video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(video_fps / self.fps_var.get())
            
            frames_to_process = self.total_frames // frame_interval
            processed_frames = 0
            saved_frames = 0
            
            # Store frame hashes for duplicate detection
            frame_hashes = set()
            
            self.root.after(0, lambda: self.progress_label.config(text="Starting frame extraction..."))
            
            for frame_idx in range(0, self.total_frames, frame_interval):
                if not self.is_processing:
                    break
                    
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = self.video_cap.read()
                
                if ret:
                    # Apply selective area if enabled
                    if self.selective_area_enabled and self.selected_region:
                        x, y, w, h = self.selected_region
                        # Ensure coordinates are within frame bounds
                        x = max(0, min(x, frame.shape[1] - 1))
                        y = max(0, min(y, frame.shape[0] - 1))
                        w = min(w, frame.shape[1] - x)
                        h = min(h, frame.shape[0] - y)
                        
                        if w > 0 and h > 0:
                            frame = frame[y:y+h, x:x+w]
                        else:
                            continue  # Skip invalid region
                    
                    # Calculate frame hash for duplicate detection
                    frame_hash = self.calculate_frame_hash(frame)
                    
                    if frame_hash not in frame_hashes:
                        frame_hashes.add(frame_hash)
                        
                        # Save frame
                        frame_filename = output_dir / f"frame_{saved_frames:06d}.jpg"
                        cv2.imwrite(str(frame_filename), frame)
                        saved_frames += 1
                    
                    processed_frames += 1
                    
                    # Update progress
                    progress = (processed_frames / frames_to_process) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    status_text = f"Processed: {processed_frames}/{frames_to_process} | Saved: {saved_frames} | Duplicates removed: {processed_frames - saved_frames}"
                    self.root.after(0, lambda t=status_text: self.progress_label.config(text=t))
                    
                    # Small delay to prevent UI freezing
                    time.sleep(0.01)
            
            if self.is_processing:
                self.root.after(0, lambda: self.progress_label.config(text=f"Completed! Saved {saved_frames} frames, removed {processed_frames - saved_frames} duplicates"))
                messagebox.showinfo("Success", f"Processing completed!\n\nSaved frames: {saved_frames}\nDuplicates removed: {processed_frames - saved_frames}\nOutput directory: {output_dir}")
            else:
                self.root.after(0, lambda: self.progress_label.config(text="Processing stopped by user"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            self.root.after(0, lambda: self.progress_label.config(text="Error occurred"))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            
    def calculate_frame_hash(self, frame):
        # Convert to grayscale and resize for faster hashing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (8, 8))
        
        # Calculate average pixel value
        avg = resized.mean()
        
        # Create binary hash based on threshold
        hash_value = 0
        for i in range(8):
            for j in range(8):
                if resized[i, j] > avg:
                    hash_value |= 1 << (i * 8 + j)
                    
        return hash_value

class AreaSelectionWindow:
    """Window for selecting a region of interest in the video frame"""
    
    def __init__(self, parent, video_path, callback):
        self.parent = parent
        self.video_path = video_path
        self.callback = callback
        self.selected_region = None
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Area of Interest")
        self.window.geometry("1000x800")  # Default size, will be adjusted based on video
        self.window.resizable(True, True)
        self.window.minsize(800, 600)  # Minimum window size
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_frame()
        self.center_window()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions
        self.instructions = ttk.Label(main_frame, 
                                    text="Click and drag to select an area of interest. Only this area will be processed.",
                                    font=("Arial", 10))
        self.instructions.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Canvas for frame display and selection
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0)
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
        
        # Selection info
        info_frame = ttk.LabelFrame(main_frame, text="Selection Information", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.selection_info = ttk.Label(info_frame, text="No area selected")
        self.selection_info.grid(row=0, column=0, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Confirm Selection", command=self.confirm_selection).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).grid(row=0, column=2)
        
        # Configure main frame grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Variables for selection
        self.start_x = None
        self.start_y = None
        self.selection_rect = None
        
    def load_frame(self):
        """Load and display a frame from the video"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            if cap.isOpened():
                # Get a frame from the middle of the video
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                middle_frame = total_frames // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Store original frame dimensions for coordinate conversion
                    self.original_frame = frame
                    self.display_frame = pil_image
                    
                    # Get original dimensions
                    orig_width, orig_height = pil_image.size
                    
                    # Calculate optimal display size while maintaining aspect ratio
                    # Target maximum dimensions for good usability
                    max_width, max_height = 1200, 800
                    
                    # Calculate scale factor to fit within max dimensions
                    scale_x = max_width / orig_width
                    scale_y = max_height / orig_height
                    scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down
                    
                    # Calculate display dimensions
                    display_width = int(orig_width * scale)
                    display_height = int(orig_height * scale)
                    
                    # Resize for display if needed
                    if scale < 1.0:
                        pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    self.photo_image = ImageTk.PhotoImage(pil_image)
                    
                    # Update canvas size and scroll region
                    self.canvas.config(scrollregion=(0, 0, self.photo_image.width(), self.photo_image.height()))
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image, tags="frame")
                    
                    # Update window size to accommodate the frame
                    # Add some padding for UI elements
                    window_width = min(display_width + 50, 1400)  # Max window width
                    window_height = min(display_height + 200, 1000)  # Max window height
                    self.window.geometry(f"{window_width}x{window_height}")
                    
                    # Update instructions with video dimensions
                    scale_text = f" (scale: {scale:.2f}x)" if scale < 1.0 else " (full size)"
                    self.instructions.config(
                        text=f"Click and drag to select an area of interest. Only this area will be processed.\n"
                             f"Video dimensions: {orig_width}×{orig_height} pixels | Display: {display_width}×{display_height} pixels{scale_text}"
                    )
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video frame: {str(e)}")
            self.window.destroy()
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # Remove previous selection rectangle
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
    
    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        if self.start_x is not None:
            # Remove previous selection rectangle
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            
            # Get current mouse position
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            
            # Draw selection rectangle
            self.selection_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline="red", width=2, dash=(5, 5)
            )
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if self.start_x is not None and self.selection_rect:
            # Get final coordinates
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            
            # Ensure positive dimensions
            x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
            x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
            
            # Convert display coordinates to original frame coordinates
            if hasattr(self, 'original_frame') and hasattr(self, 'display_frame'):
                # Calculate scale factors (handle case where display = original size)
                orig_width = self.original_frame.shape[1]
                orig_height = self.original_frame.shape[0]
                display_width = self.display_frame.width
                display_height = self.display_frame.height
                
                # Calculate scale factors
                scale_x = orig_width / display_width
                scale_y = orig_height / display_height
                
                # Convert to original frame coordinates
                orig_x = int(x1 * scale_x)
                orig_y = int(y1 * scale_y)
                sel_width = int((x2 - x1) * scale_x)
                sel_height = int((y2 - y1) * scale_y)
                
                # Store selected region
                self.selected_region = (orig_x, orig_y, sel_width, sel_height)
                
                # Update info display
                self.selection_info.config(
                    text=f"Selected: X={orig_x}, Y={orig_y}, Width={sel_width}, Height={sel_height}"
                )
            
            self.start_x = None
            self.start_y = None
    
    def clear_selection(self):
        """Clear the current selection"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        self.selected_region = None
        self.selection_info.config(text="No area selected")
    
    def confirm_selection(self):
        """Confirm the selection and close window"""
        if self.selected_region:
            self.callback(self.selected_region)
            self.window.destroy()
        else:
            messagebox.showwarning("Warning", "Please select an area first.")
    
    def cancel(self):
        """Cancel selection and close window"""
        self.window.destroy()
    
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

def main():
    root = tk.Tk()
    app = DeDupeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()