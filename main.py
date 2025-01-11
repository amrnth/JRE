import asyncio
from make_shorts import Subtitles, VideoEditor
from clip_new import get_intervals, offset_csv_file_timestamps, process_media_files
from prompts.prompt import generate_reduced_subtitles
from utils.utils import merge_intervals
from utils.yt_utils import download_save_video_info, download_subtitles, download_youtube_video, get_slug_from_full_url


async def perform_work(video_urls: list[str]):
    for url in video_urls:
        try:
            slug = get_slug_from_full_url(url)
            data_folder = f"processed_data"
            path_prefix = data_folder+"/"+slug

            results = await asyncio.gather(
                download_youtube_video(data_folder, slug), # create a check so that re-download doesn't happen if video is already present
                download_subtitles(data_folder, slug)
            )

            [video_path, subtitles_path] = results

            reduced_subtitles_path = generate_reduced_subtitles(subtitles_path)

            output_video_path = path_prefix + "/final_video.mp4"

            intervals = merge_intervals(get_intervals(reduced_subtitles_path))
            process_media_files(video_path, intervals, output_video_path)

            offsetted_subtitles = offset_csv_file_timestamps(reduced_subtitles_path)
            final_video_path = path_prefix+"/final_video_subbed.mp4"
            
            editor = VideoEditor(path_prefix, output_video_path, output_path=final_video_path, subtitles=Subtitles(offsetted_subtitles))
            editor.process_video()
        except:
            continue
if __name__ == "__main__":
    yt_video_urls = [
        ]
    asyncio.run(perform_work(yt_video_urls))
    # download_save_video_info(yt_video_urls)