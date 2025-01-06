import csv
from dataclasses import dataclass
import json
import os
import google.generativeai as genai
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@dataclass
class Schema:
  csv_file_contents: str 
  
def generate_reduced_subtitles(full_subtitles_csv: str):
  generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    "response_schema": Schema,
  }

  model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
  )

  chat_session = model.start_chat(
    history=[
    ]
  )

  subtitles_csv = ""
  with open(full_subtitles_csv) as file:
      for line in file.readlines():
          subtitles_csv = subtitles_csv + line

  hydrated_prompt = '''
  You are an experienced content creator and storyteller. You have to perform the following job:

  TASK:
  Extract a ~1 minute coherent story segment by selecting contiguous rows from the input CSV.

  REQUIREMENTS:
  1. Story Structure:
    - Must have clear beginning, middle, and end (or deliberate cliffhanger)
    - Must be coherent and self-contained
    - Should be ~1 minute in total duration
    - Must use contiguous rows only

  INPUT FORMAT:
  - CSV file with 3 columns: text (speech content), start_time, duration
  - File represents subtitles from a 10-15 minute video
  - CSV structure: text,start_time,duration

  2. Constraints:
    - Can only use existing text (no modifications)
    - Must preserve original timestamps
    - Must maintain row order
    - Total duration ≈ 60 seconds

  SELECTION CRITERIA:
  1. Story completeness
  2. Narrative coherence
  3. Natural dialogue flow
  4. Duration limits

  INPUT:
  subtitles.csv:\n'''+ subtitles_csv+'''

  Output:'''

  response = chat_session.send_message(hydrated_prompt)
  response_dict = json.loads(response.text)

  csv_file_contents = json.loads(response_dict["csv_file_contents"])

  destination_folder = full_subtitles_csv.split("subtitles.csv")[0]
  output_file = destination_folder + "subtitles_reduced.csv"

  with open(output_file, "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["text","startMs","endMs"])
    writer.writeheader()

    for row in csv_file_contents:
       writer.writerow({
          "text": row["text"],
          "startMs": row["startMs"],
          "endMs":row["endMs"]
       })

generate_reduced_subtitles("D:/Projects/JREFan/processed_data/4Gw-HQvo9jY/subtitles.csv")