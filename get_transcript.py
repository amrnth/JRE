import json
import csv

def get_transcript_from_file(file_url):
    with open(file_url, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    segments = data["actions"][0]["updateEngagementPanelAction"]["content"]["transcriptRenderer"]["content"]["transcriptSearchPanelRenderer"]["body"]["transcriptSegmentListRenderer"]["initialSegments"]
    
    with open('transcript-new.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['text', 'startMs', 'endMs']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for segment in segments:
            transcript_segment = segment["transcriptSegmentRenderer"]
            start_ms = transcript_segment["startMs"]
            end_ms = transcript_segment["endMs"]
            text = ''.join([run["text"] for run in transcript_segment["snippet"]["runs"]])
            writer.writerow({'text': text, 'startMs': start_ms, 'endMs': end_ms })

def get_transcript_from_video_url(video_slug):
    pass

get_transcript_from_file("example_transcript.json")

# import os
# from youtube_transcript_api import YouTubeTranscriptApi

# def download_subtitles():
#     """
#     Download subtitles from a YouTube video and save them to a text file.
    
#     Parameters:
#     video_url (str): The URL of the YouTube video
#     output_file (str): The path to the output text file
#     """
#     # Download the video and subtitles
#     transcript = YouTubeTranscriptApi.get_transcript('bEWdAYvANcc')

#     with open("subtitles.txt", 'w', encoding='utf-8') as f:
#         f.write("text,start,duration\n")
#         for track in transcript:
#             f.write(f"{track['text']},{track['start']},{track['duration']}\n")

# download_subtitles()