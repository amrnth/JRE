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
    def get_subtitles_as_dict(cls, file_path: str):
        rows = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for r in reader:
                rows.append(r)
                r.update({
                    "startMs": int(r["startMs"]),
                    "endMs": int(r["endMs"])
                })
        return rows
    
    @classmethod
    def get_csv_contents_as_string(cls, file_path: str):
        contents = ""
        with open(file_path, "r") as file:
            for line in file.readlines():
                contents = contents + line
        
        return contents
    
    @classmethod
    def offset_csv_file_timestamps(cls, csv_file:str):
        new_csv_file = csv_file.split(".csv")[0] + "_offsetted.csv"

        rows = cls.get_subtitles_as_dict(csv_file)

        rows.sort(key=lambda x: (x["startMs"], x["endMs"]))

        diff = rows[0]["startMs"]

        rows[0]["startMs"] -= diff
        rows[0]["endMs"] -= diff

        for i in range(1, len(rows)):
            if(rows[i]["startMs"] <= diff + rows[i-1]["endMs"]):
                rows[i]["startMs"] -= diff
                rows[i]["endMs"] -= diff
            else:
                temp = rows[i]["endMs"] - rows[i]["startMs"]
                temp2 = rows[i]["startMs"] - rows[i-1]["endMs"]

                rows[i]["startMs"] = rows[i-1]["endMs"]
                rows[i]["endMs"] = rows[i]["startMs"] + temp

                diff = temp2

        cls.write_subtitles_to_csv(new_csv_file, rows)
        
        return new_csv_file