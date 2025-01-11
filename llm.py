from dataclasses import dataclass
import json
import os
import typing
import google.generativeai as genai
import sys

from csv_utils import CSVUtils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@dataclass
class Schema:
    csv_file_contents: str 

class LLM:
    @staticmethod
    def get_prompt(subtitles_csv_str: str):
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
        subtitles.csv:\n'''+ subtitles_csv_str+'''

        Output:'''
        
        return hydrated_prompt
    
    @classmethod
    def generate_script_gemini(cls, output_dir: str, subtitles_csv_path: str, generated_file_name: str = "subtitles_reduced.csv"):
        generated_file_path = os.path.join(output_dir, generated_file_name)
        if(os.path.exists(generated_file_path)):
            return generated_file_path

        csv_contents = CSVUtils.get_csv_contents_as_string(subtitles_csv_path)

        hydrated_prompt = cls.get_prompt(csv_contents)

        response = cls.call_gemini(hydrated_prompt, Schema)

        response_dict = json.loads(response)

        csv_file_contents = json.loads(response_dict["csv_file_contents"])

        output_file = os.path.join(output_dir, generated_file_name)

        output_file = CSVUtils.write_subtitles_to_csv(output_file, csv_file_contents)

        return output_file

    @classmethod
    def call_gemini(cls, prompt: str, schema: typing.Type[Schema] = Schema):

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            "response_schema": schema,
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(
            history=[
            ]
        )

        response = chat_session.send_message([prompt])

        return response.text