import subprocess
import sys
import os

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
    
    # Step 1: Convert PDF to text and get the .txt file path
    txt_path = run_step(
        "Running convert_pdf_to_text.py",
        ["python3.10", "convert ebook to text/convert_pdf_to_text.py"],
        capture_output=True
    )
    print(f"TXT file generated: {txt_path}")

    # Step 2: Run text_to_audio_v2.py with correct input/output file names
    if txt_path:
        mp3_path = os.path.splitext(txt_path)[0] + ".mp3"
        run_step(
            "Running text_to_audio_v2.py",
            ["python3.10", "convert text to audio/text_to_audio_v2.py", txt_path, mp3_path]
        )
        print(f"MP3 file generated: {mp3_path}")
    else:
        run_step(
            "Running text_to_audio_v2.py (fallback)",
            ["python3.10", "convert text to audio/text_to_audio_v2.py"]
        )

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
    
    # Delete .txt files in convert ebook to text
    text_ebook_dir = "convert ebook to text"
    if os.path.exists(text_ebook_dir):
        for file in os.listdir(text_ebook_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(text_ebook_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file}")
    
    print("\nAll steps completed successfully!")
    print("Pipeline completed: PDF → Text → Audio Chunks → Merged Audio Files → Cleanup") 