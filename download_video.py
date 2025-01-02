from youtube_dl import YoutubeDL

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"Downloading: {d['_percent_str']} at {d['_speed_str']} ETA: {d['_eta_str']}")
    elif d['status'] == 'finished':
        print(f"Download complete: {d['filename']}")

def download_video(url: str, output_file: str):
    ydl_opts = {
        'format': 'bestvideo+bestaudio',  # Download the best quality video
        # 'outtmpl': '%(title)s.%(ext)s',  # Output filename format
        'progress_hooks': [progress_hook],  # Hook for progress updates
    }
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([url])
        if result == 0:
            with open(output_file, 'w') as f:
                f.write(f"Downloaded video from {url} successfully.\n")

# Example usage
download_video("https://www.youtube.com/watch?v=9KH4FV95ZFU", "output")
