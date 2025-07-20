import os
from PyPDF2 import PdfReader

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for PDF files in the pdf_input folder (relative to project root)
    project_root = os.path.dirname(script_dir)
    pdf_input_dir = os.path.join(project_root, "pdf_input")
    
    if not os.path.exists(pdf_input_dir):
        raise FileNotFoundError(f"PDF input directory '{pdf_input_dir}' not found.")
    
    # Find the first PDF file in the pdf_input directory
    pdf_files = [f for f in os.listdir(pdf_input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in '{pdf_input_dir}' directory.")
    pdf_path = os.path.join(pdf_input_dir, pdf_files[0])

    # Output text file in the 'convert text to audio' folder (relative to project root)
    project_root = os.path.dirname(script_dir)
    output_folder = os.path.join(project_root, "convert ebook to text")
    os.makedirs(output_folder, exist_ok=True)
    text_path = os.path.join(output_folder, os.path.splitext(os.path.basename(pdf_path))[0] + ".txt")

    with open(pdf_path, "rb") as file:
        reader = PdfReader(file)
        with open(text_path, "w", encoding="utf-8") as out:
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    out.write(text)
                    out.write("\n\n")
    # Print only the output .txt file path for pipeline use
    print(text_path)

if __name__ == "__main__":
    main() 