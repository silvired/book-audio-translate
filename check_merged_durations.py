#!/usr/bin/env python3
"""
Script to check the durations of merged audio files.
"""

import os
import glob
from pydub import AudioSegment

def check_merged_durations(directory="merged_audio_output"):
    """Check and display the duration of each merged audio file"""
    
    # Find all merged audio files
    wav_files = glob.glob(os.path.join(directory, "merged_part_*.wav"))
    
    if not wav_files:
        print(f"No merged audio files found in {directory}")
        return
    
    # Sort files naturally
    wav_files.sort()
    
    print("Merged Audio Files Duration Report")
    print("=" * 50)
    
    total_duration = 0
    
    for wav_file in wav_files:
        try:
            # Load the audio file
            audio = AudioSegment.from_wav(wav_file)
            duration_minutes = len(audio) / (1000 * 60)
            total_duration += duration_minutes
            
            filename = os.path.basename(wav_file)
            file_size_mb = os.path.getsize(wav_file) / (1024 * 1024)
            
            print(f"{filename}: {duration_minutes:.2f} minutes ({file_size_mb:.1f} MB)")
            
        except Exception as e:
            print(f"Error processing {wav_file}: {e}")
    
    print("-" * 50)
    print(f"Total duration: {total_duration:.2f} minutes ({total_duration/60:.2f} hours)")
    print(f"Number of files: {len(wav_files)}")
    print(f"Average duration per file: {total_duration/len(wav_files):.2f} minutes")

if __name__ == "__main__":
    check_merged_durations() 