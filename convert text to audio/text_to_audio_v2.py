# Requires: pip install TTS
import os
import sys
import torch
from TTS.api import TTS

X = 111  # Number of lines to skip at the start of the text
language = "en"

language_model_dict = {
    "en": "tts_models/en/ljspeech/fast_pitch",
    "it": "tts_models/it/mai_female/glow-tts", #best one in italian but it's a bit robotic
    "es": "tts_models/es/mai_female/vits",  # Spanish female voice (if available)
}

# Set device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize TTS
print("Loading TTS model...")
model_name = language_model_dict[language]
tts = TTS(model_name).to(device)
print("TTS model loaded successfully!")

def clean_text(text):
    """Clean text for TTS processing"""
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    # Replace multiple spaces with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    # Remove any non-printable characters except newlines
    text = ''.join(char for char in text if char.isprintable() or char == '\n')
    return text.strip()

def split_text_into_chunks(text, chunk_size=5000):
    """Split text into chunks of approximately chunk_size characters"""
    # Clean the text first
    text = clean_text(text)
    
    words = text.split()
    chunks = []
    current_chunk = ''
    
    for word in words:
        if len(current_chunk) + len(word) + 1 <= chunk_size:
            current_chunk += (' ' if current_chunk else '') + word
        else:
            if current_chunk:  # Only add non-empty chunks
                chunks.append(current_chunk)
            current_chunk = word
    
    if current_chunk:  # Add the last chunk if it's not empty
        chunks.append(current_chunk)
    
    return chunks

def get_input_file():
    """Get input text file from argument, or fetch the first .txt file in the convert ebook to text directory"""
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' not found.")
            return None
        return input_file
    
    # Look for .txt files in the convert ebook to text directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    ebook_text_dir = os.path.join(project_root, "convert ebook to text")
    
    if not os.path.exists(ebook_text_dir):
        print(f"Error: Directory '{ebook_text_dir}' not found.")
        return None
    
    txt_files = [f for f in os.listdir(ebook_text_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"Error: No .txt files found in '{ebook_text_dir}' directory.")
        return None
    
    # Use the first .txt file found
    input_file = os.path.join(ebook_text_dir, txt_files[0])
    print(f"Using input file: {input_file}")
    return input_file

def main():
    # Get input file
    input_file = get_input_file()
    if not input_file:
        return
    
    # Read the text file
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Original text length: {len(text)} characters")
    
    # Skip the first X lines
    lines = text.split('\n')
    if len(lines) > X:
        text = '\n'.join(lines[X:])
        print(f"Skipped first {X} lines. Remaining text length: {len(text)} characters")
    
    # Split text into chunks
    chunks = split_text_into_chunks(text, chunk_size=5000)
    print(f"Split text into {len(chunks)} chunks")
    
    # Create output directory in the main project folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, "audio_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each chunk
    for i, chunk in enumerate(chunks):
        # Skip very short chunks that might cause issues
        if len(chunk.strip()) < 20:
            print(f"Skipping chunk {i+1}/{len(chunks)}: too short ({len(chunk.strip())} chars)")
            continue
            
        output_path = os.path.join(output_dir, f'chunk_{i+1}.wav')
        print(f"Synthesizing chunk {i+1}/{len(chunks)} to {output_path} ...", flush=True)
        
        try:
            tts.tts_to_file(text=chunk, file_path=output_path)
            print(f"Chunk {i+1}/{len(chunks)} saved to file: {output_path}", flush=True)
        except Exception as e:
            print(f"Error processing chunk {i+1}/{len(chunks)}: {e}")
            print(f"Chunk content (first 100 chars): {chunk[:100]}...")
            continue
    
    print("Text-to-audio conversion completed!")

if __name__ == "__main__":
    main() 