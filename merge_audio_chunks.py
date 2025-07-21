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


class MergeAudioChunks:
    """
    Class to merge audio chunks into larger files of specified duration.
    """
    
    def __init__(self, target_duration_minutes=30, input_dir="audio_output", output_dir="merged_audio_output"):
        """
        Initialize the audio chunk merger.
        
        Args:
            target_duration_minutes (int): Target duration for each merged file in minutes
            input_dir (str): Directory containing the audio chunks
            output_dir (str): Directory to save merged audio files
        """
        self.target_duration_minutes = target_duration_minutes
        self.input_dir = input_dir
        self.output_dir = output_dir
    
    def natural_sort_key(self, text):
        """Sort strings containing numbers naturally"""
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
    
    def get_audio_duration(self, audio_segment):
        """Get duration of audio segment in minutes"""
        return len(audio_segment) / (1000 * 60)  # Convert milliseconds to minutes
    
    def merge_chunks(self):
        """
        Merge audio chunks into larger files of specified duration.
        
        Returns:
            int: Number of merged files created
        """
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Find all .wav files in the input directory
        wav_files = glob.glob(os.path.join(self.input_dir, "*.wav"))
        
        if not wav_files:
            print(f"No .wav files found in {self.input_dir}")
            return 0
        
        # Sort files naturally (chunk_1.wav, chunk_2.wav, ..., chunk_10.wav, etc.)
        wav_files.sort(key=self.natural_sort_key)
        
        print(f"Found {len(wav_files)} audio files")
        print(f"Target duration per merged file: {self.target_duration_minutes} minutes")
        
        # Convert target duration to milliseconds
        target_duration_ms = self.target_duration_minutes * 60 * 1000
        
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
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    print(f"Saving merged file {file_counter}: {output_filename}")
                    print(f"  Duration: {self.get_audio_duration(current_merged_audio):.2f} minutes")
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
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"Saving final merged file {file_counter}: {output_filename}")
            print(f"  Duration: {self.get_audio_duration(current_merged_audio):.2f} minutes")
            print(f"  Contains files: {', '.join(files_in_current_merge)}")
            
            current_merged_audio.export(output_path, format="wav")
        
        print(f"\nMerge completed! {file_counter} merged files created in '{self.output_dir}' directory")
        return file_counter
