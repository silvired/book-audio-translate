#!/usr/bin/env python3
"""
Complete Translation Pipeline Script

This script executes the full book translation pipeline in sequence:
1. BookToText: Convert book file (PDF/EPUB) to text
2. SentenceSegmenter: Segment text into sentences with paragraph structure
3. BookTranslator: Translate the segmented text
4. TextToPDFConverter: Convert translated text to PDF

Usage:
    python translation/run_translation_pipeline.py
    # or from root: python -m translation.run_translation_pipeline
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Optional

from sentence_segmenter import SentenceSegmenter
from translator import Translator
from translate_book import BookTranslator
from text_to_pdf import TextToPDFConverter
from chunk_mapper import ChunkMapper
from token_counter import TokenCounter

# Import BookToText from parent directory
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
from book_to_text import BookToText


class TranslationPipeline:
    """
    Orchestrates the complete book translation pipeline.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        target_language: str = "Italian",
        source_language: str = "English",
        input_dir: Optional[str] = None,
        text_output_dir: Optional[str] = None,
        segmented_text_dir: Optional[str] = None,
        translated_text_dir: Optional[str] = None,
        pdf_output_dir: Optional[str] = None,
    ):
        """
        Initialize the translation pipeline.
        
        Args:
            model_name: Name of the AI model to use for translation
            target_language: Target language for translation
            source_language: Source language for translation
            input_dir: Directory containing input book files
            text_output_dir: Directory for text extraction output
            segmented_text_dir: Directory for segmented text output
            translated_text_dir: Directory for translated text output
            pdf_output_dir: Directory for PDF output
        """
        self.model_name = model_name
        self.target_language = target_language
        self.source_language = source_language
        
        # Setup directories (relative to project root)
        project_root = Path(__file__).parent.parent
        self.input_dir = input_dir or str(project_root / "input_book")
        self.text_output_dir = text_output_dir or str(project_root / "text_output")
        self.segmented_text_dir = segmented_text_dir or str(project_root / "translation" / "segmented_text")
        self.translated_text_dir = translated_text_dir or str(project_root / "translation" / "translated_text")
        self.pdf_output_dir = pdf_output_dir or str(project_root / "translation" / "pdf_output")
        
        # Create output directories
        for directory in [self.text_output_dir, self.segmented_text_dir, self.translated_text_dir, self.pdf_output_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Load model configuration
        self.model_config = self._load_model_config()
        
        print("=" * 80)
        print("TRANSLATION PIPELINE INITIALIZED")
        print("=" * 80)
        print(f"Model: {self.model_name}")
        print(f"Target Language: {self.target_language}")
        print(f"Source Language: {self.source_language}")
        print()
    
    def _load_model_config(self) -> dict:
        """Load model configuration from models_info.yaml."""
        model_info_path = Path(__file__).parent / "models_info.yaml"
        with open(model_info_path, 'r', encoding='utf-8') as f:
            model_info = yaml.safe_load(f)
        
        for key in model_info.keys():
            if self.model_name in key:
                return model_info[key]
        
        raise ValueError(f"Model configuration not found for {self.model_name}")
    
    def step_1_book_to_text(self) -> str:
        """
        Step 1: Convert book file (PDF/EPUB) to plain text.
        
        Returns:
            Path to the generated text file
        """
        print("\n" + "=" * 80)
        print("STEP 1: BOOK TO TEXT CONVERSION")
        print("=" * 80)
        
        # Find the first PDF or EPUB file in the input directory
        file_path, ext = BookToText.get_file_by_extensions(self.input_dir, ".pdf", ".epub")
        
        # Get the appropriate converter for the file
        converter = BookToText.get_converter_for_file(file_path, self.input_dir, self.text_output_dir)
        
        # Convert the found file to text
        text_file = converter.convert_to_text(file_path)
        
        # Ask user for the first sentence to trim text properly
        print("\nEnter the first sentence of the book to trim extracted text:")
        first_sentence = input("> ").strip()
        
        if first_sentence:
            # Read the extracted text
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Trim text to start from the first sentence
            trimmed_text = BookToText.trim_text_to_first_sentence(text, first_sentence)
            
            # Write back the trimmed text
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(trimmed_text)
            
            print("✓ Text trimmed to first sentence")
        
        print(f"✓ Text extraction completed")
        print(f"  Output: {text_file}")
        return text_file
    
    def step_2_sentence_segmentation(self, text_file: str) -> str:
        """
        Step 2: Segment text into sentences while preserving paragraph structure.
        
        Args:
            text_file: Path to the text file from step 1
            
        Returns:
            Path to the generated segmented JSON file
        """
        print("\n" + "=" * 80)
        print("STEP 2: SENTENCE SEGMENTATION")
        print("=" * 80)
        
        segmenter = SentenceSegmenter(self.text_output_dir, self.segmented_text_dir)
        
        # Get the base name for the text file
        text_file_name = os.path.basename(text_file)
        
        # Generate output path
        segmented_file = segmenter.get_output_path(text_file)
        
        # Segment the text
        result = segmenter.segment_text_with_paragraphs(text_file, segmented_file)
        
        if result:
            print(f"✓ Text segmentation completed")
            print(f"  Output: {segmented_file}")
            print(f"  Total paragraphs: {len(result)}")
            return segmented_file
        else:
            raise RuntimeError("Text segmentation failed")
    
    def step_3_book_translation(self, segmented_file: str) -> str:
        """
        Step 3: Translate the segmented text.
        
        Args:
            segmented_file: Path to the segmented JSON file from step 2
            
        Returns:
            Path to the generated translated text file
        """
        print("\n" + "=" * 80)
        print("STEP 3: BOOK TRANSLATION")
        print("=" * 80)
        
        # Initialize token counter
        token_counter = TokenCounter(
            model_name=self.model_name,
            provider="tiktoken",  # Fast local counting
            api_key=None,
            base_url=None
        )
        
        # Initialize translator
        translator = Translator(model_name=self.model_name)
        
        # Initialize chunk mapper
        chunk_mapper = ChunkMapper(
            max_output_token=self.model_config['max_output_tokens'],
            output_input_token_ratio=self.model_config['output_input_token_ratio']
        )
        
        # Get just the filename without directory path
        segmented_file_name = os.path.basename(segmented_file)
        
        # Initialize book translator
        book_translator = BookTranslator(
            chunk_mapper=chunk_mapper,
            translator=translator,
            token_counter=token_counter,
            segmented_file=segmented_file_name,
            target_language=self.target_language,
            source_language=self.source_language
        )
        
        # Run translation
        book_translator.run()
        
        print(f"✓ Book translation completed")
        
        # Find the generated translated file
        translated_files = list(Path(self.translated_text_dir).glob("*_translated.txt"))
        if translated_files:
            translated_file = str(translated_files[-1])  # Get the most recent
            print(f"  Output: {translated_file}")
            return translated_file
        else:
            raise RuntimeError("Translation output file not found")
    
    def step_4_text_to_pdf(self, translated_file: str) -> str:
        """
        Step 4: Convert translated text to PDF.
        
        Args:
            translated_file: Path to the translated text file from step 3
            
        Returns:
            Path to the generated PDF file
        """
        print("\n" + "=" * 80)
        print("STEP 4: TEXT TO PDF CONVERSION")
        print("=" * 80)
        
        converter = TextToPDFConverter(self.translated_text_dir, self.pdf_output_dir)
        
        # Get just the filename
        translated_file_name = os.path.basename(translated_file)
        
        # Convert to PDF using create_pdf method
        pdf_file = converter.create_pdf(translated_file_name)
        
        print(f"✓ PDF conversion completed")
        print(f"  Output: {pdf_file}")
        return pdf_file
    
    def run(self) -> dict:
        """
        Execute the complete translation pipeline.
        
        Returns:
            Dictionary with output paths from each step
        """
        try:
            # Step 1: Book to Text
            text_file = self.step_1_book_to_text()
            
            # Step 2: Sentence Segmentation
            segmented_file = self.step_2_sentence_segmentation(text_file)
            
            # Step 3: Book Translation
            translated_file = self.step_3_book_translation(segmented_file)
            
            # Step 4: Text to PDF
            pdf_file = self.step_4_text_to_pdf(translated_file)
            
            # Success summary
            print("\n" + "=" * 80)
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Text Output:        {text_file}")
            print(f"Segmented Output:   {segmented_file}")
            print(f"Translated Output:  {translated_file}")
            print(f"PDF Output:         {pdf_file}")
            print("=" * 80)
            
            return {
                "text_file": text_file,
                "segmented_file": segmented_file,
                "translated_file": translated_file,
                "pdf_file": pdf_file
            }
        
        except Exception as e:
            print(f"\n❌ Pipeline failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point for the translation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Book Translation Pipeline")
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="AI model to use for translation (default: gemini-2.5-flash)"
    )
    parser.add_argument(
        "--target-language",
        type=str,
        default="Italian",
        help="Target language for translation (default: Italian)"
    )
    parser.add_argument(
        "--source-language",
        type=str,
        default="English",
        help="Source language (default: English)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Input directory for book files"
    )
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = TranslationPipeline(
        model_name=args.model,
        target_language=args.target_language,
        source_language=args.source_language,
        input_dir=args.input_dir
    )
    
    pipeline.run()


if __name__ == "__main__":
    main()
