import os
import sys
import torch
from abc import ABC, abstractmethod
from TTS.api import TTS


class TextToSpeechConverter(ABC):
    """
    Abstract base class for converting text to speech.
    """
    
    # Default folder paths as class attributes
    DEFAULT_INPUT_FOLDER = "text_output"
    DEFAULT_OUTPUT_FOLDER = "audio_output"
    
    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize the converter with input and output directories.
        
        Args:
            input_dir (str): Directory containing input text files. If None, uses DEFAULT_INPUT_FOLDER.
            output_dir (str): Directory for output audio files. If None, uses DEFAULT_OUTPUT_FOLDER.
        """
        # Get the directory where this script is located (now in main directory)
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        if input_dir is None:
            input_dir = os.path.join(project_root, self.DEFAULT_INPUT_FOLDER)
        if output_dir is None:
            output_dir = os.path.join(project_root, self.DEFAULT_OUTPUT_FOLDER)
        
        self.input_dir = input_dir
        self.output_dir = output_dir
    
    @abstractmethod
    def convert_to_speech(self, input_path):
        """
        Convert a text file to speech.
        
        Args:
            input_path (str): Path to the text file to convert.
            
        Returns:
            str: Path to the output audio file.
        """
        pass
    
    def find_input_file(self, extension='.txt'):
        """
        Find the first file with the given extension in the input directory.
        
        Args:
            extension (str): File extension to search for (e.g., '.txt').
            
        Returns:
            str: Path to the found file.
            
        Raises:
            FileNotFoundError: If no files with the extension are found.
        """
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Input directory '{self.input_dir}' not found.")
        
        files = [f for f in os.listdir(self.input_dir) if f.lower().endswith(extension)]
        if not files:
            raise FileNotFoundError(f"No {extension} files found in '{self.input_dir}' directory.")
        
        return os.path.join(self.input_dir, files[0])
    
    def get_output_path(self, input_file_path, output_extension='.wav'):
        """
        Generate output file path based on input file path.
        
        Args:
            input_file_path (str): Path to the input file.
            output_extension (str): Extension for the output file.
            
        Returns:
            str: Path to the output file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        return os.path.join(self.output_dir, base_name + output_extension)
    
    def clean_text(self, text):
        """Clean text for TTS processing"""
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        # Replace multiple spaces with single space
        import re
        text = re.sub(r'\s+', ' ', text)
        # Remove any non-printable characters except newlines
        text = ''.join(char for char in text if char.isprintable() or char == '\n')
        return text.strip()
    
    def split_text_into_chunks(self, text, chunk_size=5000):
        """Split text into chunks of approximately chunk_size characters"""
        # Clean the text first
        text = self.clean_text(text)
        
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


class CoquiTTS(TextToSpeechConverter):
    """
    Concrete class for converting text to speech using Coqui TTS.
    """
    
    def __init__(self, input_dir=None, output_dir=None, language="en", skip_lines=111):
        """
        Initialize Coqui TTS converter.
        
        Args:
            input_dir (str): Directory containing text files. If None, uses 'text_output'.
            output_dir (str): Directory for output audio files. If None, uses 'audio_output'.
            language (str): Language code for TTS model.
            skip_lines (int): Number of lines to skip at the start of the text.
        """
        super().__init__(input_dir, output_dir)
        self.language = language
        self.skip_lines = skip_lines
        
        # Language model dictionary
        self.language_model_dict = {
            "en": "tts_models/en/ljspeech/fast_pitch",
            "it": "tts_models/it/mai_female/glow-tts",  # best one in italian but it's a bit robotic
            "es": "tts_models/es/mai_female/vits",  # Spanish female voice (if available)
        }
        
        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize TTS
        print("Loading TTS model...")
        model_name = self.language_model_dict[self.language]
        self.tts = TTS(model_name).to(self.device)
        print("TTS model loaded successfully!")
    
    def convert_to_speech(self, input_path):
        """
        Convert a text file to speech using Coqui TTS.
        
        Args:
            input_path (str): Path to the text file to convert.
            
        Returns:
            str: Path to the output audio file.
        """
        # Read the text file
        print(f"Reading {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Original text length: {len(text)} characters")
        
        # Skip the first X lines
        lines = text.split('\n')
        if len(lines) > self.skip_lines:
            text = '\n'.join(lines[self.skip_lines:])
            print(f"Skipped first {self.skip_lines} lines. Remaining text length: {len(text)} characters")
        
        # Split text into chunks
        chunks = self.split_text_into_chunks(text, chunk_size=5000)
        print(f"Split text into {len(chunks)} chunks")
        
        # Process each chunk
        chunk_files = []
        for i, chunk in enumerate(chunks):
            # Skip very short chunks that might cause issues
            if len(chunk.strip()) < 20:
                print(f"Skipping chunk {i+1}/{len(chunks)}: too short ({len(chunk.strip())} chars)")
                continue
                
            output_path = os.path.join(self.output_dir, f'chunk_{i+1}.wav')
            print(f"Synthesizing chunk {i+1}/{len(chunks)} to {output_path} ...", flush=True)
            
            try:
                self.tts.tts_to_file(text=chunk, file_path=output_path)
                print(f"Chunk {i+1}/{len(chunks)} saved to file: {output_path}", flush=True)
                chunk_files.append(output_path)
            except Exception as e:
                print(f"Error processing chunk {i+1}/{len(chunks)}: {e}")
                print(f"Chunk content (first 100 chars): {chunk[:100]}...")
                continue
        
        print("Text-to-audio conversion completed!")
        
        # Return the path to the first chunk file (or None if no chunks were created)
        return chunk_files[0] if chunk_files else None
    
    def convert_first_text_file(self):
        """
        Find and convert the first text file in the input directory.
        
        Returns:
            str: Path to the first output audio chunk file.
        """
        text_path = self.find_input_file('.txt')
        return self.convert_to_speech(text_path) 