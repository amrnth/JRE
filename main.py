import asyncio
from make_shorts import Subtitles, VideoEditor
from clip_new import get_intervals, offset_csv_file_timestamps, process_media_files
from llm import LLM
from utils.utils import merge_intervals
from yt_utils import VideoTools

async def perform_work(video_urls: list[str]):
    for url in video_urls:
        try:
            slug = VideoTools.get_slug_from_yt_video_url(url)
            data_folder = f"processed_data"
            video_dir = data_folder+"/"+slug
 
            results = await asyncio.gather(
                VideoTools.download_yt_video(url, video_dir), 
                VideoTools.download_yt_subtitles(url, video_dir)
            )

            [video_path, subtitles_path] = results

            reduced_subtitles_path = LLM.generate_script_gemini(video_dir, subtitles_path)

            output_video_path = video_dir + "/final_video.mp4"

            intervals = merge_intervals(get_intervals(reduced_subtitles_path))
            process_media_files(video_path, intervals, output_video_path)

            offsetted_subtitles = offset_csv_file_timestamps(reduced_subtitles_path)
            final_video_path = video_dir+"/final_video_subbed.mp4"
            
            editor = VideoEditor(video_dir, output_video_path, output_path=final_video_path, subtitles=Subtitles(offsetted_subtitles))
            editor.process_video()
        except Exception as e:
            print(f"error processing {url}: {str(e)}")
            continue

if __name__ == "__main__":
    yt_video_urls = [
        "https://www.youtube.com/shorts/9cjffFvPIrU"
        ]
    asyncio.run(perform_work(yt_video_urls))
    # download_save_video_info(yt_video_urls)