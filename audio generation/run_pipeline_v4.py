import subprocess
import sys
import os
import yaml
import time
from datetime import datetime

# Add parent directory to path to import book_to_text
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '..'))
from book_to_text import BookToText
from text_to_speech_chunks import CoquiTTS, GTTS
from merge_audio_chunks import MergeAudioChunks

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

def read_config(config_path="audiobook_config.yaml"):
    """Read configuration from the audiobook_config.yaml file in the audio generation directory."""
    config_file = os.path.join(current_dir, config_path)
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def ensure_required_directories():
    """Make sure all directories needed by the pipeline exist."""
    project_root = os.path.dirname(current_dir)
    required_dirs = [
        os.path.join(project_root, BookToText.DEFAULT_INPUT_FOLDER),
        os.path.join(project_root, BookToText.DEFAULT_OUTPUT_FOLDER),
        os.path.join(current_dir, "audio_output"),
        os.path.join(current_dir, "merged_audio_output"),
    ]
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    # Start timing the entire pipeline
    pipeline_start_time = time.time()
    pipeline_start_dt = datetime.now()
    print(f"Pipeline started at: {pipeline_start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 0: Read configuration
    config = read_config()
    language = config.get('language', 'en')
    target_duration_minutes = config.get('target_duration_minutes', 30)
    test_mode = config.get('test', False)

    ensure_required_directories()

    # Step 2: Install dependencies
    print("=== Installing dependencies ===")
    run_step(
        "Installing TTS",
        ["python", "-m", "pip", "install", "TTS"]
    )
    run_step(
        "Installing pydub",
        ["python", "-m", "pip", "install", "pydub"]
    )
    
    # Step 3: Convert book to text using automatic format detection
    print("\n=== Converting book to text using automatic format detection ===")
    try:
        # Get project root directory
        project_root = os.path.dirname(current_dir)
        input_dir = os.path.join(project_root, BookToText.DEFAULT_INPUT_FOLDER)
        output_dir = os.path.join(project_root, BookToText.DEFAULT_OUTPUT_FOLDER)
        
        # Look for files with either PDF or EPUB extension
        file_path, extension = BookToText.get_file_by_extensions(input_dir, '.pdf', '.epub')
        
        # Get the appropriate converter for this file type
        converter = BookToText.get_converter_for_file(file_path, input_dir, output_dir)
        
        print(f"Found {extension.upper()} file: {os.path.basename(file_path)}")
        print("Converting to text...")
        
        txt_path = converter.convert_to_text(file_path)
        print(f"TXT file generated: {txt_path}")
    except Exception as e:
        print(f"Error during book to text conversion: {e}")
        sys.exit(1)
    
    print("DEBUG: About to show trimming prompt...")
    # Ask user for the first sentence to trim front matter
    print("\n" + "="*70)
    print("TRIMMING FRONT MATTER")
    print("="*70)
    print("\nBooks often have front matter (cover, table of contents, foreword, etc.)")
    print("before the actual story begins.")
    print("\nPlease enter the FIRST SENTENCE of the actual book content:")
    print("(This will be used to find and remove all text before it)")
    print("-" * 70)
    
    first_sentence = input("> ").strip()
    
    if first_sentence:
        try:
            # Read the generated text file
            with open(txt_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            # Trim the text
            trimmed_text = BookToText.trim_text_to_first_sentence(full_text, first_sentence)
            
            # Write back the trimmed text
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(trimmed_text)
            
            print("\n✓ Text trimmed successfully!")
            print(f"Removed front matter - text now starts with your specified sentence.")
        except ValueError as trim_error:
            print(f"\n⚠ Warning: {trim_error}")
            print("The text file has been saved without trimming.")
    else:
        print("\nNo input provided. Text saved as-is without trimming.")

    # Step 4: Convert text to audio using the selected TTS class
    print("\n=== Converting text to audio using selected TextToSpeechConverter class ===")
    try:
        if language == 'en':
            tts_converter = CoquiTTS(language=language)
        elif language == 'it':
            tts_converter = GTTS(language=language)
        elif language == 'es':
            tts_converter = CoquiTTS(language=language)
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
    if not test_mode:
        print("\n=== Cleaning up temporary files ===")
        
        # Get project root directory
        project_root = os.path.dirname(current_dir)
        audio_output_dir = os.path.join(current_dir, "audio_output")
        if os.path.exists(audio_output_dir):
            for file in os.listdir(audio_output_dir):
                if file.endswith('.wav') or file.endswith('.mp3'):
                    file_path = os.path.join(audio_output_dir, file)
                    os.remove(file_path)
                    print(f"Deleted: {file}")
        
        text_output_dir = os.path.join(project_root, "text_output")
        if os.path.exists(text_output_dir):
            for file in os.listdir(text_output_dir):
                if file.endswith('.txt'):
                    file_path = os.path.join(text_output_dir, file)
                    os.remove(file_path)
                    print(f"Deleted: {file}")
        
        import shutil
        # Clean up __pycache__ directories
        pycache_dirs = [
            os.path.join(project_root, "__pycache__"),
            os.path.join(project_root, "audio generation", "__pycache__")
        ]
        for pycache_dir in pycache_dirs:
            if os.path.exists(pycache_dir):
                shutil.rmtree(pycache_dir)
                print(f"Deleted: {pycache_dir}")
    else:
        print("\n=== Skipping cleanup (test mode enabled) ===")
    
    # End timing and print pipeline duration
    pipeline_end_time = time.time()
    pipeline_end_dt = datetime.now()
    pipeline_duration_hours = (pipeline_end_time - pipeline_start_time) / 3600
    print(f"\nPipeline ended at: {pipeline_end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total pipeline duration: {pipeline_duration_hours:.4f} hours")
    print("\nAll steps completed successfully!")
    print("Pipeline completed: PDF → Text → Audio Chunks → Merged Audio Files → Cleanup") 