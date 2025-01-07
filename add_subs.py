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
        self.entries: List[SubtitleEntry] = []
        self._load_subtitles(subtitle_file)
    
    def _load_subtitles(self, subtitle_file: str) -> None:
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
        for entry in self.entries:
            if entry.start_ms <= timestamp_ms <= entry.end_ms:
                return entry.text
        return None

class VideoEditor:
    def __init__(self, video_root_folder:str, video_path: str, output_path: str, subtitles: Subtitles):
        self.video_path = video_path
        self.output_path = output_path
        self.subtitles = subtitles
        self.temp_dir = video_root_folder+"/temp_frames"
        # self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _extract_frames(self) -> tuple[int, float]:
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
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-framerate', str(fps),
            '-i', f'{self.temp_dir}/frame_%06d.png',
            '-i', self.video_path,  # Add original video as second input
            '-c:v', 'libx264',
            '-c:a', 'copy',         # Copy audio without re-encoding
            '-map', '0:v:0',        # Use video from first input (frames)
            '-map', '1:a:0',        # Use audio from second input (original video)
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