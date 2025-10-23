"""
Script to translate a segmented book using ChunkMapper and Translator.
Tracks token usage and calculates translation costs.
"""

import json
import yaml
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from chunk_mapper import ChunkMapper
from translator import Translator
from token_counter import TokenCounter
from cost_calculator import CostCalculator


class BookTranslator:
    """
    A class to handle book translation workflow.
    
    Translates segmented books using ChunkMapper and Translator,
    tracks token usage, and calculates translation costs.
    """
    
    def __init__(
        self,
        chunk_mapper: ChunkMapper,
        translator: Translator,
        token_counter: TokenCounter,
        segmented_file: Optional[str] = None,
        target_language: str = "Italian",
        source_language: str = "English",
        thinking_enabled: int = -1
    ):
        """
        Initialize BookTranslator.
        
        Args:
            chunk_mapper: ChunkMapper instance for mapping paragraphs into chunks
            translator: Translator instance for translating text
            token_counter: TokenCounter instance for counting tokens
            segmented_file: Path to segmented book file. If None, uses first file in segmented_text folder.
            target_language: Target language for translation
            source_language: Source language for translation
            thinking_enabled: Thinking budget (-1 for unlimited)
        """
        self.script_dir = Path(__file__).parent
        self.segmented_text_dir = self.script_dir.parent / "translation/segmented_text"
        self.translated_text_dir = self.script_dir.parent / "translation/translated_text"
        
        # Create translated_text directory if it doesn't exist
        self.translated_text_dir.mkdir(parents=True, exist_ok=True)
        
        # Store dependency objects
        self.chunk_mapper = chunk_mapper
        self.translator = translator
        self.token_counter = token_counter
        
        self.target_language = target_language
        self.source_language = source_language
        self.thinking_enabled = thinking_enabled
        
        # Determine the segmented file to use
        if segmented_file:
            self.segmented_book_file = self.segmented_text_dir / segmented_file
        else:
            self.segmented_book_file = self._get_first_segmented_file()
        
        if not self.segmented_book_file.exists():
            raise FileNotFoundError(f"Segmented book file not found: {self.segmented_book_file}")
        
        # File paths
        self.prompt_file = self.script_dir / "translation_prompt.txt"
        self.model_info_file = self.script_dir / "models_info.yaml"
        
        # Initialize tracking variables
        self.prompt = None
        self.segmented_book = None
        self.model_info = None
        self.model_config = None
        
        self.tot_input_tokens = 0
        self.tot_output_tokens = 0
        self.tot_thinking_tokens = 0
    
    def _get_first_segmented_file(self) -> Path:
        """
        Get the first segmented file from the segmented_text folder.
        
        Returns:
            Path to the first .json file in segmented_text folder
            
        Raises:
            FileNotFoundError: If no files found in segmented_text folder
        """
        if not self.segmented_text_dir.exists():
            raise FileNotFoundError(f"Segmented text directory not found: {self.segmented_text_dir}")
        
        # Find all .json files
        json_files = sorted(self.segmented_text_dir.glob("*.json"))
        
        if not json_files:
            raise FileNotFoundError(f"No .json files found in {self.segmented_text_dir}")
        
        return json_files[0]
    
    def load_prompt(self) -> str:
        """Load the translation prompt from file."""
        with open(str(self.prompt_file), 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_segmented_book(self) -> List[Dict]:
        """Load the segmented book from JSON file."""
        with open(str(self.segmented_book_file), 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_model_info(self) -> Dict:
        """Load model information from YAML file."""
        with open(str(self.model_info_file), 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def prepare_paragraphs_for_chunking(self) -> List[Dict]:
        """
        Prepare paragraphs with token counts for ChunkMapper.
        
        Returns:
            List of dictionaries with paragraph_id, text, and token_count
        """
        paragraphs_with_tokens = []
        
        for paragraph in self.segmented_book:
            par_id = paragraph['par_id']
            sentences = paragraph['sentences']
            
            # Join sentences to create paragraph text
            text = ' '.join(sentences)
            
            # Count tokens for this paragraph
            token_count = self.token_counter.count_tokens(text)
            
            paragraphs_with_tokens.append({
                'paragraph_id': par_id,
                'text': text,
                'token_count': token_count
            })
        
        return paragraphs_with_tokens
    
    def merge_paragraphs_into_chunks(
        self,
        chunk_mapping: Dict[str, List[int]], 
        paragraphs: List[Dict]
    ) -> Dict[str, str]:
        """
        Merge paragraphs into chunks based on chunk mapping.
        
        Args:
            chunk_mapping: Dictionary mapping chunk names to lists of paragraph IDs
            paragraphs: List of paragraph dictionaries with paragraph_id and text
        
        Returns:
            Dictionary mapping chunk names to merged text (paragraphs separated by empty lines)
        """
        # Create a lookup dictionary for quick paragraph access
        paragraph_lookup = {p['paragraph_id']: p['text'] for p in paragraphs}
        
        chunks = {}
        for chunk_name, paragraph_ids in chunk_mapping.items():
            # Merge paragraphs with empty line separator
            chunk_text = '\n\n'.join(paragraph_lookup[pid] for pid in paragraph_ids)
            chunks[chunk_name] = chunk_text
        
        return chunks
    
    def get_output_filename(self) -> str:
        """
        Generate output filename by removing _segmented and adding _translated.
        
        Returns:
            Output filename for translated text
        """
        # Get the filename without path
        filename = self.segmented_book_file.stem
        
        # Remove _segmented suffix if present
        if filename.endswith('_segmented'):
            filename = filename[:-len('_segmented')]
        
        # Add _translated suffix
        filename = filename + '_translated.txt'
        
        return filename
    
    @staticmethod
    def format_elapsed_time(seconds: float) -> str:
        """Format elapsed time in a readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def run(self):
        """Main translation workflow."""
        
        # Start timing
        script_start_time = time.time()
        
        print("="*80)
        print("BOOK TRANSLATION SCRIPT")
        print("="*80)
        
        # Step 1: Load all required data
        step_start_time = time.time()
        print("\n[1/7] Loading prompt, segmented book, and model info...")
        
        self.prompt = self.load_prompt()
        self.segmented_book = self.load_segmented_book()
        self.model_info = self.load_model_info()
        
        print(f"  ✓ Loaded prompt from {self.prompt_file.name}")
        print(f"  ✓ Loaded {len(self.segmented_book)} paragraphs from {self.segmented_book_file.name}")
        print(f"  ✓ Loaded model info from {self.model_info_file.name}")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Step 2: Prepare paragraphs for chunking
        step_start_time = time.time()
        print("\n[2/7] Counting tokens for each paragraph...")
        
        paragraphs = self.prepare_paragraphs_for_chunking()
        total_input_tokens_estimated = sum(p['token_count'] for p in paragraphs)
        
        print(f"  ✓ Processed {len(paragraphs)} paragraphs")
        print(f"  ✓ Estimated total input tokens: {total_input_tokens_estimated:,}")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Step 3: Use ChunkMapper to create chunk mapping
        step_start_time = time.time()
        print("\n[3/7] Creating chunk mapping...")
        
        max_input_tokens = self.chunk_mapper.calculate_max_input_token()
        print(f"  ✓ Max input tokens per chunk: {max_input_tokens:,}")
        
        chunk_mapping = self.chunk_mapper.map_chunk_paragraphs(paragraphs)
        
        print(f"  ✓ Created {len(chunk_mapping)} chunks")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Step 4: Merge paragraphs into chunks
        step_start_time = time.time()
        print("\n[4/7] Merging paragraphs into chunks...")
        
        chunks = self.merge_paragraphs_into_chunks(chunk_mapping, paragraphs)
        
        for chunk_name, chunk_text in list(chunks.items())[:3]:  # Show first 3
            print(f"  ✓ {chunk_name}: {len(chunk_text)} characters")
        if len(chunks) > 3:
            print(f"  ... and {len(chunks) - 3} more chunks")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Step 5: Translate chunks
        step_start_time = time.time()
        print(f"\n[5/7] Translating {len(chunks)} chunks...")
        print(f"  Source: {self.source_language} → Target: {self.target_language}\n")
        
        # Dictionary to store translations: chunk_name -> translation
        # This allows us to keep track of chunk order and handle retries
        chunk_translations = {}
        failed_chunks = []  # List of (chunk_name, chunk_text) tuples to retry
        
        for i, (chunk_name, chunk_text) in enumerate(chunks.items(), 1):
            print(f"  [{i}/{len(chunks)}] Translating {chunk_name}...", end=" ", flush=True)
            
            # Translate the chunk
            result = self.translator.translate_text(
                text=chunk_text,
                target_language=self.target_language,
                source_language=self.source_language,
                thinking_budget=self.thinking_enabled
            )
            
            if result['success']:
                translated_text = result['translated_text']
                chunk_translations[chunk_name] = translated_text
                
                # Get usage metadata and add to totals
                actual_tokens = result.get('actual_tokens', {})
                self.tot_input_tokens += actual_tokens.get('prompt_tokens', 0)
                self.tot_output_tokens += actual_tokens.get('completion_tokens', 0)
                self.tot_thinking_tokens += actual_tokens.get('thoughts_tokens', 0)
                
                print(f"✓ ({actual_tokens.get('total_tokens', 0):,} tokens)")
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Error: {error_msg}")
                # Track failed chunk for retry
                failed_chunks.append((chunk_name, chunk_text))
                chunk_translations[chunk_name] = f"[TRANSLATION FAILED: {error_msg}]"
            
            # Sleep between chunks (except after the last one)
            if i < len(chunks):
                time.sleep(10)
        
        # Retry failed chunks
        if failed_chunks:
            time.sleep(60)
            print(f"\n  ⚠ {len(failed_chunks)} chunk(s) failed. Retrying...")
            retry_success_count = 0
            
            for i, (chunk_name, chunk_text) in enumerate(failed_chunks, 1):
                print(f"  [Retry {i}/{len(failed_chunks)}] Retrying {chunk_name}...", end=" ", flush=True)
                
                result = self.translator.translate_text(
                    text=chunk_text,
                    target_language=self.target_language,
                    source_language=self.source_language,
                    thinking_budget=self.thinking_enabled
                )
                
                if result['success']:
                    translated_text = result['translated_text']
                    chunk_translations[chunk_name] = translated_text
                    
                    # Add tokens from successful retry (not double-counting)
                    actual_tokens = result.get('actual_tokens', {})
                    self.tot_input_tokens += actual_tokens.get('prompt_tokens', 0)
                    self.tot_output_tokens += actual_tokens.get('completion_tokens', 0)
                    self.tot_thinking_tokens += actual_tokens.get('thoughts_tokens', 0)
                    
                    print(f"✓ ({actual_tokens.get('total_tokens', 0):,} tokens)")
                    retry_success_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"✗ Still failed: {error_msg}")
                    # Keep the failed message
                
                # Sleep between retries (except after the last one)
                if i < len(failed_chunks):
                    time.sleep(10)
            
            print(f"\n  ✓ Successfully recovered {retry_success_count}/{len(failed_chunks)} chunk(s)")
        
        # Build final list in original chunk order
        all_translated_chunks = [chunk_translations[name] for name in chunks.keys()]
        
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Print token usage summary
        print("\n" + "="*80)
        print("TRANSLATION COMPLETE - TOKEN USAGE SUMMARY")
        print("="*80)
        print(f"  Input Tokens:            {self.tot_input_tokens:,}")
        print(f"  Output Tokens:           {self.tot_output_tokens:,}")
        print(f"  Thinking Tokens:         {self.tot_thinking_tokens:,}")
        print(f"  Total Tokens:            {self.tot_input_tokens + self.tot_output_tokens + self.tot_thinking_tokens:,}")
        print("="*80)
        
        # Step 6: Save translated text and monitoring file
        step_start_time = time.time()
        output_filename = self.get_output_filename()
        output_path = self.translated_text_dir / output_filename
        
        print(f"\n[6/7] Saving translated text to {output_filename}...")
        
        # Join all translated chunks with empty lines
        final_translated_text = '\n\n'.join(all_translated_chunks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_translated_text)
        
        print(f"  ✓ Saved {len(final_translated_text)} characters to {output_path}")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        # Step 7: Save translation monitoring file
        print(f"\n[7/7] Saving translation monitoring file...")
        
        # Create monitoring data structure
        monitoring_data = []
        for chunk_name in chunks.keys():
            monitoring_entry = {
                "chunk_id": chunk_name,
                "translated_chunk": chunk_translations[chunk_name],
                "paragraphs_ids": chunk_mapping[chunk_name]
            }
            monitoring_data.append(monitoring_entry)
        
        # Generate monitoring filename
        monitoring_filename = self.segmented_book_file.stem
        if monitoring_filename.endswith('_segmented'):
            monitoring_filename = monitoring_filename[:-len('_segmented')]
        monitoring_filename = monitoring_filename + '_translation_monitoring.json'
        monitoring_path = self.translated_text_dir / monitoring_filename
        
        # Save monitoring file
        with open(monitoring_path, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Saved {len(monitoring_data)} chunks to {monitoring_path}")
        print(f"  ⏱ Elapsed time: {self.format_elapsed_time(time.time() - script_start_time)}")
        
        print("\n" + "="*80)
        print("TRANSLATION COMPLETE!")
        print(f"Total time: {self.format_elapsed_time(time.time() - script_start_time)}")
        print("="*80)


def main():
    """Main entry point for command-line usage."""
    # Initialize required dependencies externally
    model_name = "gemini-2.5-flash"
    
    # Initialize token counter
    token_counter = TokenCounter(
        model_name=model_name,
        provider="tiktoken",  # Fast local counting
        api_key=None,
        base_url=None
    )
    
    # Initialize translator
    translator = Translator(model_name=model_name)
    
    # Load model info to configure chunk mapper
    script_dir = Path(__file__).parent
    model_info_file = script_dir / "models_info.yaml"
    with open(str(model_info_file), 'r', encoding='utf-8') as f:
        model_info = yaml.safe_load(f)
    
    # Find model config
    model_config = None
    for key in model_info.keys():
        if model_name in key:
            model_config = model_info[key]
            break
    
    if model_config is None:
        print(f"Error: Model configuration not found for {model_name}")
        return
    
    # Initialize chunk mapper
    chunk_mapper = ChunkMapper(
        max_output_token=model_config['max_output_tokens'],
        output_input_token_ratio=model_config['output_input_token_ratio']
    )
    
    # Initialize BookTranslator with dependencies
    book_translator = BookTranslator(
        chunk_mapper=chunk_mapper,
        translator=translator,
        token_counter=token_counter
    )
    
    # Run translation
    book_translator.run()


if __name__ == "__main__":
    main()

