"""
Book Cost Estimator Script

This script estimates translation costs for a book using different model configurations.
It uses ChunkMapper to split the book into chunks, TokenCounter to estimate token usage,
and CostCalculator to estimate costs for various pricing models.
"""

import json
import yaml
from chunk_mapper import ChunkMapper
from cost_calculator import CostCalculator
from token_counter import TokenCounter


# ========== FILE PATH CONSTANTS ==========
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

PROMPT_FILE = "translation_prompt.txt"
SEGMENTED_BOOK_FILE = "Cujo - Stephen King_segmented.json"
MODEL_INFO_FILE = "models_info.yaml"

# Translation languages (modify as needed)
SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "Italian"


def load_model_info(file_path):
    """Load model information from YAML file."""
    with open(str(file_path), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def estimate_cost_for_configuration(
    config_name,
    token_counter,
    chunk_mapper,
    paragraphs_with_tokens,
    prompt_file,
    prices,
    output_input_ratio,
    thinking_input_ratio=None
):
    """
    Estimate cost for a specific model configuration.
    
    Args:
        config_name: Name of the configuration for display
        token_counter: TokenCounter instance
        chunk_mapper: ChunkMapper instance
        paragraphs_with_tokens: List of paragraphs with token counts
        prompt_file: Path to prompt file
        prices: Dictionary with pricing information
        output_input_ratio: Ratio of output to input tokens
        thinking_input_ratio: Optional ratio of thinking to input tokens
    
    Returns:
        Dictionary with cost breakdown and token counts
    """
    print(f"\n{'='*60}")
    print(f"Estimating cost for: {config_name}")
    print(f"{'='*60}")
    
    # Get chunk mapping
    chunk_mapping = chunk_mapper.map_chunk_paragraphs(paragraphs_with_tokens)
    print(f"Number of chunks: {len(chunk_mapping)}")
    
    # Count tokens for prompt
    prompt_tokens_data = token_counter.count_tokens_for_prompt(
        prompt_file_path=str(prompt_file),
        source_language=SOURCE_LANGUAGE,
        target_language=TARGET_LANGUAGE
    )
    prompt_token_count = prompt_tokens_data.get("token_count", 0)
    print(f"Prompt tokens: {prompt_token_count:,}")
    
    # Create segmented tokens data structure (similar to token_counter output)
    segmented_tokens_data = {
        "paragraphs": [
            {
                "par_id": para["paragraph_id"],
                "token_count": para["token_count"]
            }
            for para in paragraphs_with_tokens
        ]
    }
    
    # Count chunk input tokens
    chunk_input_tokens = token_counter.count_chunk_input_tokens(
        segmented_tokens_data=segmented_tokens_data,
        prompt_tokens_data=prompt_tokens_data,
        chunk_mapping=chunk_mapping
    )
    
    # Estimate output and thinking tokens
    chunk_tokens_with_estimates = token_counter.estimate_output_thinking_tokens(
        chunk_input_tokens_data=chunk_input_tokens,
        output_input_ratio=output_input_ratio,
        thinking_input_ratio=thinking_input_ratio
    )
    
    # Calculate total tokens
    total_tokens = token_counter.estimate_total_tokens(
        chunk_tokens_data=chunk_tokens_with_estimates
    )
    
    print(f"Total input tokens: {total_tokens['input']:,}")
    print(f"Total output tokens: {total_tokens['output']:,}")
    if 'thinking' in total_tokens:
        print(f"Total thinking tokens: {total_tokens['thinking']:,}")
    
    # Calculate cost
    cost_calculator = CostCalculator(prices=prices)
    cost_breakdown = cost_calculator.calculate_cost(
        tot_input_token=total_tokens['input'],
        tot_output_token=total_tokens['output'],
        tot_thinking_token=total_tokens.get('thinking', 0)
    )
    
    print(f"\nCost breakdown:")
    print(f"  Input cost: ${cost_breakdown['input_cost']:.4f}")
    print(f"  Output cost: ${cost_breakdown['output_cost']:.4f}")
    if cost_breakdown['thinking_cost'] > 0:
        print(f"  Thinking cost: ${cost_breakdown['thinking_cost']:.4f}")
    print(f"  TOTAL COST: ${cost_breakdown['total_cost']:.4f}")
    
    return {
        "config_name": config_name,
        "num_chunks": len(chunk_mapping),
        "total_tokens": total_tokens,
        "cost_breakdown": cost_breakdown
    }


def main():
    """Main function to estimate costs for all configurations."""
    print("="*60)
    print("BOOK TRANSLATION COST ESTIMATOR")
    print("="*60)
    
    # Load data files
    print("\nLoading data files...")
    model_info = load_model_info(MODEL_INFO_FILE)
    
    print(f"✓ Loaded model info: {len(model_info)} configurations")
    
    # Get model configurations
    gemini_config = model_info.get("gemini-2.5-flash_no_thinking", {})
    deepseek_config = model_info.get("deep-seek-v3-no_thinking", {})
    
    # Initialize token counter (using tiktoken for estimation since no API key)
    token_counter = TokenCounter(
        model_name="gemini-2.5-flash",
        provider="gemini"
    )
    
    print("\nCounting tokens for all paragraphs...")
    # Use the token counter's method to count tokens for the segmented file
    segmented_tokens_data = token_counter.count_tokens_for_segmented_file(
        file_path=str(SEGMENTED_BOOK_FILE),
        output_file_path=None  # Don't save intermediate file
    )
    
    # Convert the paragraph data format for ChunkMapper (par_id -> paragraph_id)
    paragraphs_with_tokens = [
        {
            "paragraph_id": para["par_id"],
            "token_count": para["token_count"]
        }
        for para in segmented_tokens_data["paragraphs"]
    ]
    
    total_paragraph_tokens = segmented_tokens_data["total_input_tokens"]
    print(f"✓ Loaded segmented book: {segmented_tokens_data['total_paragraphs']} paragraphs")
    print(f"✓ Total paragraph tokens: {total_paragraph_tokens:,}")
    
    # Store all results
    all_results = []
    
    # ========== GEMINI WITH THINKING ENABLED - STANDARD PRICING ==========
    chunk_mapper_gemini_thinking = ChunkMapper(
        max_output_token=gemini_config.get("max_output_tokens", 4000),
        output_input_token_ratio=1.22  # Using the first ratio listed in YAML
    )
    
    prices_gemini_standard = {
        'input_token': gemini_config.get("input_price_per_million_tokens", 0.3),
        'output_token': gemini_config.get("output_price_per_million_tokens", 2.5),
        'thinking_token': gemini_config.get("thinking_price_per_million_tokens", 0.3)
    }
    
    result = estimate_cost_for_configuration(
        config_name="Gemini 2.5 Flash - Thinking Enabled - Standard Pricing",
        token_counter=token_counter,
        chunk_mapper=chunk_mapper_gemini_thinking,
        paragraphs_with_tokens=paragraphs_with_tokens,
        prompt_file=PROMPT_FILE,
        prices=prices_gemini_standard,
        output_input_ratio=1.22,
        thinking_input_ratio=3.6  # Using the second ratio as thinking ratio
    )
    all_results.append(result)
    
    # ========== GEMINI WITH THINKING ENABLED - BATCH PRICING ==========
    prices_gemini_batch = {
        'input_token': gemini_config.get("batch_input_price_per_million_tokens", 0.15),
        'output_token': gemini_config.get("batch_output_price_per_million_tokens", 1.25),
        'thinking_token': 0.15  # Using batch input price for thinking
    }
    
    result = estimate_cost_for_configuration(
        config_name="Gemini 2.5 Flash - Thinking Enabled - Batch Pricing",
        token_counter=token_counter,
        chunk_mapper=chunk_mapper_gemini_thinking,
        paragraphs_with_tokens=paragraphs_with_tokens,
        prompt_file=PROMPT_FILE,
        prices=prices_gemini_batch,
        output_input_ratio=1.22,
        thinking_input_ratio=3.6
    )
    all_results.append(result)
    
    # ========== GEMINI WITH THINKING DISABLED - STANDARD PRICING ==========
    chunk_mapper_gemini_no_thinking = ChunkMapper(
        max_output_token=gemini_config.get("max_output_tokens", 4000),
        output_input_token_ratio=1.22
    )
    
    result = estimate_cost_for_configuration(
        config_name="Gemini 2.5 Flash - Thinking Disabled - Standard Pricing",
        token_counter=token_counter,
        chunk_mapper=chunk_mapper_gemini_no_thinking,
        paragraphs_with_tokens=paragraphs_with_tokens,
        prompt_file=PROMPT_FILE,
        prices=prices_gemini_standard,
        output_input_ratio=1.22,
        thinking_input_ratio=None  # No thinking
    )
    all_results.append(result)
    
    # ========== GEMINI WITH THINKING DISABLED - BATCH PRICING ==========
    result = estimate_cost_for_configuration(
        config_name="Gemini 2.5 Flash - Thinking Disabled - Batch Pricing",
        token_counter=token_counter,
        chunk_mapper=chunk_mapper_gemini_no_thinking,
        paragraphs_with_tokens=paragraphs_with_tokens,
        prompt_file=PROMPT_FILE,
        prices=prices_gemini_batch,
        output_input_ratio=1.22,
        thinking_input_ratio=None  # No thinking
    )
    all_results.append(result)
    
    # ========== DEEPSEEK (THINKING DISABLED) ==========
    chunk_mapper_deepseek = ChunkMapper(
        max_output_token=deepseek_config.get("max_output_tokens", 4000),
        output_input_token_ratio=deepseek_config.get("output_input_token_ratio", 1.35)
    )
    
    prices_deepseek = {
        'input_token': deepseek_config.get("input_price_per_million_tokens", 0.28),
        'output_token': deepseek_config.get("output_price_per_million_tokens", 0.42),
        'thinking_token': 0  # Not applicable
    }
    
    result = estimate_cost_for_configuration(
        config_name="DeepSeek V3 - Thinking Disabled",
        token_counter=token_counter,
        chunk_mapper=chunk_mapper_deepseek,
        paragraphs_with_tokens=paragraphs_with_tokens,
        prompt_file=PROMPT_FILE,
        prices=prices_deepseek,
        output_input_ratio=deepseek_config.get("output_input_token_ratio", 1.35),
        thinking_input_ratio=None  # No thinking
    )
    all_results.append(result)
    
    # ========== SUMMARY ==========
    print("\n" + "="*60)
    print("COST SUMMARY")
    print("="*60)
    
    for result in all_results:
        print(f"\n{result['config_name']}")
        print(f"  Chunks: {result['num_chunks']}")
        print(f"  Input tokens: {result['total_tokens']['input']:,}")
        print(f"  Output tokens: {result['total_tokens']['output']:,}")
        if 'thinking' in result['total_tokens']:
            print(f"  Thinking tokens: {result['total_tokens']['thinking']:,}")
        print(f"  TOTAL COST: ${result['cost_breakdown']['total_cost']:.4f}")
    
    # Find cheapest option
    cheapest = min(all_results, key=lambda x: x['cost_breakdown']['total_cost'])
    print(f"\n{'='*60}")
    print(f"CHEAPEST OPTION: {cheapest['config_name']}")
    print(f"Cost: ${cheapest['cost_breakdown']['total_cost']:.4f}")
    print(f"{'='*60}")
    
    # Save results to JSON
    output_file = SCRIPT_DIR / "book_cost_estimation_results.json"
    with open(str(output_file), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()

