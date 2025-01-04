import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment
from pydub.utils import which
AudioSegment.converter = which("ffmpeg")

# File paths
csv_file = "example_data/reduced_transcript.csv"
video_file = "input_video.mp4"
audio_file = "input_audio.m4a"
output_file = "edited_video.mp4"
final_output = "example_data/final_output.mp4"

# Load CSV data
df = pd.read_csv(csv_file)

# Combine overlapping or adjacent intervals
def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Sort intervals by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for current in intervals[1:]:
        last = merged[-1]
        # Check for overlap or adjacency
        if current[0] <= last[1]:  # Overlapping or touching intervals
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    
    return merged

# Extract start and end times from the CSV
intervals = [(row['startMs']/1000, row['endMs']/1000) for _, row in df.iterrows()]
merged_intervals = merge_intervals(intervals)

# Initialize lists to store video clips
video_clips = []

# Load the original video
video = VideoFileClip(video_file)

# Create clips based on merged intervals
for start_time, end_time in merged_intervals:
    # Create subclips for video
    video_clip = video.subclip(start_time, end_time)
    video_clips.append(video_clip)

# Concatenate all video clips into one video
final_video = concatenate_videoclips(video_clips)

# Process the audio separately using pydub
audio = AudioSegment.from_file(audio_file, format="m4a")
audio_clips = []

for start_time, end_time in merged_intervals:
    # Extract audio segments in milliseconds
    audio_clip = audio[start_time * 1000:end_time * 1000]
    audio_clips.append(audio_clip)

# Combine audio clips
final_audio = sum(audio_clips)

# Export the final audio without re-encoding
final_audio_path = "final_audio.m4a"
final_audio.export(final_audio_path, format="m4a", codec="copy")

# Set the concatenated audio to the final video
final_video = final_video.set_audio(final_audio_path)

# Write the result to a file
final_video.write_videofile(output_file, codec="libx264", audio_codec="aac")

# Close video objects
video.close()
final_video.close()
