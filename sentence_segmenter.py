#!/usr/bin/env python3
"""
Sentence Segmentation Script using spaCy
Segments text into sentences while preserving paragraph structure.
Outputs JSON format with paragraph and sentence information.
Automatically processes the first .txt file found in text_output folder.
"""

import spacy
import json
import os
from pathlib import Path


def segment_text_with_paragraphs(text_file_path, output_file_path=None):
    """
    Segment text into sentences while preserving paragraph structure.
    
    Args:
        text_file_path (str): Path to input text file
        output_file_path (str, optional): Path to output JSON file
    
    Returns:
        list: List of dictionaries with paragraph and sentence information
    """
    # Load spaCy model
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Error: spaCy English model not found. Please install it with:")
        print("python -m spacy download en_core_web_sm")
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
        doc = nlp(paragraph_text)
        
        # Extract sentences from this paragraph
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        # Count tokens for each sentence
        token_counts = []
        for sent in doc.sents:
            if sent.text.strip():  # Only count non-empty sentences
                # Count tokens (words) - exclude spaces and punctuation except basic punctuation
                token_count = len([token for token in sent])
                token_counts.append(token_count)
        
        # Add paragraph to result
        paragraphs.append({
            'par_id': para_idx,
            'sentences': sentences,
            'token_counts': token_counts
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


def find_first_txt_file(directory):
    """
    Find the first .txt file in the specified directory.
    
    Args:
        directory (str): Directory to search for .txt files
        
    Returns:
        str: Path to the first .txt file found, or None if none found
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return None
    
    txt_files = [f for f in os.listdir(directory) if f.lower().endswith('.txt')]
    if not txt_files:
        print(f"Error: No .txt files found in '{directory}' directory.")
        return None
    
    return os.path.join(directory, txt_files[0])


def main():
    """Main function - automatically processes first .txt file in text_output folder."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output directories
    input_dir = os.path.join(script_dir, "text_output")
    output_dir = os.path.join(script_dir, "segmented_text_output")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find the first .txt file in text_output
    input_file = find_first_txt_file(input_dir)
    if input_file is None:
        return
    
    # Generate output file path
    input_filename = os.path.basename(input_file)
    output_filename = os.path.splitext(input_filename)[0] + "_segmented.json"
    output_file = os.path.join(output_dir, output_filename)
    
    print(f"Processing: {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # Segment the text
    result = segment_text_with_paragraphs(input_file, output_file)
    
    if result is None:
        return
    
    # Print summary
    total_paragraphs = len(result)
    total_sentences = sum(len(para['sentences']) for para in result)
    total_tokens = sum(sum(para['token_counts']) for para in result)
    
    print(f"\nSegmentation Summary:")
    print(f"Total paragraphs: {total_paragraphs}")
    print(f"Total sentences: {total_sentences}")
    print(f"Total tokens: {total_tokens}")


if __name__ == "__main__":
    main()
