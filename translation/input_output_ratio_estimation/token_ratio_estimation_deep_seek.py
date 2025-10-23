import json
import csv
import sys
from pathlib import Path

# Add parent directory to path to import translator
sys.path.insert(0, str(Path(__file__).parent.parent))
from translator import Translator


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Model to use for translation
MODEL_NAME = "deepseek-chat"

# Input and output files (segmented file is in the parent directory)
INPUT_JSON_FILE = "../Cujo - Stephen King_segmented.json"
OUTPUT_CSV_FILE = "deepseek_token_ratio.csv"

# ============================================================================


def load_segmented_json(file_path):
    """Load the segmented JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def combine_paragraphs(paragraphs_data, start_idx, end_idx):
    """
    Combine paragraphs from start_idx to end_idx into a single text.
    
    Args:
        paragraphs_data: List of paragraph dictionaries
        start_idx: Starting paragraph index (inclusive)
        end_idx: Ending paragraph index (inclusive)
    
    Returns:
        Combined text string
    """
    combined_text = []
    
    for i in range(start_idx, end_idx + 1):
        if i < len(paragraphs_data):
            paragraph = paragraphs_data[i]
            # Join all sentences in the paragraph
            paragraph_text = ' '.join(paragraph['sentences'])
            combined_text.append(paragraph_text)
    
    # Join paragraphs with double newline
    return '\n\n'.join(combined_text)


def main():
    """Main function to estimate token ratio."""
    
    # Set up file paths
    json_file = Path(__file__).parent / INPUT_JSON_FILE
    output_csv = Path(__file__).parent / OUTPUT_CSV_FILE
    
    # Load the segmented data
    print(f"Loading segmented data from: {json_file}")
    paragraphs_data = load_segmented_json(json_file)
    total_paragraphs = len(paragraphs_data)
    print(f"Total paragraphs available: {total_paragraphs}")
    
    # Initialize translator
    print(f"\nInitializing translator with model: {MODEL_NAME}")
    translator = Translator(MODEL_NAME)
    
    # Prepare CSV file
    csv_data = []
    csv_data.append(['input_tokens', 'output_tokens'])
    
    # Translation parameters
    target_language = "Italian"
    source_language = "English"
    
    # Specific sequence of paragraph counts to test
    paragraph_counts = [10, 20, 30, 40, 50, 70, 90, 120, 150]
    start_idx = 0
    
    print(f"\n{'='*80}")
    print("Starting cumulative translation with custom sequence...")
    print(f"Testing with paragraph counts: {paragraph_counts}")
    print(f"{'='*80}\n")
    
    for batch_num, num_paragraphs in enumerate(paragraph_counts, start=1):
        # Skip if we don't have enough paragraphs
        if num_paragraphs > total_paragraphs:
            print(f"\nSkipping batch {batch_num}: Requested {num_paragraphs} paragraphs but only {total_paragraphs} available")
            continue
        
        current_end_idx = start_idx + num_paragraphs - 1
        
        # Combine paragraphs
        text_to_translate = combine_paragraphs(paragraphs_data, start_idx, current_end_idx)
        
        print(f"\nBatch {batch_num}: Translating paragraphs {start_idx}-{current_end_idx} ({num_paragraphs} paragraphs)")
        print(f"Text length: {len(text_to_translate)} characters")
        print("-" * 80)
        
        # Translate
        result = translator.translate_text(
            text=text_to_translate,
            target_language=target_language,
            source_language=source_language
        )
        
        # Extract token information
        if result.get('success'):
            actual_tokens = result.get('actual_tokens', {})
            input_tokens = actual_tokens.get('prompt_tokens', 0)
            output_tokens = actual_tokens.get('completion_tokens', 0)
            reasoning_tokens = actual_tokens.get('reasoning_tokens', 0)
            total_tokens = actual_tokens.get('total_tokens', 0)
            
            print(f"\nToken counts:")
            print(f"  Input tokens:     {input_tokens:,}")
            print(f"  Output tokens:    {output_tokens:,}")
            print(f"  Reasoning tokens: {reasoning_tokens:,}")
            print(f"  Total tokens:     {total_tokens:,}")
            
            if input_tokens > 0:
                ratio = output_tokens / input_tokens
                print(f"  Output/Input ratio: {ratio:.4f}")
            
            # Add to CSV data
            csv_data.append([input_tokens, output_tokens])
            
            print(f"\n✓ Batch {batch_num} completed successfully")
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"\n✗ Batch {batch_num} failed: {error_msg}")
            # Still add a row to maintain structure, but with zeros
            csv_data.append([0, 0])
        
        print("=" * 80)
    
    # Save to CSV
    print(f"\nSaving results to: {output_csv}")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    
    print(f"\n✓ Results saved successfully!")
    print(f"Total batches processed: {len(csv_data) - 1}")  # -1 for header
    
    # Calculate and display average ratio
    if len(csv_data) > 1:
        total_input = sum(row[0] for row in csv_data[1:])
        total_output = sum(row[1] for row in csv_data[1:])
        
        if total_input > 0:
            avg_ratio = total_output / total_input
            print(f"\nOverall statistics:")
            print(f"  Total input tokens:  {total_input:,}")
            print(f"  Total output tokens: {total_output:,}")
            print(f"  Average output/input ratio: {avg_ratio:.4f}")


if __name__ == "__main__":
    main()

