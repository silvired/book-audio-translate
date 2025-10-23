import json
import os
import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Class constant for the model - using a model better suited for text editing
MODEL_NAME = "google/mt5-base"  # Smaller multilingual T5 model for translation tasks

class paragraph_smoother:
    """
    A class to smooth and refine translated paragraphs using a language model.
    """
    
    
    def __init__(self):
        """
        Initialize the paragraph smoother with the specified model.
        """
        self.model_name = MODEL_NAME
        self.tokenizer = None
        self.model = None
        self.translated_paragraphs = []
        self.original_paragraphs = []
        
    def load_model(self):
        """
        Load the tokenizer and model for text generation.
        """
        print(f"Loading model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )
        print("Model loaded successfully!")
        
    def read_translated_text(self, translated_text_folder="translated_text"):
        """
        Read the first file in the translated_text folder and extract paragraphs.
        Each non-empty line is treated as a paragraph.
        """
        translated_files = [f for f in os.listdir(translated_text_folder) if f.endswith('.txt')]
        if not translated_files:
            raise FileNotFoundError("No .txt files found in translated_text folder")
            
        # Get the first file
        first_file = sorted(translated_files)[0]
        file_path = os.path.join(translated_text_folder, first_file)
        
        print(f"Reading translated text from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Filter out empty lines and strip whitespace
        self.translated_paragraphs = [line.strip() for line in lines if line.strip()]
        
        print(f"Loaded {len(self.translated_paragraphs)} translated paragraphs")
        
    def read_segmented_sentences(self, segmented_folder="segmented_text_output"):
        """
        Read the first file in the segmented_text_output folder and join sentences to create paragraphs.
        """
        segmented_files = [f for f in os.listdir(segmented_folder) if f.endswith('.json')]
        if not segmented_files:
            raise FileNotFoundError("No .json files found in segmented_text_output folder")
            
        # Get the first file
        first_file = sorted(segmented_files)[0]
        file_path = os.path.join(segmented_folder, first_file)
        
        print(f"Reading segmented sentences from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Join sentences for each paragraph
        self.original_paragraphs = []
        for paragraph_data in data:
            sentences = paragraph_data.get('sentences', [])
            if sentences:
                # Join sentences with spaces
                paragraph = ' '.join(sentences)
                self.original_paragraphs.append(paragraph)
                
        print(f"Loaded {len(self.original_paragraphs)} original paragraphs")
        
    def create_prompt(self, original_paragraph, translated_paragraph):
        """
        Create the prompt for the model with the specified format.
        """
        prompt = f"""Refine this Italian translation to make it more natural and fluent while keeping the same meaning:

English: {original_paragraph}

Italian translation to improve: {translated_paragraph}

Improved Italian translation:"""
        
        return prompt
        
    def smooth_paragraph(self, original_paragraph, translated_paragraph):
        """
        Use the model to smooth a single paragraph pair.
        """
        prompt = self.create_prompt(original_paragraph, translated_paragraph)
        
        # Tokenize the input without truncation to preserve full context
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        
        try:
            # Generate response with parameters suitable for flan-t5
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=512,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    attention_mask=inputs.attention_mask,
                    early_stopping=True,
                    repetition_penalty=1.1,
                    no_repeat_ngram_size=2
                )
                
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Debug: Print the response to see what the model is generating
            print(f"DEBUG - Full response length: {len(response)}")
            print(f"DEBUG - Full response: {response}")
            
            # For flan-t5, the response should be the generated text directly
            # Remove the input prompt from the response
            if prompt in response:
                smoothed_translation = response.replace(prompt, "").strip()
            else:
                # If prompt not found, use the full response
                smoothed_translation = response.strip()
            
            # Clean up any remaining artifacts
            smoothed_translation = smoothed_translation.replace("Thank you", "").strip()
            smoothed_translation = smoothed_translation.replace("Please provide only the final polished Italian translation, no description whatsoever.", "").strip()
            
            # If we still don't have a good result, return the original translation
            if not smoothed_translation or len(smoothed_translation) < 5:
                print("DEBUG - Response too short or empty, using original translation")
                smoothed_translation = translated_paragraph
            else:
                print(f"DEBUG - Final smoothed translation: {smoothed_translation[:100]}...")
                
            return smoothed_translation
            
        except Exception as e:
            print(f"Generation error: {e}, using original translation")
            return translated_paragraph
        
    def smooth_all_paragraphs(self):
        """
        Smooth all paragraph pairs using the model.
        """
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call load_model() first.")
            
        if not self.original_paragraphs or not self.translated_paragraphs:
            raise ValueError("Paragraphs not loaded. Call read_segmented_sentences() and read_translated_text() first.")
            
        # Ensure we have the same number of paragraphs
        min_paragraphs = min(len(self.original_paragraphs), len(self.translated_paragraphs))
        
        print(f"Smoothing {min_paragraphs} paragraph pairs...")
        
        smoothed_paragraphs = []
        for i in range(min_paragraphs):
            print(f"Processing paragraph {i+1}/{min_paragraphs}...")
            
            original = self.original_paragraphs[i]
            translated = self.translated_paragraphs[i]
            
            # For very short paragraphs, skip smoothing to avoid issues
            if len(translated.strip()) < 10:
                print(f"⚠ Paragraph {i+1} too short, skipping smoothing")
                smoothed_paragraphs.append(translated)
                continue
            
            try:
                start_time = time.time()
                smoothed = self.smooth_paragraph(original, translated)
                elapsed_time = time.time() - start_time
                print(f"✓ Paragraph {i+1} smoothed successfully ({elapsed_time:.1f}s)")
                smoothed_paragraphs.append(smoothed)
            except Exception as e:
                print(f"✗ Error smoothing paragraph {i+1}: {e}")
                # Fallback to original translation
                smoothed_paragraphs.append(translated)
                
        return smoothed_paragraphs
        
    def save_smoothed_paragraphs(self, smoothed_paragraphs, output_folder="smoothed_paragraphs"):
        """
        Save smoothed paragraphs to a file in the specified folder.
        """
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Save to file
        output_file = os.path.join(output_folder, "smoothed_paragraphs.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            for paragraph in smoothed_paragraphs:
                f.write(paragraph + '\n\n')
        
        print(f"Smoothed paragraphs saved to: {output_file}")
        
    def run_full_pipeline(self):
        """
        Run the complete pipeline: load model, read data, and smooth paragraphs.
        """
        print("Starting paragraph smoothing pipeline...")
        
        # Load model
        self.load_model()
        
        # Read data
        self.read_segmented_sentences()
        self.read_translated_text()
        
        # Smooth paragraphs
        smoothed_paragraphs = self.smooth_all_paragraphs()
        
        # Save smoothed paragraphs to file
        self.save_smoothed_paragraphs(smoothed_paragraphs)
        
        print(f"Pipeline completed! Smoothed {len(smoothed_paragraphs)} paragraphs.")
        return smoothed_paragraphs


def main():
    """
    Main function to demonstrate the paragraph smoother.
    """
    smoother = paragraph_smoother()
    
    try:
        smoothed_paragraphs = smoother.run_full_pipeline()
        
    except Exception as e:
        print(f"Error running pipeline: {e}")


if __name__ == "__main__":
    main()
