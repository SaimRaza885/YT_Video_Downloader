import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import shutil
import os
import glob
import time
import subprocess
import sys

# Store last downloaded file path
last_downloaded_file = None

# ---------- Helpers ----------
def ffmpeg_available():
    return shutil.which("ffmpeg") is not None

def find_final_file(prepared_path, save_dir, lookback_seconds=600):
    base = os.path.splitext(prepared_path)[0] if prepared_path else ""
    candidates = glob.glob(base + ".*") if base else []
    if candidates:
        return max(candidates, key=os.path.getmtime)

    now = time.time()
    recent = []
    for p in glob.glob(os.path.join(save_dir, "*")):
        try:
            m = os.path.getmtime(p)
            size = os.path.getsize(p)
            if (now - m) <= lookback_seconds and size > 0:
                recent.append(p)
        except:
            continue
    if recent:
        return max(recent, key=os.path.getmtime)
    return None

def open_file(path):
    """Open file in default player."""
    if sys.platform.startswith("darwin"):  # macOS
        subprocess.call(["open", path])
    elif os.name == "nt":  # Windows
        os.startfile(path)
    elif os.name == "posix":  # Linux
        subprocess.call(["xdg-open", path])

def open_folder(path):
    """Open folder in file explorer."""
    folder = os.path.dirname(path)
    if sys.platform.startswith("darwin"):
        subprocess.call(["open", folder])
    elif os.name == "nt":
        os.startfile(folder)
    elif os.name == "posix":
        subprocess.call(["xdg-open", folder])

# ---------- Download Logic ----------
def start_download(download_type):
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return

    save_path = filedialog.askdirectory()
    if not save_path:
        return

    progress_bar["value"] = 0
    status_label.config(text="Starting download...", fg="blue")
    window.update_idletasks()

    threading.Thread(target=download_worker, args=(url, save_path, download_type), daemon=True).start()

def download_worker(url, save_dir, download_type):
    global last_downloaded_file
    try:
        has_ffmpeg = ffmpeg_available()
        outtmpl = os.path.join(save_dir, "%(title)s.%(ext)s")

        quality = quality_var.get()
        if quality == "1080p":
            quality_fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif quality == "720p":
            quality_fmt = "bestvideo[height<=720]+bestaudio/best"
        elif quality == "480p":
            quality_fmt = "bestvideo[height<=480]+bestaudio/best"
        else:
            quality_fmt = "bestvideo+bestaudio/best"

        ydl_opts = {
            "outtmpl": outtmpl,
            "progress_hooks": [progress_hook],
            "noplaylist": True,
        }

        if download_type == "video":
            if has_ffmpeg:
                ydl_opts.update({
                    "format": quality_fmt,
                    "merge_output_format": "mp4",
                    "postprocessors": [{
                        "key": "FFmpegVideoRemuxer",
                        "preferedformat": "mp4",
                    }],
                })
            else:
                ydl_opts.update({
                    "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
                })
        else:  # audio
            if has_ffmpeg:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                })
            else:
                ydl_opts.update({
                    "format": "bestaudio/best",
                })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            try:
                prepared = ydl.prepare_filename(info)
            except Exception:
                prepared = None

        final = find_final_file(prepared, save_dir)
        if final:
            last_downloaded_file = final
            ui_update_status(f"✅ Download complete:\n{final}", "green")
            window.after(0, lambda: show_open_buttons())
            messagebox.showinfo("Download complete", f"Saved to:\n{final}")
        else:
            ui_update_status("❌ Download finished but file not found.", "red")
            messagebox.showwarning("Warning", "Download finished but file not found. Check the folder.")

    except Exception as e:
        ui_update_status("❌ Download Failed", "red")
        messagebox.showerror("Error", str(e))

def progress_hook(d):
    status = d.get("status")
    if status == "downloading":
        pct_str = d.get("_percent_str") or ""
        try:
            pct = float(pct_str.replace("%", "").strip())
            window.after(0, lambda: progress_bar_step(pct))
        except:
            pass
    elif status == "finished":
        filename = d.get("filename")
        if filename:
            window.after(0, lambda: status_label.config(text=f"Downloaded: {os.path.basename(filename)} (processing...)", fg="orange"))

def progress_bar_step(value):
    progress_bar["value"] = value
    status_label.config(text=f"{int(value)}% downloaded", fg="blue")
    window.update_idletasks()

def ui_update_status(text, color="black"):
    window.after(0, lambda: status_label.config(text=text, fg=color))

def show_open_buttons():
    if last_downloaded_file:
        open_btn_frame.pack(pady=10)

# ---------- UI ----------
window = tk.Tk()
window.title("YouTube Downloader")
window.geometry("620x420")
window.resizable(False, False)

tk.Label(window, text="YouTube Downloader", font=("Arial", 18, "bold")).pack(pady=10)

tk.Label(window, text="Enter YouTube URL:", font=("Arial", 12)).pack()
url_entry = tk.Entry(window, width=70, font=("Arial", 12))
url_entry.pack(pady=6)

tk.Label(window, text="Select Quality:", font=("Arial", 12)).pack(pady=(8, 0))
quality_var = tk.StringVar(value="Best")
quality_dropdown = ttk.Combobox(window, textvariable=quality_var, state="readonly",
                                values=["1080p", "720p", "480p", "Best"])
quality_dropdown.current(3)
quality_dropdown.pack(pady=6)

btn_frame = tk.Frame(window)
btn_frame.pack(pady=12)
tk.Button(btn_frame, text="Download Video (MP4)", command=lambda: start_download("video"),
          bg="#1f6feb", fg="white", font=("Arial", 11, "bold"), width=20).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="Download Audio (MP3 if available)", command=lambda: start_download("audio"),
          bg="#16a34a", fg="white", font=("Arial", 11, "bold"), width=25).grid(row=0, column=1, padx=10)

progress_bar = ttk.Progressbar(window, orient="horizontal", length=520, mode="determinate")
progress_bar.pack(pady=18)

status_label = tk.Label(window, text="", font=("Arial", 11))
status_label.pack(pady=4)

# Frame for Open buttons (hidden until a file is downloaded)
open_btn_frame = tk.Frame(window)

open_video_btn = tk.Button(open_btn_frame, text="Open Video", command=lambda: open_file(last_downloaded_file),
                           bg="purple", fg="white", font=("Arial", 11, "bold"), width=15)
open_video_btn.grid(row=0, column=0, padx=10)

open_folder_btn = tk.Button(open_btn_frame, text="Open Folder", command=lambda: open_folder(last_downloaded_file),
                            bg="orange", fg="black", font=("Arial", 11, "bold"), width=15)
open_folder_btn.grid(row=0, column=1, padx=10)

tk.Label(window, text="Note: If ffmpeg is missing, video is limited to ≤720p and audio may not be MP3.", font=("Arial", 9)).pack(pady=(6,0))

window.mainloop()
