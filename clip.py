import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Load CSV data
csv_file = "reduced_transcript.csv"
video_file = "prison.mp4"
output_file = "edited_video.mp4"

# Read the CSV file
df = pd.read_csv(csv_file)

# Initialize a list to store video clips
clips = []

# Load the original video
video = VideoFileClip(video_file)

# start-time, start-time+duration
intervals = []

# Loop over each row in the DataFrame and create video clips
for _, row in df.iterrows():
    start_time = row['start']
    duration = row['duration']
    end_time = start_time + duration
    
    # Create a subclip from the start time to end time
    clip = video.subclip(start_time, end_time)
    clips.append(clip)

# Concatenate all clips into one video
final_video = concatenate_videoclips(clips)

# Write the result to a file
final_video.write_videofile(output_file, codec="libx264", audio_codec="aac")

# Close video objects
video.close()
final_video.close()
