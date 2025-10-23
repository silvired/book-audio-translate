import os
import csv
import json
import re
import requests
import time
from pathlib import Path

# Constants - Configure these for your evaluation
FILE_NAME = "deepseek-v3_translation.txt"  # The translation file to evaluate
INPUT_FOLDER = "5_pages_test_translations"  # Folder containing the translation files
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


def extract_model_name(filename):
    """Extract model name from translation filename."""
    # Remove '_translation.txt' suffix
    return filename.replace('_translation.txt', '')


def load_translation(filename):
    """Load a single translation file."""
    filepath = os.path.join(INPUT_FOLDER, filename)
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


def append_result_to_csv(model_name, scores):
    """Append a single evaluation result to the CSV file."""
    # Check if CSV exists to determine if we need to write header
    file_exists = os.path.exists(OUTPUT_CSV)
    
    # Read existing fieldnames if file exists
    if file_exists:
        with open(OUTPUT_CSV, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_fieldnames = reader.fieldnames
    else:
        # If file doesn't exist, create fieldnames from the scores
        existing_fieldnames = ['model_name'] + sorted(scores.keys())
    
    # Merge fieldnames (in case new criteria are added)
    all_fields = set(existing_fieldnames)
    all_fields.update(scores.keys())
    all_fields.add('model_name')
    
    # Sort fields: model_name first, then alphabetically
    fieldnames = ['model_name'] + sorted([f for f in all_fields if f != 'model_name'])
    
    # Prepare the result row
    result = {'model_name': model_name}
    result.update(scores)
    
    # If fieldnames changed, we need to rewrite the whole file
    if file_exists and set(fieldnames) != set(existing_fieldnames):
        # Read all existing rows
        with open(OUTPUT_CSV, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_rows = list(reader)
        
        # Write all rows with updated fieldnames
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow(result)
    else:
        # Simply append the new row
        mode = 'a' if file_exists else 'w'
        with open(OUTPUT_CSV, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)
    
    print(f"\nResult appended to {OUTPUT_CSV}")
    print(f"Model: {model_name}")
    print(f"Scores: {scores}")


def main():
    """Main function to run the single translation evaluation."""
    print(f"Evaluating translation: {FILE_NAME}")
    print(f"From folder: {INPUT_FOLDER}")
    
    # Verify file exists
    file_path = os.path.join(INPUT_FOLDER, FILE_NAME)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return
    
    print("\nLoading prompt template...")
    prompt_template = load_prompt_template()
    
    print("Loading original text...")
    original_text = load_original_text()
    
    print("Loading translation...")
    translated_text = load_translation(FILE_NAME)
    
    print(f"\nEvaluating translation...")
    model_name = extract_model_name(FILE_NAME)
    
    try:
        # Evaluate translation
        evaluation_response = evaluate_translation(original_text, translated_text, prompt_template)
        
        # Print raw response for debugging
        print(f"\n  Raw API Response:")
        print(f"  {'-' * 60}")
        print(f"  {evaluation_response}")
        print(f"  {'-' * 60}\n")
        
        # Parse scores
        scores = parse_evaluation_scores(evaluation_response)
        
        # Print all scores
        print(f"  Parsed scores:")
        for key, value in scores.items():
            print(f"    {key}: {value}")
        
        # Append to CSV
        append_result_to_csv(model_name, scores)
        
        print("\nEvaluation complete!")
        
    except Exception as e:
        print(f"  Error evaluating {model_name}: {str(e)}")
        raise


if __name__ == "__main__":
    main()

