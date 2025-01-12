
import json
import time
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
from math import ceil
import os
import pandas as pd
from pydub import AudioSegment

from make_shorts import VideoEditor


def merge_audio_files(root_folder):
   audio_files = sorted([f for f in os.listdir(root_folder) if f.endswith('.mp3')])
   if not audio_files:
       return
   
   combined = AudioSegment.empty()
   timings = []
   current_pos = 0
   
   for audio_file in audio_files:
       segment = AudioSegment.from_mp3(os.path.join(root_folder, audio_file))
       duration = len(segment)
       timings.append({
           'file': audio_file,
           'start_time': current_pos,
           'end_time': current_pos + duration
       })
       combined += segment
       current_pos += duration

   combined.export(os.path.join(root_folder, "audio.m4a"), format="mp4", codec="aac")
   
   df = pd.DataFrame(timings)
   df.to_csv(os.path.join(root_folder, "audio_timings.csv"), index=False)

def load_data(summary_path, timings_path):
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    timings_df = pd.read_csv(timings_path)
    return summary, timings_df

def create_frame(image_path, text, current_frame, total_frames, width=1080, height=1920):
    # Create base frame
    frame = Image.new('RGB', (width, height), color='black')
    
    # Load and resize background image
    bg_image = Image.open(image_path)
    img_w, img_h = bg_image.size
    bg_image = bg_image.resize((width, int(img_h*width/img_w)), Image.Resampling.LANCZOS)
    frame.paste(bg_image, (0, 0))
    
    # Add text at bottom
    draw = ImageDraw.Draw(frame)
    font = ImageFont.truetype("fonts/Times-New-Roman/Times New Roman/times new roman.ttf", 64)
    
    # Calculate text position and wrap text
    margin = 40
    text_width = width - 2 * margin
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if draw.textlength(test_line, font=font) > text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    # Draw text
    text_height = len(lines) * font.size
    y_position = height - text_height - margin
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x_position = (width - text_width) // 2
        draw.text((x_position, y_position), line, font=font, fill='white')
        y_position += font.size
    
    return frame

def generate_segment_frames(content, start_time, end_time, fps=5, prev_count = 0):
    duration = end_time - start_time
    num_frames = ceil(duration * fps / 1000)  # duration is in milliseconds
    # Save identical frames
    frames_paths = []
    for i in range(prev_count, num_frames+prev_count):
        frame = create_frame(content['image'], content['text'], i-prev_count, num_frames)
        # Create temporary directory for frames if it doesn't exist
        os.makedirs('news_shorts/temp_frames', exist_ok=True)
        frame_path = f'news_shorts/temp_frames/frame_{i:04d}.png'
        frame.save(frame_path, quality=95)
        frames_paths.append(frame_path)
    
    return frames_paths

def create_video_segments(summary, timings_df, fps=5):
    all_frame_paths = []
    prev_count = 0
    for i, (_, timing) in enumerate(timings_df.iterrows()):
        content = summary['contents'][i]
        frame_paths = generate_segment_frames(
            content,
            int(timing['start_time']),
            int(timing['end_time']),
            fps,
            prev_count
        )
        prev_count += len(frame_paths)
        all_frame_paths.extend(frame_paths)
    
    return all_frame_paths

def create_final_video(frame_paths, audio_path, output_path, fps=5):
    # # Create temporary file with frame paths
    # with open('news_shorts/temp_frames.txt', 'w') as f:
    #     for path in frame_paths:
    #         f.write(f"file '{path}'\n")
    #         f.write(f"duration {1/fps}\n")
    # print("Here?")
    # time.sleep(20)
    # Use ffmpeg to create video with audio
    if not os.path.exists('news_shorts/temp_frames'):
        raise FileNotFoundError("Temporary frames directory not found")
    if not frame_paths:
        raise ValueError("No frames were generated")
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', 'news_shorts/temp_frames/frame_%04d.png',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-c:a', 'copy',
        '-shortest',
        output_path
    ]
    subprocess.run(cmd)
    
    # Cleanup temporary files
    # os.remove('news_shorts/temp_frames.txt')
    # for frame_path in frame_paths:
    #     os.remove(frame_path)
    # os.rmdir('news_shorts/temp_frames')

def main():
    # merge_audio_files("news_shorts/")
    summary, timings_df = load_data('news_shorts/summary.json', 'news_shorts/audio_timings.csv')
    print(summary)
    frame_paths = create_video_segments(summary, timings_df, fps=5)
    create_final_video(frame_paths, 'news_shorts/audio.m4a', 'news_shorts/final_video.mp4', fps=5)

if __name__ == "__main__":
    main()