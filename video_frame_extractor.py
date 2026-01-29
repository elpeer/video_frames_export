"""
Video Frame Extractor
A tool to extract frames from MP4 videos in a selected folder.
Compatible with Windows.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import numpy as np


def check_dependencies():
    """Check if opencv-python is installed."""
    try:
        import cv2
        return True
    except ImportError:
        return False


def save_image_unicode(path, image, quality=95):
    """Save image to a path that may contain Unicode characters (like Hebrew)."""
    import cv2
    # Encode image to JPG in memory
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    result, encoded_img = cv2.imencode('.jpg', image, encode_param)
    if result:
        # Write using Python's open() which handles Unicode paths
        with open(path, 'wb') as f:
            f.write(encoded_img.tobytes())
        return True
    return False


def open_video_unicode(video_path):
    """Open video file with Unicode path support for Windows."""
    import cv2

    # Try opening directly first
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        return cap

    # If failed, try with Windows short path
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes

            GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
            GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            GetShortPathNameW.restype = wintypes.DWORD

            buffer = ctypes.create_unicode_buffer(500)
            GetShortPathNameW(video_path, buffer, 500)
            short_path = buffer.value

            if short_path:
                cap = cv2.VideoCapture(short_path)
                if cap.isOpened():
                    return cap
        except:
            pass

    return cap


def extract_frames_from_video(video_path, output_folder, frame_interval=1, progress_callback=None):
    """
    Extract frames from a video file.

    Args:
        video_path: Path to the video file
        output_folder: Folder to save extracted frames
        frame_interval: Extract every Nth frame (1 = all frames)
        progress_callback: Function to call with progress updates (current, total)

    Returns:
        Number of frames extracted
    """
    import cv2

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Create output subfolder for this video
    video_output_folder = os.path.join(output_folder, video_name)
    os.makedirs(video_output_folder, exist_ok=True)

    # Open video with Unicode support
    cap = open_video_unicode(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_count % frame_interval == 0:
            # Format: video_name_frame_00001.jpg
            frame_filename = f"{video_name}_frame_{frame_count:05d}.jpg"
            frame_path = os.path.join(video_output_folder, frame_filename)

            # Use Unicode-safe save function
            if save_image_unicode(frame_path, frame):
                saved_count += 1

        frame_count += 1

        if progress_callback and frame_count % 10 == 0:
            progress_callback(frame_count, total_frames)

    cap.release()

    if progress_callback:
        progress_callback(total_frames, total_frames)

    return saved_count


def find_mp4_files(folder_path):
    """Find all MP4 files in the given folder."""
    mp4_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.mp4'):
            mp4_files.append(os.path.join(folder_path, file))
    return mp4_files


class VideoFrameExtractorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Frame Extractor")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.frame_interval = tk.IntVar(value=1)
        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input folder selection
        input_frame = ttk.LabelFrame(main_frame, text="Source Folder (MP4 files)", padding="5")
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(input_frame, textvariable=self.input_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side=tk.RIGHT)

        # Output folder selection
        output_frame = ttk.LabelFrame(main_frame, text="Output Folder (for JPG frames)", padding="5")
        output_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.RIGHT)

        # Frame interval
        interval_frame = ttk.LabelFrame(main_frame, text="Settings", padding="5")
        interval_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interval_frame, text="Extract every N frames:").pack(side=tk.LEFT)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=100, textvariable=self.frame_interval, width=10)
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(interval_frame, text="(1 = all frames)").pack(side=tk.LEFT)

        # Progress
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack()

        # Log area
        self.log_text = tk.Text(progress_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Extraction", command=self.start_extraction)
        self.start_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def browse_input(self):
        folder = filedialog.askdirectory(title="Select folder containing MP4 files")
        if folder:
            self.input_folder.set(folder)
            # Auto-set output folder
            if not self.output_folder.get():
                self.output_folder.set(os.path.join(folder, "extracted_frames"))

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder for frames")
        if folder:
            self.output_folder.set(folder)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_extraction(self):
        if self.is_running:
            return

        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()

        if not input_folder:
            messagebox.showerror("Error", "Please select a source folder")
            return

        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return

        if not os.path.exists(input_folder):
            messagebox.showerror("Error", "Source folder does not exist")
            return

        # Find MP4 files
        mp4_files = find_mp4_files(input_folder)

        if not mp4_files:
            messagebox.showwarning("Warning", "No MP4 files found in the selected folder")
            return

        # Create output folder
        os.makedirs(output_folder, exist_ok=True)

        # Start extraction in a separate thread
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)

        thread = threading.Thread(
            target=self.extraction_thread,
            args=(mp4_files, output_folder, self.frame_interval.get())
        )
        thread.daemon = True
        thread.start()

    def extraction_thread(self, mp4_files, output_folder, frame_interval):
        total_videos = len(mp4_files)

        self.root.after(0, lambda: self.log(f"Found {total_videos} MP4 files"))

        for i, video_path in enumerate(mp4_files):
            video_name = os.path.basename(video_path)
            self.root.after(0, lambda v=video_name, n=i+1, t=total_videos:
                self.status_label.config(text=f"Processing: {v} ({n}/{t})"))
            self.root.after(0, lambda v=video_name: self.log(f"Processing: {v}"))

            try:
                def progress_callback(current, total):
                    if total > 0:
                        video_progress = (current / total) * 100
                        overall_progress = ((i + current/total) / total_videos) * 100
                        self.root.after(0, lambda p=overall_progress: self.progress_var.set(p))

                frames_saved = extract_frames_from_video(
                    video_path,
                    output_folder,
                    frame_interval,
                    progress_callback
                )

                self.root.after(0, lambda f=frames_saved, v=video_name:
                    self.log(f"  Extracted {f} frames from {v}"))

            except Exception as e:
                self.root.after(0, lambda v=video_name, err=str(e):
                    self.log(f"  Error processing {v}: {err}"))

        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.status_label.config(text="Extraction complete!"))
        self.root.after(0, lambda: self.log("Extraction complete!"))
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: messagebox.showinfo("Complete",
            f"Extraction complete!\nFrames saved to: {output_folder}"))

        self.is_running = False

    def run(self):
        self.root.mainloop()


def main():
    # Check for OpenCV
    if not check_dependencies():
        print("Error: opencv-python is not installed.")
        print("Please install it using: pip install opencv-python")

        # Show GUI error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Missing Dependency",
                "opencv-python is not installed.\n\n"
                "Please install it using:\n"
                "pip install opencv-python"
            )
            root.destroy()
        except:
            pass

        sys.exit(1)

    # Run GUI
    app = VideoFrameExtractorGUI()
    app.run()


if __name__ == "__main__":
    main()
