import ffmpeg
import os
from typing import List, Tuple
import logging
from csv_utils import CSVUtils

def setup_logging():
    """Configure logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def split_media(input_file: str, output_prefix: str, intervals: List[Tuple[int, int]]) -> List[str]:
    output_files = []
    
    for idx, (start_ms, end_ms) in enumerate(intervals):
        start_sec = start_ms / 1000
        duration_sec = (end_ms - start_ms) / 1000
        
        output_file = f"{output_prefix}_segment_{idx}.mp4"
        output_files.append(output_file)
        
        try:
            stream = ffmpeg.input(input_file, ss=start_sec, t=duration_sec)
            stream = ffmpeg.output(stream, output_file, acodec='copy', vcodec='copy')
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            logger.info(f"Successfully created segment {idx + 1}: {output_file}")
            
        except ffmpeg.Error as e:
            logger.error(f"Error processing segment {idx + 1}: {str(e)}")
            raise
    
    return output_files

def create_concat_file(file_list: List[str], concat_file: str):
    """
    Create a concat demuxer file for ffmpeg
    """
    with open(concat_file, 'w') as f:
        for file_path in file_list:
            f.write(f"file '{os.path.abspath(file_path)}'\n")

def merge_media_files(file_list: List[str], output_file: str):
    """
    Merge multiple media files into a single file using the concat demuxer
    """
    concat_file = "concat_list.txt"
    create_concat_file(file_list, concat_file)
    
    try:
        stream = ffmpeg.input(concat_file, f='concat', safe=0)
        stream = ffmpeg.output(stream, output_file, c='copy')
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
        logger.info(f"Successfully merged files into: {output_file}")

        return output_file
        
    except ffmpeg.Error as e:
        logger.error(f"Error merging files: {str(e)}")
        raise
    
    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)

def clip_video(video_file: str, intervals: List[Tuple[int, int]], 
                       output_video: str):
    """
    Main function to process video and audio files
    """
    if(os.path.exists(output_video)):
        return output_video
    
    try:
        # Split video
        logger.info("Processing video segments...")
        video_segments = split_media(video_file, "temp_video", intervals)
        print("Split videos - \n", video_segments)
        
        # Merge video segments
        logger.info("Merging video segments...")
        merge_media_files(video_segments, output_video)

        # Clean up temporary files
        for file in video_segments:
            os.remove(file)
            logger.info(f"Cleaned up temporary file: {file}")
        
        return output_video
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

def get_intervals(file_name:str):
    timestamps = []

    subtitle_rows = CSVUtils.get_subtitles_as_dict(file_name)
    timestamps =[
        (row["startMs"], row["endMs"]) for row in subtitle_rows
    ]
    return timestamps
