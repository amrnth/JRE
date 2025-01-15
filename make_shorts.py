import csv
import subprocess
import os
from dataclasses import dataclass
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import multiprocessing as mp
from functools import partial

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
    
    def get_subtitles_at_time(self, timestamp_ms: int) -> Optional[str]:
        entries = []
        for entry in self.entries:
            if entry.start_ms <= timestamp_ms <= entry.end_ms:
                entries.append(entry)
        
        return entries


class VideoEditor:
    def __init__(self, video_root_folder:str, video_path: str, output_path: str, subtitles: Subtitles, font_path: str = "fonts/komika-axis/KOMIKAX_.ttf", font_size:int = 42):
        self.video_path = video_path
        self.output_path = output_path
        self.subtitles = subtitles
        self.temp_dir = video_root_folder+"/temp_frames"
        self.font = ImageFont.truetype(font_path, font_size)
        self.shadow_color = (128, 128, 128)
        self.blur_radius = 30
        self.brightness_factor = 0.4
        self.shadow_offset = (5, 5)
        self.explosion_factor = 2
        self.zoom_factor = 1.9
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)

    def _extract_frames(self) -> tuple[int, float]:
        cap = cv2.VideoCapture(self.video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Create frame data generator
        def frame_generator():
            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                timestamp_ms = int((frame_number / fps) * 1000)
                yield (frame_number, timestamp_ms, frame)
                frame_number += 1

        # Use all available CPU cores minus 1
        num_processes = max(1, mp.cpu_count() - 1)
        
        with mp.Pool(num_processes) as pool:
            process_func = partial(self.process_frame, temp_dir=self.temp_dir, subtitles=self.subtitles)
            # Process frames in parallel
            list(pool.imap(process_func, frame_generator()))
        
        cap.release()
        return frame_count, fps
    
    def process_frame(self, frame_data, temp_dir, subtitles):
        frame_number, timestamp_ms, frame = frame_data


        # Convert frame from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # Get subtitle for this timestamp
        subtitle_texts = subtitles.get_subtitles_at_time(timestamp_ms)
        
        self.resize_and_add_text_to_frame(pil_image, subtitle_texts, f"{temp_dir}/frame_{frame_number:06d}.png")
    
    def resize_and_add_text_to_frame(self, image: Image.Image, texts: list[SubtitleEntry], save_frame_dir: str) -> None:
        original_width, original_height = image.size

        img = image.copy()

        image = image.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
        new_width_exploded = int(self.explosion_factor*1920*1920/1080)
        new_height_exploded = 1920 * self.explosion_factor
        image = image.resize((new_width_exploded, new_height_exploded))
        image = image.crop((new_width_exploded//2 - 1080//2, 0, new_width_exploded//2 + 1080//2, 1920))

        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.brightness_factor)

        # Resize original frame to fit within target width
        scale_factor = 1080 / original_width
        new_width =int( 1080 * self.zoom_factor)
        new_height = int(original_height * scale_factor * self.zoom_factor)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        if(self.zoom_factor != 1):
            resized_img = resized_img.crop(((new_width - 1080)//2, 0, (new_width+1080)//2, new_height))

        paste_y = (1920 - new_height) // 2

        image.paste(resized_img, (0, paste_y))

        draw = ImageDraw.Draw(image)
        
        resized_img_w = 1080
        resized_img_h = new_height
        line_spacing = 15  # Space between lines
        
        # Calculate total height needed for all texts
        total_height = 0
        text_sizes = []
        shadow_offset = self.shadow_offset
        for text in texts:
            bbox = draw.textbbox((0, 0), text.text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_sizes.append((text_width, text_height))
            total_height += text_height + line_spacing
        
        # Start position for the first line
        offset = 15
        current_y = image.size[1]//2 + resized_img_h//2 + offset
        
        # Draw each line of text
        for text, (text_width, text_height) in zip(texts, text_sizes):
            x = (resized_img_w - text_width) // 2
            # Draw text shadow and main text
            draw.text((x, current_y ), text.text, font=self.font, fill="black", stroke_width=4)
            draw.text((x, current_y), text.text, font=self.font, fill="white", stroke_width=1)
            
            current_y += text_height + line_spacing
        
        image.save(save_frame_dir)


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
        if(os.path.exists(self.output_path)):
            return self.output_path
        try:
            print("Processing ", self.output_path)
            print("Extracting and processing frames...")
            frame_count, fps = self._extract_frames()
            
            print("Combining frames into video...")
            self._combine_frames(frame_count, fps)
            
            print("Cleaning up temporary files...")
            self._cleanup()
            
            print(f"Video processing complete. Output saved to: {self.output_path}")

            return self.output_path
        
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            self._cleanup()
            raise