import json

def sum_all_tokens(json_file_path):
    """Sum all token counts from the segmented JSON file."""
    total_tokens = 0
    
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    for paragraph in data:
        if 'token_counts' in paragraph:
            total_tokens += sum(paragraph['token_counts'])
    
    return total_tokens

if __name__ == "__main__":
    json_file = "segmented_text_output/Cujo - Stephen King_segmented.json"
    total = sum_all_tokens(json_file)
    print(f"Total tokens: {total}")
