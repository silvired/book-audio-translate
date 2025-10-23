import os
import csv
import json
import re
import requests
import time
from pathlib import Path

# Constants
TRANSLATIONS_FOLDER = "5_pages_test_translations"
ORIGINAL_FILE = "Cujo - Stephen King-5.txt"
EVALUATION_MODEL = "deepseek-chat"
PROMPT_FILE = "evaluation_prompt.txt"
OUTPUT_CSV = "translation_evaluations.csv"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def load_prompt_template():
    """Load the evaluation prompt template from file."""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def load_original_text():
    """Load the original English text."""
    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def load_translation_files():
    """Load all translation files from the translations folder."""
    translation_files = []
    for file in os.listdir(TRANSLATIONS_FOLDER):
        if file.endswith('_translation.txt'):
            translation_files.append(file)
    return sorted(translation_files)


def extract_model_name(filename):
    """Extract model name from translation filename."""
    # Remove '_translation.txt' suffix
    return filename.replace('_translation.txt', '')


def load_translation(filename):
    """Load a single translation file."""
    filepath = os.path.join(TRANSLATIONS_FOLDER, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def evaluate_translation(original_text, translated_text, prompt_template):
    """Call DeepSeek API to evaluate the translation."""
    # Substitute the placeholders in the prompt
    prompt = prompt_template.replace('[original]', original_text)
    prompt = prompt.replace('[translation]', translated_text)
    
    # Get API key from environment
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")
    
    # Prepare request payload
    payload = {
        "model": EVALUATION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 8000  # Increased to handle large evaluation responses
    }
    
    # Make API request with retry logic
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            break  # Success, exit retry loop
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503 and attempt < max_retries - 1:
                print(f"  503 error, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise  # Re-raise if not 503 or last attempt
    
    # Parse response
    result = response.json()
    
    # DEBUG: Print raw API response
    print(f"  DEBUG - Raw API Response:")
    print(f"  {json.dumps(result, indent=2)[:1000]}...")  # Print first 1000 chars
    
    if 'choices' in result and len(result['choices']) > 0:
        choice = result['choices'][0]
        
        # Check finish reason
        finish_reason = choice.get('finish_reason', 'unknown')
        if finish_reason == 'length':
            raise Exception("Response was cut off due to max_tokens. Try increasing max_tokens.")
        
        if 'message' in choice and 'content' in choice['message']:
            response_text = choice['message']['content'].strip()
            return response_text
        else:
            raise Exception(f"No 'content' in message. Finish reason: {finish_reason}. Choice keys: {list(choice.keys())}")
    
    raise Exception(f"No choices found in API result. Keys in response: {list(result.keys())}")


def parse_evaluation_scores(evaluation_text):
    """Parse the scores from the evaluation response (JSON format).
    Returns whatever fields the model provides."""
    try:
        # Try to extract JSON from the response (in case there's extra text)
        # Look for JSON object in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', evaluation_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            scores = json.loads(json_str)
            return scores
        else:
            # Try to parse the entire response as JSON
            scores = json.loads(evaluation_text)
            return scores
    except json.JSONDecodeError as e:
        print(f"  WARNING: Failed to parse JSON response: {e}")
        print(f"  Raw response: {evaluation_text[:500]}...")
        return {}


def write_results_to_csv(results):
    """Write evaluation results to CSV file.
    Dynamically determines field names from the results."""
    if not results:
        print("No results to write!")
        return
    
    # Collect all unique field names from all results
    all_fields = set(['model_name'])  # Always include model_name first
    for result in results:
        all_fields.update(result.keys())
    
    # Sort fields: model_name first, then alphabetically
    fieldnames = ['model_name'] + sorted([f for f in all_fields if f != 'model_name'])
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults written to {OUTPUT_CSV}")
    print(f"Fields included: {', '.join(fieldnames)}")


def main():
    """Main function to run the evaluation pipeline."""
    print("Loading prompt template...")
    prompt_template = load_prompt_template()
    
    print("Loading original text...")
    original_text = load_original_text()
    
    print("Finding translation files...")
    translation_files = load_translation_files()
    print(f"Found {len(translation_files)} translation files to evaluate")
    
    results = []
    
    for i, translation_file in enumerate(translation_files, 1):
        model_name = extract_model_name(translation_file)
        print(f"\n[{i}/{len(translation_files)}] Evaluating {model_name}...")
        
        try:
            # Load translation
            translated_text = load_translation(translation_file)
            
            # Evaluate translation
            evaluation_response = evaluate_translation(original_text, translated_text, prompt_template)
            
            # Print raw response for debugging
            print(f"\n  Raw API Response:")
            print(f"  {'-' * 60}")
            print(f"  {evaluation_response}")
            print(f"  {'-' * 60}\n")
            
            # Parse scores
            scores = parse_evaluation_scores(evaluation_response)
            
            # Add model name to results
            result = {'model_name': model_name}
            result.update(scores)
            results.append(result)
            
            # Print all scores dynamically
            print(f"  Parsed scores:")
            for key, value in scores.items():
                print(f"    {key}: {value}")
            
        except Exception as e:
            print(f"  Error evaluating {model_name}: {str(e)}")
            # Add result with just the model name in case of error
            result = {'model_name': model_name}
            results.append(result)
        
        # Add delay between API calls to avoid rate limiting
        if i < len(translation_files):
            time.sleep(5)  # 2 second delay between calls
    
    # Write results to CSV
    write_results_to_csv(results)
    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()
