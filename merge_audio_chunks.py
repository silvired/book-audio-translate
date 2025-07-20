#!/usr/bin/env python3
"""
Script to merge audio chunks into 30-minute files.
This script takes all the .wav files from the audio_output directory
and merges them into larger files, each approximately 30 minutes long.
"""

import os
import glob
import re
from pydub import AudioSegment
from pydub.utils import make_chunks

def natural_sort_key(text):
    """Sort strings containing numbers naturally"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

def get_audio_duration(audio_segment):
    """Get duration of audio segment in minutes"""
    return len(audio_segment) / (1000 * 60)  # Convert milliseconds to minutes

def merge_audio_chunks(input_dir="audio_output", 
                      output_dir="merged_audio_output", 
                      target_duration_minutes=30):
    """
    Merge audio chunks into larger files of specified duration.
    
    Args:
        input_dir (str): Directory containing the audio chunks
        output_dir (str): Directory to save merged audio files
        target_duration_minutes (int): Target duration for each merged file in minutes
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .wav files in the input directory
    wav_files = glob.glob(os.path.join(input_dir, "*.wav"))
    
    if not wav_files:
        print(f"No .wav files found in {input_dir}")
        return
    
    # Sort files naturally (chunk_1.wav, chunk_2.wav, ..., chunk_10.wav, etc.)
    wav_files.sort(key=natural_sort_key)
    
    print(f"Found {len(wav_files)} audio files")
    print(f"Target duration per merged file: {target_duration_minutes} minutes")
    
    # Convert target duration to milliseconds
    target_duration_ms = target_duration_minutes * 60 * 1000
    
    current_merged_audio = AudioSegment.empty()
    current_duration = 0
    file_counter = 1
    files_in_current_merge = []
    
    for i, wav_file in enumerate(wav_files):
        print(f"Processing {os.path.basename(wav_file)} ({i+1}/{len(wav_files)})...")
        
        try:
            # Load the audio file
            audio = AudioSegment.from_wav(wav_file)
            files_in_current_merge.append(os.path.basename(wav_file))
            
            # Add to current merged audio
            current_merged_audio += audio
            current_duration += len(audio)
            
            # Check if we've reached or exceeded the target duration
            if current_duration >= target_duration_ms:
                # Save the current merged file
                output_filename = f"merged_part_{file_counter:03d}.wav"
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"Saving merged file {file_counter}: {output_filename}")
                print(f"  Duration: {get_audio_duration(current_merged_audio):.2f} minutes")
                print(f"  Contains files: {', '.join(files_in_current_merge)}")
                
                current_merged_audio.export(output_path, format="wav")
                
                # Reset for next merge
                current_merged_audio = AudioSegment.empty()
                current_duration = 0
                file_counter += 1
                files_in_current_merge = []
                
        except Exception as e:
            print(f"Error processing {wav_file}: {e}")
            continue
    
    # Save any remaining audio
    if current_duration > 0:
        output_filename = f"merged_part_{file_counter:03d}.wav"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Saving final merged file {file_counter}: {output_filename}")
        print(f"  Duration: {get_audio_duration(current_merged_audio):.2f} minutes")
        print(f"  Contains files: {', '.join(files_in_current_merge)}")
        
        current_merged_audio.export(output_path, format="wav")
    
    print(f"\nMerge completed! {file_counter} merged files created in '{output_dir}' directory")

def main():
    """Main function to run the audio merging process"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge audio chunks into 30-minute files")
    parser.add_argument("--input-dir", default="audio_output",
                       help="Directory containing audio chunks (default: audio_output)")
    parser.add_argument("--output-dir", default="merged_audio_output",
                       help="Directory to save merged audio files (default: merged_audio_output)")
    parser.add_argument("--duration", type=int, default=30,
                       help="Target duration in minutes for each merged file (default: 30)")
    
    args = parser.parse_args()
    
    print("Audio Chunk Merger")
    print("=" * 50)
    
    merge_audio_chunks(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        target_duration_minutes=args.duration
    )

if __name__ == "__main__":
    main() 