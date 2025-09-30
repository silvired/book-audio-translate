import json
import os
import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class Translator:
    def __init__(self, model_name="Anhptp/opus-mt-en-it-BDS-G1"):
        """
        Initialize the Translator with the specified model.
        
        Args:
            model_name (str): The name of the translation model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the tokenizer and model."""
        print(f"Loading model: {self.model_name}")
        start_time = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        end_time = time.time()
        print(f"Model loaded successfully in {end_time - start_time:.2f} seconds!")
    
    def translate_text(self, text):
        """
        Translate a single text using the loaded model.
        
        Args:
            text (str): The text to translate
            
        Returns:
            str: The translated text
        """
        # Encode the input text
        inputs = self.tokenizer.encode(text, return_tensors="pt")
        
        # Generate translation
        outputs = self.model.generate(inputs)
        
        # Decode the output
        translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return translation
    
    def translate_paragraph(self, sentences):
        """
        Translate a paragraph (list of sentences) and join them.
        
        Args:
            sentences (list): List of sentences in the paragraph
            
        Returns:
            str: The translated paragraph
        """
        translated_sentences = []
        for sentence in sentences:
            if sentence.strip():  # Only translate non-empty sentences
                translated_sentence = self.translate_text(sentence)
                translated_sentences.append(translated_sentence)
        
        return " ".join(translated_sentences)
    
    def translate_json_file(self, json_file_path, output_file_path):
        """
        Translate a JSON file containing segmented text and save to TXT file.
        
        Args:
            json_file_path (str): Path to the input JSON file
            output_file_path (str): Path to the output TXT file
        """
        # Load the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        translated_paragraphs = []
        
        print(f"Translating {len(data)} paragraphs...")
        total_start_time = time.time()
        
        for i, paragraph in enumerate(data):
            print(f"Translating paragraph {i+1}/{len(data)}")
            
            # Translate the paragraph
            translated_paragraph = self.translate_paragraph(paragraph['sentences'])
            translated_paragraphs.append(translated_paragraph)
        
        # Save to TXT file with paragraph separation
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for paragraph in translated_paragraphs:
                f.write(paragraph + '\n\n')  # Two newlines for paragraph separation
        
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        print(f"Translation completed! Output saved to: {output_file_path}")
        print(f"Total translation time: {total_time:.2f} seconds")
    
    def translate_first_json_file(self, segmented_dir="segmented_text_output", output_dir="translated_text"):
        """
        Find and translate the first JSON file in the segmented_text_output directory.
        
        Args:
            segmented_dir (str): Directory containing segmented JSON files
            output_dir (str): Directory to save the translated output
        """
        # Find the first JSON file
        json_files = [f for f in os.listdir(segmented_dir) if f.endswith('.json')]
        
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {segmented_dir}")
        
        # Sort to ensure consistent selection of "first" file
        json_files.sort()
        first_json_file = json_files[0]
        
        print(f"Found JSON file: {first_json_file}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        base_name = os.path.splitext(first_json_file)[0]
        output_filename = f"{base_name}_translated.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        # Full paths
        input_path = os.path.join(segmented_dir, first_json_file)
        
        # Translate the file
        self.translate_json_file(input_path, output_path)


if __name__ == "__main__":
    # Create translator instance
    overall_start_time = time.time()
    translator = Translator()
    
    # Translate the first JSON file
    translator.translate_first_json_file()
    
    overall_end_time = time.time()
    overall_time = overall_end_time - overall_start_time
    print(f"\n=== OVERALL EXECUTION TIME: {overall_time:.2f} seconds ===")
