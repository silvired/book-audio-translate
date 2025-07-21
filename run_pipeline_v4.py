import subprocess
import sys
import os
from book_to_text import PDFToText
from text_to_speech_chunks import CoquiTTS

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

if __name__ == "__main__":
    # Step 0: Install dependencies
    print("=== Installing dependencies ===")
    run_step(
        "Installing TTS",
        ["python3.10", "-m", "pip", "install", "TTS"]
    )
    run_step(
        "Installing pydub",
        ["python3.10", "-m", "pip", "install", "pydub"]
    )
    
    # Step 1: Convert PDF to text using object-oriented approach
    print("\n=== Converting PDF to text using PDFToText class ===")
    try:
        # Initialize the PDFToText object
        pdf_converter = PDFToText()
        
        # Convert the first PDF file in the input folder to text
        txt_path = pdf_converter.convert_first_pdf()
        print(f"TXT file generated: {txt_path}")
    except Exception as e:
        print(f"Error during PDF to text conversion: {e}")
        sys.exit(1)

    # Step 2: Convert text to audio using object-oriented approach
    print("\n=== Converting text to audio using CoquiTTS class ===")
    try:
        # Initialize the CoquiTTS object
        tts_converter = CoquiTTS()
        
        # Convert the text file to audio chunks
        first_chunk_path = tts_converter.convert_to_speech(txt_path)
        if first_chunk_path:
            print(f"First audio chunk generated: {first_chunk_path}")
        else:
            print("No audio chunks were generated")
    except Exception as e:
        print(f"Error during text to audio conversion: {e}")
        sys.exit(1)

    # Step 3: Merge audio chunks into 30-minute files
    run_step(
        "Merging audio chunks into 30-minute files",
        ["python3.10", "merge_audio_chunks.py"]
    )
    
    # Step 4: Cleanup temporary files
    print("\n=== Cleaning up temporary files ===")
    
    # Delete all files in audio_output (main project folder)
    audio_output_dir = "audio_output"
    if os.path.exists(audio_output_dir):
        for file in os.listdir(audio_output_dir):
            if file.endswith('.wav'):
                file_path = os.path.join(audio_output_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file}")
    
    # Delete .txt files in text_output folder
    text_output_dir = "text_output"
    if os.path.exists(text_output_dir):
        for file in os.listdir(text_output_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(text_output_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file}")
    
    # Delete __pycache__ folders
    import shutil
    pycache_dirs = [
        "__pycache__"
    ]
    for pycache_dir in pycache_dirs:
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)
            print(f"Deleted: {pycache_dir}")
    
    print("\nAll steps completed successfully!")
    print("Pipeline completed: PDF → Text → Audio Chunks → Merged Audio Files → Cleanup") 