#!/usr/bin/env python3
"""
PDF Translation Pipeline
Runs the complete translation pipeline in sequence:
1. book_to_text.py - Convert PDF to text
2. sentence_segmenter.py - Segment text into sentences
3. translator.py - Translate segmented text
4. text_to_pdf.py - Convert translated text back to PDF

Each step has a 5-second pause between execution.
"""

import time
import os
from book_to_text import PDFToText
from sentence_segmenter import SentenceSegmenter
from translator import SentenceBySentence, ParagraphByParagraph
from text_to_pdf import TextToPDFConverter

# Translation strategy constant - change this to switch between strategies
# Options: "sentence_by_sentence" or "paragraph_by_paragraph"
TRANSLATION_STRATEGY = "sentence_by_sentence"


def run_pdf_translation_pipeline(translation_strategy="sentence_by_sentence"):
    """
    Run the complete PDF translation pipeline in sequence.
    
    Args:
        translation_strategy (str): Translation strategy to use. 
                                   Options: "sentence_by_sentence" or "paragraph_by_paragraph"
    """
    print("=" * 60)
    print("PDF TRANSLATION PIPELINE")
    print("=" * 60)
    print()
    
    # Step 1: Convert PDF to text
    print("STEP 1: Converting PDF to text...")
    print("-" * 40)
    try:
        # Create PDF to text converter
        converter = PDFToText()
        
        # Find and convert the first PDF file
        print("Looking for PDF files in input directory...")
        output_path = converter.convert_first_pdf()
        
        print(f"✓ Successfully converted PDF to text!")
        print(f"  Output saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("  Please make sure you have a PDF file in the 'input_book' directory.")
        return False
    except Exception as e:
        print(f"✗ An error occurred: {e}")
        return False
    
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    print()
    
    # Step 2: Segment text into sentences
    print("STEP 2: Segmenting text into sentences...")
    print("-" * 40)
    try:
        # Create sentence segmenter
        segmenter = SentenceSegmenter()
        
        # Find and segment the first .txt file
        result = segmenter.segment_first_txt_file()
        
        if result is None:
            return False
        
        print(f"✓ Segmentation completed successfully!")
        
    except Exception as e:
        print(f"✗ An error occurred during segmentation: {e}")
        return False
    
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    print()
    
    # Step 3: Translate segmented text
    print("STEP 3: Translating segmented text...")
    print("-" * 40)
    try:
        # Create translator instance based on strategy
        overall_start_time = time.time()
        
        if translation_strategy == "paragraph_by_paragraph":
            translator = ParagraphByParagraph()
            print("Using paragraph-by-paragraph translation strategy")
        else:
            translator = SentenceBySentence()
            print("Using sentence-by-sentence translation strategy")
        
        # Translate the first JSON file
        translator.translate_first_json_file()
        
        overall_end_time = time.time()
        overall_time = overall_end_time - overall_start_time
        
        print(f"✓ Translation completed successfully!")
        print(f"  Total translation time: {overall_time:.2f} seconds")
        
    except Exception as e:
        print(f"✗ An error occurred during translation: {e}")
        return False
    
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    print()
    
    # Step 4: Convert translated text back to PDF
    print("STEP 4: Converting translated text to PDF...")
    print("-" * 40)
    try:
        # Create text to PDF converter
        converter = TextToPDFConverter()
        
        # Convert translated text to PDF
        pdf_path = converter.create_pdf()
        
        print(f"✓ PDF creation completed successfully!")
        print(f"  PDF saved to: {pdf_path}")
        
    except Exception as e:
        print(f"✗ An error occurred during PDF creation: {e}")
        return False
    
    print()
    print("=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("All four steps have been executed in sequence:")
    print("1. ✓ PDF to text conversion")
    print("2. ✓ Text segmentation")
    print("3. ✓ Text translation")
    print("4. ✓ Translated text to PDF conversion")
    print()
    
    return True


if __name__ == "__main__":
    """
    Main execution block.
    """
    try:
        # Run with the translation strategy defined by the constant
        success = run_pdf_translation_pipeline(TRANSLATION_STRATEGY)
        if not success:
            print("\nPipeline failed. Please check the error messages above.")
            exit(1)
        
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        exit(1)
