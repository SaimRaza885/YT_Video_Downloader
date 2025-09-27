import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp

# Function to start the download
def download_video():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    # Ask user where to save the file
    save_path = filedialog.askdirectory()
    if not save_path:
        return

    # Show loading message
    status_label.config(text="Downloading... Please wait.", fg="blue")
    window.update_idletasks()

    try:
        ydl_opts = {
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',  # Save with title as filename
            'merge_output_format': 'mp4',  # Final file format
            'format': 'bestvideo+bestaudio/best',  # Best quality video+audio
            'postprocessors': [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',  # Remux to mp4 without re-encoding
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_label.config(text="✅ Download Complete!", fg="green")
        messagebox.showinfo("Success", "Download finished successfully!")

    except Exception as e:
        status_label.config(text="❌ Download Failed", fg="red")
        messagebox.showerror("Error", str(e))


# ----------------- UI Setup -----------------
window = tk.Tk()
window.title("YouTube Video Downloader")
window.geometry("500x250")
window.resizable(False, False)

# Heading
heading = tk.Label(window, text="YouTube Downloader", font=("Arial", 16, "bold"))
heading.pack(pady=10)

# URL Entry
url_label = tk.Label(window, text="Enter YouTube URL:", font=("Arial", 12))
url_label.pack()

url_entry = tk.Entry(window, width=50, font=("Arial", 12))
url_entry.pack(pady=5)

# Download Button
download_btn = tk.Button(window, text="Download Video", command=download_video,
                         font=("Arial", 12, "bold"), bg="blue", fg="white")
download_btn.pack(pady=10)

# Status Label
status_label = tk.Label(window, text="", font=("Arial", 12))
status_label.pack(pady=10)

# Run the UI
window.mainloop()
