import json

import google.generativeai as genai

def send_prompt(document_text):
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


INPUT_FILE = 'total_json.json'
results = []
with open(INPUT_FILE, encoding='utf-8') as json_file:
    data = json.load(json_file)

for a_key, a_value in data.items():
    akten_text = """
Transcription:
=============="""

    for p_key, p_value in a_value.items():
        akten_text += f"""
- Type {p_value["attributes"]["document_type"]}
- Page {p_key}:
{p_value["content_transcription"]}\n\n///\n\n"""

    akten_text = akten_text[:-5]  # Remove the last newline and slashes
    answer = send_prompt(akten_text)
    results.append(answer)


resulting_string = "\n".join(results)
OUTPUT_FILE = 'gemini_results.json'
with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
    json.dump(resulting_string, output_file, ensure_ascii=False, indent=4)
