import csv
import os
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

class VideoTools:
    @staticmethod
    def progress_hook_yt(d):
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
    
    @staticmethod
    def get_slug_from_yt_video_url(full_url: str):
        is_short = False
        if(full_url.find("shorts") != -1):
            is_short = True

        parsed_url = urlparse(full_url)
        params = parse_qs(parsed_url.query)

        if(is_short):
            return parsed_url.path.split("/")[-1]

        return params['v'][0]

    @classmethod
    async def download_yt_video(cls, video_url: str, output_dir: str, file_name: str = "source_video.mp4") -> None:
        output_file = os.path.join(output_dir, file_name)

        if(os.path.exists(output_file)):
            return output_file

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Highest quality with audio
            'outtmpl': output_file,
            'merge_output_format': 'mp4',
            'progress_hooks': [cls.progress_hook_yt],
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'no_cache': True,

            'cookiefile': 'cookies.txt',  # Add your YouTube cookies
            'sleep_interval': 1,  # Add delay between requests
            'max_sleep_interval': 5,
            'external_downloader_args': ['--max-download-rate', '2M'],  # 
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                print(f"\nDownload completed successfully! Video saved at: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error downloading video: ", e)

    @classmethod
    async def download_yt_subtitles(cls, video_url:str, output_dir:str, file_name:str = "subtitles.csv"):
        video_slug = cls.get_slug_from_yt_video_url(video_url)

        output_file = os.path.join(output_dir, file_name)

        if(os.path.exists(output_file)):
            return output_file

        transcript = YouTubeTranscriptApi.get_transcript(video_slug)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("text,startMs,endMs\n")
                for track in transcript:
                    startMs = int(1000*float(track["start"]))
                    durationMs = int(1000*float(track["duration"]))
                    endMs = startMs+durationMs
                    f.write(f"{track['text']},{startMs},{endMs}\n")
            return output_file
        except Exception as e:
            print(f"Error downloading subtitles: ", e)

    async def get_video_info(url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_details = {
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),  # in seconds
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'upload_date': info.get('upload_date'),
                    'channel': info.get('uploader'),
                    'channel_url': info.get('uploader_url')
                }
                
                return video_details
                
        except Exception as e:
            print(f"Error downloading video info: ", e)

# def download_save_video_info(urls: list[str]):
#     csv_store = "processed_data/metadata_temp/data.csv"

#     video_details = []
#     for url in urls:
#         video_details.append(get_video_info(url))
    
#     with open(csv_store, "w", encoding="utf-8") as file:
#         csv_writer = csv.DictWriter(file,video_details[0].keys())
#         csv_writer.writeheader()
#         for vd in video_details:
#             if not vd:
#                 continue
#             csv_writer.writerow(vd)
    