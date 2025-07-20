from gtts import gTTS
import os
import sys
import time
from datetime import datetime

# Set the language for the AI voice (e.g., 'en' for English, 'it' for Italian)
LANGUAGE = 'it'  # Change this to your desired language code

# Function to find the first .txt file in the convert ebook to text folder
def get_first_txt_file(folder_path):
    # Navigate to the "convert ebook to text" folder
    convert_folder = os.path.join(os.path.dirname(folder_path), "convert ebook to text")
    for filename in os.listdir(convert_folder):
        if filename.lower().endswith('.txt'):
            return os.path.join(convert_folder, filename)
    return None

# Read the text from the file
def main():
    start_time = time.time()
    start_dt = datetime.now()
    print(f"executing script at {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # Accept input and output file paths as arguments
    input_file = None
    output_mp3 = None
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_mp3 = sys.argv[2]

    folder_path = os.path.dirname(os.path.abspath(__file__))
    input_file = get_first_txt_file(folder_path)
    if not input_file:
        print("No .txt file found in the directory.")
        return
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()
    except UnicodeDecodeError:
        with open(input_file, 'r', encoding='latin-1') as file:
            text = file.read()

    # Convert the text to speech using the specified language
    tts = gTTS(text, lang=LANGUAGE)

    # Save the audio file
    tts.save('output.mp3')
    print(f"Audio file 'output.mp3' has been created using language '{LANGUAGE}' from file '{input_file}'.")

    end_time = time.time()
    end_dt = datetime.now()
    duration_hours = (end_time - start_time) / 3600
    print(f"done at: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"it took {duration_hours:.4f} hours")

if __name__ == "__main__":
    main() 