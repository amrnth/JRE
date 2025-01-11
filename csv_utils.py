


import csv
from typing import Union


class CSVUtils:

    @classmethod
    def write_subtitles_to_csv(cls, output_file: str, contents: dict[str, Union[str, int]]):
        with open(output_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["text","startMs","endMs"])
            writer.writeheader()

            for row in contents:
                writer.writerow({
                    "text": row["text"],
                    "startMs": row["startMs"],
                    "endMs":row["endMs"]
                })
                
            file.close()
        
        return output_file
    
    @classmethod
    def get_csv_contents_as_string(cls, file_path: str):
        contents = ""
        with open(file_path, "r") as file:
            for line in file.readlines():
                contents = contents + line
        
        return contents