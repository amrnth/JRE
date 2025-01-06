import os
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

from constants import ROOT_RESULTS_FOLDER

def progress_hook(d):
    """
    Hook to track download progress.
    """
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        
        if total_bytes:
            progress = (downloaded_bytes / total_bytes) * 100
            speed = d.get('speed', 0)
            if speed:
                speed_mb = speed / 1024 / 1024  # Convert to MB/s
                print(f'\rProgress: {progress:.1f}% - Speed: {speed_mb:.1f} MB/s', end='')
            else:
                print(f'\rProgress: {progress:.1f}%', end='')
    elif d['status'] == 'finished':
        print('\nDownload finished, now converting...')


def download_youtube_video(video_slug: str) -> None:
    # Create output directory
    output_dir = os.path.join(os.getcwd(), ROOT_RESULTS_FOLDER, video_slug)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'source_video.%(ext)s')
    print(output_dir)
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Highest quality with audio
        'outtmpl': output_file,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': False,
    }
    
    # Download the video
    url = f'https://www.youtube.com/watch?v={video_slug}'
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print(f"\nDownload completed successfully! Video saved in: {output_dir}")
        return output_dir
    except Exception as e:
        print(f"Error downloading video: {str(e)}")

def download_subtitles(video_slug):
    transcript = YouTubeTranscriptApi.get_transcript(video_slug)

    output_file = os.path.join(os.getcwd(), ROOT_RESULTS_FOLDER, video_slug, "subtitles.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("text,startMs,endMs\n")
        for track in transcript:
            startMs = int(1000*float(track["start"]))
            durationMs = int(1000*float(track["duration"]))
            endMs = startMs+durationMs
            f.write(f"{track['text']},{startMs},{endMs}\n")
    
    return output_file