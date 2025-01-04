import csv
import subprocess
import os
from dataclasses import dataclass
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

@dataclass
class SubtitleEntry:
    text: str
    start_ms: int
    end_ms: int

class Subtitles:
    def __init__(self, subtitle_file: str):
        """
        Initialize the Subtitles class with a CSV file containing subtitle data.
        
        Args:
            subtitle_file (str): Path to the CSV file with columns: text, startMs, endMs
        """
        self.entries: List[SubtitleEntry] = []
        self._load_subtitles(subtitle_file)
    
    def _load_subtitles(self, subtitle_file: str) -> None:
        """
        Load subtitles from the CSV file into memory.
        """
        with open(subtitle_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                entry = SubtitleEntry(
                    text=row['text'],
                    start_ms=int(float(row['startMs'])),
                    end_ms=int(float(row['endMs']))
                )
                self.entries.append(entry)
    
    def get_subtitle_at_time(self, timestamp_ms: int) -> Optional[str]:
        """
        Get the subtitle text that should be displayed at a given timestamp.
        
        Args:
            timestamp_ms (int): Timestamp in milliseconds
            
        Returns:
            Optional[str]: Subtitle text if one should be displayed, None otherwise
        """
        for entry in self.entries:
            if entry.start_ms <= timestamp_ms <= entry.end_ms:
                return entry.text
        return None

class VideoEditor:
    def __init__(self, video_path: str, output_path: str, subtitles: Subtitles):
        """
        Initialize the VideoEditor with input video and subtitles.
        
        Args:
            video_path (str): Path to the input video file
            output_path (str): Path where the output video will be saved
            subtitles (Subtitles): Subtitles object containing the subtitle entries
        """
        self.video_path = video_path
        self.output_path = output_path
        self.subtitles = subtitles
        self.temp_dir = "temp_frames"
        # self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _extract_frames(self) -> tuple[int, float]:
        """
        Extract frames from the video and return the frame count and FPS.
        
        Returns:
            tuple[int, float]: (frame_count, fps)
        """
        cap = cv2.VideoCapture(self.video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_number = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Calculate timestamp for this frame
            timestamp_ms = int((frame_number / fps) * 1000)
            
            # Get subtitle for this timestamp
            subtitle_text = self.subtitles.get_subtitle_at_time(timestamp_ms)
            
            if subtitle_text:
                # Add subtitle to the frame
                self._add_subtitle_to_frame(pil_image, subtitle_text)
            
            # Save the frame
            pil_image.save(f"{self.temp_dir}/frame_{frame_number:06d}.png")
            frame_number += 1
        
        cap.release()
        return frame_count, fps
    
    def _add_subtitle_to_frame(self, image: Image.Image, text: str) -> None:
        """
        Add large subtitle text to a frame using system default font.
        
        Args:
            image (Image.Image): PIL Image object of the frame
            text (str): Subtitle text to add
        """
        draw = ImageDraw.Draw(image)
        
        # Set a large font size
        font = ImageFont.load_default()
        font_size = 48  # Increase this value for larger text
        font = font.font_variant(size=font_size)
        
        # Calculate text size and position
        img_w, img_h = image.size
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Position text at bottom center with padding
        x = (img_w - text_width) // 2
        y = img_h - text_height - 80
        
        # Draw text shadow for better visibility
        shadow_offset = 0
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill="black", stroke_width=10)
        draw.text((x, y), text, font=font, fill="white", stroke_width=1)


    def _combine_frames(self, frame_count: int, fps: float) -> None:
        """
        Combine the processed frames back into a video using ffmpeg.
        
        Args:
            frame_count (int): Total number of frames
            fps (float): Frames per second of the original video
        """
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-framerate', str(fps),
            '-i', f'{self.temp_dir}/frame_%06d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '23',
            self.output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
    
    def _cleanup(self) -> None:
        """Remove temporary files and directory."""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def process_video(self) -> None:
        """
        Process the video by extracting frames, adding subtitles, and combining frames.
        """
        try:
            print("Extracting and processing frames...")
            frame_count, fps = self._extract_frames()
            
            print("Combining frames into video...")
            self._combine_frames(frame_count, fps)
            
            print("Cleaning up temporary files...")
            self._cleanup()
            
            print(f"Video processing complete. Output saved to: {self.output_path}")
        
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            self._cleanup()
            raise

def main():
    subtitle_file = "example_data/reduced_transcript_offsetted.csv"
    input_video = "example_vids/final_output.mp4"
    output_video = "output_with_subs2.mp4"
    
    subtitles = Subtitles(subtitle_file)
    editor = VideoEditor(input_video, output_video, subtitles)
    editor.process_video()

if __name__ == "__main__":
    main()