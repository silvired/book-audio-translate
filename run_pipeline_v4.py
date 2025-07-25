import subprocess
import sys
import os
import yaml
from book_to_text import PDFToText
from text_to_speech_chunks import CoquiTTS, GTTS
from merge_audio_chunks import MergeAudioChunks
import time
from datetime import datetime

def run_step(description, command, capture_output=False):
    print(f"\n=== {description} ===")
    try:
        if capture_output:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            result = subprocess.run(command, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        sys.exit(1)

def read_config(config_path="config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    # Start timing the entire pipeline
    pipeline_start_time = time.time()
    pipeline_start_dt = datetime.now()
    print(f"Pipeline started at: {pipeline_start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 0: Read configuration
    config = read_config()
    language = config.get('language', 'en')
    input_file_type = config.get('input_file_type', 'PDF')
    skip_lines = config.get('skip_lines', 111)
    target_duration_minutes = config.get('target_duration_minutes', 30)

    # Step 1: Check input file type
    if input_file_type != 'PDF':
        print("the file type you selected is not supported yet")
        sys.exit(1)

    # Step 2: Install dependencies
    print("=== Installing dependencies ===")
    run_step(
        "Installing TTS",
        ["python3.10", "-m", "pip", "install", "TTS"]
    )
    run_step(
        "Installing pydub",
        ["python3.10", "-m", "pip", "install", "pydub"]
    )
    
    # Step 3: Convert PDF to text using object-oriented approach
    print("\n=== Converting PDF to text using PDFToText class ===")
    try:
        pdf_converter = PDFToText()
        txt_path = pdf_converter.convert_first_pdf()
        print(f"TXT file generated: {txt_path}")
    except Exception as e:
        print(f"Error during PDF to text conversion: {e}")
        sys.exit(1)

    # Step 4: Convert text to audio using the selected TTS class
    print("\n=== Converting text to audio using selected TextToSpeechConverter class ===")
    try:
        if language == 'en':
            tts_converter = CoquiTTS(skip_lines=skip_lines)
        elif language == 'it':
            tts_converter = GTTS(language=language)
            tts_converter.skip_lines = skip_lines
        else:
            print(f"Language '{language}' is not supported yet for TTS.")
            sys.exit(1)
        first_chunk_path = tts_converter.convert_to_speech(txt_path)
        if first_chunk_path:
            print(f"First audio chunk generated: {first_chunk_path}")
        else:
            print("No audio chunks were generated")
    except Exception as e:
        print(f"Error during text to audio conversion: {e}")
        sys.exit(1)

    # Step 5: Merge audio chunks into files of the configured duration
    print(f"\n=== Merging audio chunks into {target_duration_minutes}-minute files using MergeAudioChunks class ===")
    try:
        audio_merger = MergeAudioChunks(target_duration_minutes=target_duration_minutes)
        num_merged_files = audio_merger.merge_chunks()
        print(f"Successfully created {num_merged_files} merged audio files")
    except Exception as e:
        print(f"Error during audio merging: {e}")
        sys.exit(1)

    # Step 6: Cleanup temporary files
    print("\n=== Cleaning up temporary files ===")
    audio_output_dir = "audio_output"
    if os.path.exists(audio_output_dir):
        for file in os.listdir(audio_output_dir):
            if file.endswith('.wav'):
                file_path = os.path.join(audio_output_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file}")
    text_output_dir = "text_output"
    if os.path.exists(text_output_dir):
        for file in os.listdir(text_output_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(text_output_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file}")
    import shutil
    pycache_dirs = [
        "__pycache__",
        "convert text to audio/__pycache__"
    ]
    for pycache_dir in pycache_dirs:
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)
            print(f"Deleted: {pycache_dir}")
    
    # End timing and print pipeline duration
    pipeline_end_time = time.time()
    pipeline_end_dt = datetime.now()
    pipeline_duration_hours = (pipeline_end_time - pipeline_start_time) / 3600
    print(f"\nPipeline ended at: {pipeline_end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total pipeline duration: {pipeline_duration_hours:.4f} hours")
    print("\nAll steps completed successfully!")
    print("Pipeline completed: PDF → Text → Audio Chunks → Merged Audio Files → Cleanup") 