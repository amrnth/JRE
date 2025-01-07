import ffmpeg
import os
from typing import List, Tuple
import logging
from utils.utils import merge_intervals
import csv

def setup_logging():
    """Configure logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def split_media(input_file: str, output_prefix: str, intervals: List[Tuple[int, int]], logger: logging.Logger) -> List[str]:
    """
    Split a media file according to given time intervals.
    
    Args:
        input_file: Path to input media file
        output_prefix: Prefix for output files
        intervals: List of (start_time, end_time) in milliseconds
        logger: Logger instance
    
    Returns:
        List of generated output file paths
    """
    output_files = []
    
    for idx, (start_ms, end_ms) in enumerate(intervals):
        # Convert milliseconds to seconds
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

def merge_media_files(file_list: List[str], output_file: str, logger: logging.Logger):
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

def process_media_files(video_file: str, intervals: List[Tuple[int, int]], 
                       output_video: str):
    """
    Main function to process video and audio files
    """
    if(os.path.exists(output_video)):
        return output_video
    
    try:
        # Split video
        logger.info("Processing video segments...")
        video_segments = split_media(video_file, "temp_video", intervals, logger)
        print("Split videos - \n", video_segments)
        
        # Merge video segments
        logger.info("Merging video segments...")
        merge_media_files(video_segments, output_video, logger)

        # Clean up temporary files
        for file in video_segments:
            os.remove(file)
            logger.info(f"Cleaned up temporary file: {file}")
        
        return output_video
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

def combine_video_audio(video_file: str, output_file: str, logger: logging.Logger):
    """
    Combine video and audio files into a single media file
    """
    try:
        input_video = ffmpeg.input(video_file)
        
        stream = ffmpeg.output(
            input_video,
            output_file,
            vcodec='copy',
            acodec='copy'
        )
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
        logger.info(f"Successfully combined video and audio into: {output_file}")

    except ffmpeg.Error as e:
        logger.error(f"Error combining video and audio: {str(e)}")
        raise

def get_intervals(file_name:str):
    timestamps = []
    with open(file_name, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if(row[1].isalpha()):
                continue
            timestamps.append((float(row[1]), float(row[2])))
    print("timestamps: ", timestamps)
    return timestamps

def offset_csv_file_timestamps(csv_file:str):
    new_csv_file = csv_file.split(".csv")[0] + "_offsetted.csv"
    with open(csv_file, "r") as src_csv_file:
        with open(new_csv_file, "w", newline='', encoding="utf-8") as dest_csv_file:

            reader = csv.DictReader(src_csv_file)
            field_names = reader.fieldnames

            writer = csv.DictWriter(dest_csv_file, fieldnames=field_names)
            last_val = 0.0
            writer.writeheader()
            for row in reader:
                text = row[field_names[0]]
                startMs = float(row[field_names[1]])
                endMs = float(row[field_names[2]])
                duration = endMs - startMs
                writer.writerow(
                    {
                        field_names[0]: text,
                        field_names[1]: last_val,
                        field_names[2]: duration + last_val
                    }
                )
                last_val += duration
            dest_csv_file.close()
        src_csv_file.close()
    
    return new_csv_file


def main():
    csv_file = "processed_data/4Gw-HQvo9jY/subtitles_reduced.csv"
    video_file = "processed_data/4Gw-HQvo9jY/source_video.mp4"
    final_output = "processed_data/4Gw-HQvo9jY/final_output.mp4"
    
    intervals = merge_intervals(get_intervals(csv_file))
    
    process_media_files(video_file, intervals, final_output)
    offsetted_subtitles = offset_csv_file_timestamps("processed_data/4Gw-HQvo9jY/subtitles_reduced.csv")
    