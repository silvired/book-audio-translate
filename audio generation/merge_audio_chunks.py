#!/usr/bin/env python3
"""
Script to merge audio chunks into 30-minute files.
This script takes all the .wav or .mp3 files from the audio_output directory
and merges them into larger files, each approximately 30 minutes long.
"""

import os
import glob
import re
import sys
import contextlib
import logging
import traceback
import subprocess
import warnings

# Add ffmpeg to PATH before importing pydub
ffmpeg_path = r"C:\Users\silvi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

from pydub import AudioSegment
from moviepy import AudioFileClip
from moviepy import concatenate_audioclips
from io import StringIO

# Suppress all logging and warnings
logging.getLogger("moviepy").setLevel(logging.CRITICAL)
logging.getLogger("PIL").setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

# Disable traceback printing
sys.tracebacklimit = 0


class MergeAudioChunks:
    """
    Class to merge audio chunks into larger files of specified duration.
    """
    
    def __init__(self, target_duration_minutes=30, input_dir="audio generation/audio_output", output_dir="audio generation/merged_audio_output"):
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
        self.book_title = os.listdir('input_book')[0].split('.')[0]
        
        # Suppress FFmpeg output at OS level
        os.environ['FFREPORT'] = 'file='
        if hasattr(os, 'devnull'):
            os.environ['FFREPORT'] = f'file={os.devnull}'
    
    @contextlib.contextmanager
    def suppress_output(self):
        """Suppress stdout and stderr completely"""
        with open(os.devnull, 'w', encoding='utf-8') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_environ = os.environ.copy()
            try:
                sys.stdout = devnull
                sys.stderr = devnull
                # Suppress FFmpeg output
                os.environ['FFREPORT'] = ''
                yield
            except Exception:
                pass  # Silently ignore all exceptions during suppression
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                os.environ.clear()
                os.environ.update(old_environ)
    
    def is_valid_audio_file(self, file_path):
        """Check if an audio file is valid and can be read"""
        try:
            with self.suppress_output():
                clip = AudioFileClip(file_path)
                if clip.duration <= 0:
                    clip.close()
                    return False
                clip.close()
                return True
        except:
            return False
    
    def natural_sort_key(self, text):
        """Sort strings containing numbers naturally"""
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
    
    def get_audio_duration(self, audio_obj, is_moviepy=False):
        """Get duration of audio object in minutes"""
        if is_moviepy:
            return audio_obj.duration / 60  # Convert seconds to minutes for moviepy
        else:
            return len(audio_obj) / (1000 * 60)  # Convert milliseconds to minutes for pydub
    
    def merge_chunks(self):
        """
        Merge audio chunks into larger files of specified duration.
        Uses pydub for .wav files and moviepy for .mp3 files.
        
        Returns:
            int: Number of merged files created
        """
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Find all .wav or .mp3 files in the input directory
        wav_files = glob.glob(os.path.join(self.input_dir, "*.wav"))
        mp3_files = glob.glob(os.path.join(self.input_dir, "*.mp3"))
        
        if wav_files:
            # Use pydub for WAV files (existing functionality)
            return self._merge_wav_files(wav_files)
        elif mp3_files:
            # Use moviepy for MP3 files
            return self._merge_mp3_files(mp3_files)
        else:
            print(f"No .wav or .mp3 files found in {self.input_dir}")
            return 0
        
    def _merge_wav_files(self, audio_files):
        """Merge WAV files using pydub (existing functionality)"""
        # Sort files naturally (chunk_1.wav, chunk_2.wav, ..., chunk_10.wav, etc.)
        audio_files.sort(key=self.natural_sort_key)
        
        print(f"Found {len(audio_files)} WAV files")
        print(f"Target duration per merged file: {self.target_duration_minutes} minutes")
        print("Using pydub for WAV file processing...")
        
        # Convert target duration to milliseconds
        target_duration_ms = self.target_duration_minutes * 60 * 1000
        
        current_merged_audio = AudioSegment.empty()
        current_duration = 0
        file_counter = 1
        files_in_current_merge = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"Processing {os.path.basename(audio_file)} ({i+1}/{len(audio_files)})...")
            
            try:
                # Load the audio file using pydub
                audio = AudioSegment.from_file(audio_file, format='wav')
                files_in_current_merge.append(os.path.basename(audio_file))
                
                # Add to current merged audio
                current_merged_audio += audio
                current_duration += len(audio)
                
                # Check if we've reached or exceeded the target duration
                if current_duration >= target_duration_ms:
                    # Save the current merged file
                    output_filename = f"{file_counter:03d}_{self.book_title}.wav"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    print(f"Saving merged file {file_counter}: {output_filename}")
                    print(f"  Duration: {self.get_audio_duration(current_merged_audio):.2f} minutes")
                    print(f"  Contains files: {', '.join(files_in_current_merge)}")
                    
                    current_merged_audio.export(output_path, format='wav')
                    
                    # Reset for next merge
                    current_merged_audio = AudioSegment.empty()
                    current_duration = 0
                    file_counter += 1
                    files_in_current_merge = []
                    
            except Exception as e:
                print(f"Error processing {audio_file}: {e}")
                continue
        
        # Save any remaining audio
        if current_duration > 0:
            output_filename = f"{file_counter:03d}_{self.book_title}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"Saving final merged file {file_counter}: {output_filename}")
            print(f"  Duration: {self.get_audio_duration(current_merged_audio):.2f} minutes")
            print(f"  Contains files: {', '.join(files_in_current_merge)}")
            
            current_merged_audio.export(output_path, format='wav')
        
        print(f"\nMerge completed! {file_counter} merged files created in '{self.output_dir}' directory")
        return file_counter
    
    def _merge_mp3_files(self, audio_files):
        """Merge MP3 files using moviepy"""
        # Sort files naturally (chunk_1.mp3, chunk_2.mp3, ..., chunk_10.mp3, etc.)
        audio_files.sort(key=self.natural_sort_key)
        
        print(f"Found {len(audio_files)} MP3 files")
        print(f"Target duration per merged file: {self.target_duration_minutes} minutes")
        print("Using moviepy for MP3 file processing...")
        
        # Convert target duration to seconds
        target_duration_sec = self.target_duration_minutes * 60
        
        current_audio_clips = []
        current_duration = 0
        file_counter = 1
        files_in_current_merge = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"Processing {os.path.basename(audio_file)} ({i+1}/{len(audio_files)})...", end='', flush=True)
            
            # Check if file is valid before attempting to load
            if not self.is_valid_audio_file(audio_file):
                print(f" (skipped - invalid file)")
                continue
            
            audio_clip = None
            try:
                # Load the audio file using moviepy with suppressed output
                with self.suppress_output():
                    audio_clip = AudioFileClip(audio_file)
                    files_in_current_merge.append(os.path.basename(audio_file))
                    
                    # Add to current list
                    current_audio_clips.append(audio_clip)
                    current_duration += audio_clip.duration
                print(f" ✓")
                
                # Check if we've reached or exceeded the target duration
                if current_duration >= target_duration_sec:
                    # Concatenate and save the current merged file
                    output_filename = f"{file_counter:03d}_{self.book_title}.mp3"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    print(f"Saving merged file {file_counter}: {output_filename}")
                    merged_clip = None
                    merge_success = False
                    try:
                        with self.suppress_output():
                            merged_clip = concatenate_audioclips(current_audio_clips)
                            merged_clip.write_audiofile(output_path, codec='mp3', verbose=False, logger=None)
                        print(f"  Duration: {self.get_audio_duration(merged_clip, is_moviepy=True):.2f} minutes")
                        print(f"  Contains files: {', '.join(files_in_current_merge)}")
                        if merged_clip:
                            with self.suppress_output():
                                merged_clip.close()
                        merge_success = True
                    except:
                        print(f"Couldn't merge part {file_counter:03d}")
                        if merged_clip:
                            try:
                                with self.suppress_output():
                                    merged_clip.close()
                            except:
                                pass
                    
                    # Close all clips and reset for next merge
                    for clip in current_audio_clips:
                        try:
                            with self.suppress_output():
                                clip.close()
                        except:
                            pass
                    
                    # Only reset counters if merge succeeded
                    if merge_success:
                        current_audio_clips = []
                        current_duration = 0
                        file_counter += 1
                        files_in_current_merge = []
                    else:
                        # If merge failed, clear the clips and continue
                        current_audio_clips = []
                        current_duration = 0
                        file_counter += 1
                        files_in_current_merge = []
                
            except:
                print(f" (skipped - error)")
                # Try to close the clip if it was opened
                if audio_clip:
                    try:
                        with self.suppress_output():
                            audio_clip.close()
                    except:
                        pass
                continue
        
        # Save any remaining audio
        if current_duration > 0 and current_audio_clips:
            output_filename = f"{file_counter:03d}_{self.book_title}.mp3"
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"Saving final merged file {file_counter}: {output_filename}")
            merged_clip = None
            try:
                with self.suppress_output():
                    merged_clip = concatenate_audioclips(current_audio_clips)
                    merged_clip.write_audiofile(output_path, codec='mp3', verbose=False, logger=None)
                print(f"  Duration: {self.get_audio_duration(merged_clip, is_moviepy=True):.2f} minutes")
                print(f"  Contains files: {', '.join(files_in_current_merge)}")
                if merged_clip:
                    with self.suppress_output():
                        merged_clip.close()
            except:
                print(f"Couldn't merge part {file_counter:03d}")
                if merged_clip:
                    try:
                        with self.suppress_output():
                            merged_clip.close()
                    except:
                        pass
            
            # Close all clips
            for clip in current_audio_clips:
                try:
                    with self.suppress_output():
                        clip.close()
                except:
                    pass
        
        print(f"\nMerge completed! {file_counter} merged files created in '{self.output_dir}' directory")
        return file_counter


if __name__ == "__main__":
    # Example usage for testing/debugging
    # This allows you to run this script directly without running the full pipeline
    
    # Suppress all errors during main execution
    try:
        # Example 1: Use default settings (30 minutes, audio_output -> merged_audio_output)
        merger = MergeAudioChunks()
        merger.merge_chunks()
    except:
        pass  # Silently ignore all errors
    
    # Example 2: Custom settings
    # merger = MergeAudioChunks(
    #     target_duration_minutes=15,  # 15-minute chunks instead of 30
    #     input_dir="audio_output",     # Input directory with audio chunks
    #     output_dir="merged_audio_output"  # Output directory for merged files
    # )
    # merger.merge_chunks()
