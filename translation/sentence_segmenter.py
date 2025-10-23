#!/usr/bin/env python3
"""
Sentence Segmentation Script using spaCy
Segments text into sentences while preserving paragraph structure.
Outputs JSON format with paragraph and sentence information.
Set FILE_NAME to "default" to auto-pick first .txt file, or specify a filename.
"""

import spacy
import json
import os
from pathlib import Path


class SentenceSegmenter:
    """
    Class for segmenting text into sentences while preserving paragraph structure.
    """
    
    # Default folder paths as class attributes (absolute paths)
    DEFAULT_INPUT_FOLDER = r"C:\Users\silvi\Desktop\book-audio-translate\text_output"
    DEFAULT_OUTPUT_FOLDER = r"C:\Users\silvi\Desktop\book-audio-translate\translation\segmented_text"
    FILE_NAME = "default"  # Set to "default" to auto-pick first .txt file, or specify a filename
    
    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize the sentence segmenter with input and output directories.
        
        Args:
            input_dir (str): Directory containing input text files. If None, uses DEFAULT_INPUT_FOLDER.
            output_dir (str): Directory for output JSON files. If None, uses DEFAULT_OUTPUT_FOLDER.
        """
        if input_dir is None:
            input_dir = self.DEFAULT_INPUT_FOLDER
        if output_dir is None:
            output_dir = self.DEFAULT_OUTPUT_FOLDER
        
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load the spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Error: spaCy English model not found. Please install it with:")
            print("python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def find_first_txt_file(self):
        """
        Find the first .txt file in the input directory.
        
        Returns:
            str: Path to the first .txt file found, or None if none found
        """
        if not os.path.exists(self.input_dir):
            print(f"Error: Directory '{self.input_dir}' not found.")
            return None
        
        txt_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.txt')]
        if not txt_files:
            print(f"Error: No .txt files found in '{self.input_dir}' directory.")
            return None
        
        return os.path.join(self.input_dir, txt_files[0])
    
    def get_output_path(self, input_file_path, output_extension='_segmented.json'):
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
    
    def segment_text_with_paragraphs(self, text_file_path, output_file_path=None):
        """
        Segment text into sentences while preserving paragraph structure.
        
        Args:
            text_file_path (str): Path to input text file
            output_file_path (str, optional): Path to output JSON file
        
        Returns:
            list: List of dictionaries with paragraph and sentence information
        """
        if self.nlp is None:
            print("Error: spaCy model not loaded.")
            return None
        
        # Read input text
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{text_file_path}' not found.")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
        
        # Split text into paragraphs by empty lines
        raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Process each paragraph with spaCy
        paragraphs = []
        
        for para_idx, paragraph_text in enumerate(raw_paragraphs):
            # Process paragraph with spaCy
            doc = self.nlp(paragraph_text)
            
            # Extract sentences from this paragraph
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            
            # Add paragraph to result
            paragraphs.append({
                'par_id': para_idx,
                'sentences': sentences
            })
        
        # Save to JSON if output path provided
        if output_file_path:
            try:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    json.dump(paragraphs, f, indent=2, ensure_ascii=False)
                print(f"Segmented text saved to: {output_file_path}")
            except Exception as e:
                print(f"Error saving to file: {e}")
        
        return paragraphs
    
    def segment_first_txt_file(self):
        """
        Find and segment the first .txt file in the input directory, or a specific file if FILE_NAME is set.
        
        Returns:
            list: List of dictionaries with paragraph and sentence information, or None if failed
        """
        # Determine which file to process
        if self.FILE_NAME == "default":
            # Auto-detect first .txt file
            input_file = self.find_first_txt_file()
        else:
            # Use specified filename
            input_file = os.path.join(self.input_dir, self.FILE_NAME)
            if not os.path.exists(input_file):
                print(f"Error: Specified file '{input_file}' not found.")
                return None
        
        if input_file is None:
            return None
        
        # Generate output file path
        output_file = self.get_output_path(input_file)
        
        print(f"Processing: {input_file}")
        print(f"Output will be saved to: {output_file}")
        
        # Segment the text
        result = self.segment_text_with_paragraphs(input_file, output_file)
        
        if result is not None:
            # Print summary
            total_paragraphs = len(result)
            total_sentences = sum(len(para['sentences']) for para in result)
            
            print(f"Segmentation Summary:")
            print(f"Total paragraphs: {total_paragraphs}")
            print(f"Total sentences: {total_sentences}")
        
        return result


# Legacy function wrappers for backward compatibility
def segment_text_with_paragraphs(text_file_path, output_file_path=None):
    """
    Legacy function wrapper for backward compatibility.
    """
    segmenter = SentenceSegmenter()
    return segmenter.segment_text_with_paragraphs(text_file_path, output_file_path)


def find_first_txt_file(directory):
    """
    Legacy function wrapper for backward compatibility.
    """
    segmenter = SentenceSegmenter(input_dir=directory)
    return segmenter.find_first_txt_file()


def main():
    """Main function - processes file based on FILE_NAME constant (default: auto-detect first .txt)."""
    segmenter = SentenceSegmenter()
    segmenter.segment_first_txt_file()


if __name__ == "__main__":
    main()
