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
                                   variable=self.similarity_var, orient=tk.HORIZONTAL, length=200)
        similarity_scale.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.similarity_label = ttk.Label(settings_frame, text="95.0%")
        self.similarity_label.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # Bind similarity scale update
        similarity_scale.configure(command=self.update_similarity_label)
        
        # Output directory
        ttk.Label(settings_frame, text="Output directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(settings_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        output_btn = ttk.Button(settings_frame, text="Browse", command=self.browse_output)
        output_btn.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
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
                    
    def update_similarity_label(self, value):
        self.similarity_threshold = float(value)
        self.similarity_label.config(text=f"{self.similarity_threshold:.1f}%")
        
    def start_processing(self):
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file first!")
            return
            
        if not self.output_var.get():
            messagebox.showerror("Error", "Please select an output directory!")
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

def main():
    root = tk.Tk()
    app = DeDupeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()