# This file reformats the MMMA data
import json
import re

import google.generativeai as genai
import pandas as pd

INPUT_FILE = 'total_json.json'
OUTPUT_FILE = 'reformatted_json.json'
TRANSKRIBUS_ID_FILE = 'uebersicht.csv'

def send_prompt(document_text, execute=True):
    API_KEY = "AIzaSyDWXn0RRrj9SQ7K17w2NwO2gyzx3VZ9zb4"
    PROMPT_FILE = 'prompt.txt'

    # --- Configure your API key ---
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        print(f"Error configuring Generative AI API: {e}. Please ensure your API_KEY is valid.")
        exit()

    # --- Load Prompt from File ---
    prompt_text = ""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        if not prompt_text.strip():
            print(f"Prompt file '{PROMPT_FILE}' is empty. The model might not perform as expected.")
    except FileNotFoundError:
        print(f"Prompt file '{PROMPT_FILE}' not found. Please create it with your instructions.")
        exit()
    except Exception as e:
        print(f"Error reading prompt file '{PROMPT_FILE}': {e}")
        exit()

    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt_text += "\n" + document_text

    if not execute:
        print(prompt_text)
        return '```json["tag1", "tag2", "tag3"]```'

    try:
        response = model.generate_content(
            [prompt_text]
        )

        resulting_json_list_string = response.text
        print(resulting_json_list_string)
        return resulting_json_list_string

    except Exception as e:
        print(f"Error generating content: {e}")
        exit()


################################################################################
# Load the Transkribus IDs from the CSV file
df = pd.read_csv(TRANSKRIBUS_ID_FILE, sep=";")
akte_to_transkribus = dict(zip(df["AkteNummer"].astype(str).str.zfill(3), df["Transkribus-ID"].astype(str)))

with open(INPUT_FILE, encoding='utf-8') as json_file:
    data = json.load(json_file)

# Reformatting the data
output_list = []
# Iterate over "Akten"
for dossier_key, dossier_value in data.items():
    raw_meta = dossier_key.split('_')

    if raw_meta[1] != 'Akte':
        print("KEY ERROR:", dossier_key)
    # Dossier data entry is generally valid
    else:
        # 1: Get dossier transcription
        page_transcriptions = []
        for page_key, page_value in dossier_value.items():
            page_transcriptions.append(page_value["content_transcription"])
        dossier_transcription = "\n".join(page_transcriptions)

        # 2: Get Dossier tags
        tags = []
        llm_tags = send_prompt(dossier_transcription, execute=True)
        match = re.search(r'```json\s*(\[.*?\])\s*```', llm_tags, re.DOTALL)
        if match:
            tags = json.loads(match.group(1))
        else:
            print("No valid JSON found.")

        # 3: Create the page object
        page_object = {"meta":{},
                       "attributes": {},
                       "display": {},
                       "tags": tags,
                      }


        for page_key, page_value in dossier_value.items():
            akte_nummer = raw_meta[2].zfill(3)
            transkribus_id = akte_to_transkribus.get(akte_nummer, "unknown")
            image_id = f"Akte_{raw_meta[2]}_S{page_key}.jpg"

            page_object["meta"]["dossier"] = akte_nummer
            page_object["meta"]["nodegoat_id"] = raw_meta[0]
            page_object["meta"]["page"] = page_key
            page_object["meta"]["image_id"] = image_id
            page_object["meta"]["transkribus_id"] = transkribus_id

            page_object["display"]["iiif"] = f"http://localhost:8182/iiif/2/{image_id}/full/full/0/default.jpg"

            if "document_type" in page_value["attributes"]:
                page_object["meta"]["document_type"] = page_value["attributes"]["document_type"]

            # Check if the image exists in C:\Users\sorin\Downloads\iiif-images
            image_path = f"C:\\Users\\sorin\\Downloads\\iiif-images\\{page_object['meta']['image_id']}"
            try:
                with open(image_path, 'rb') as img_file:
                    page_object["meta"]["image_exists"] = True
            except FileNotFoundError:
                page_object["meta"]["image_exists"] = False
                print(f"IMAGE NOT FOUND: {image_path}")

        output_list.append(page_object)


# Save the reformatted data to a new JSON file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
    json.dump(output_list, output_file, ensure_ascii=False, indent=4)


