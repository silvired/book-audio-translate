import os
from abc import ABC, abstractmethod
from PyPDF2 import PdfReader


class BookToText(ABC):
    """
    Abstract base class for converting different book formats to text.
    """
    # Default folder paths as class attributes
    DEFAULT_INPUT_FOLDER = "input_book"
    DEFAULT_OUTPUT_FOLDER = "text_output"
    
    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize the converter with input and output directories.
        
        Args:
            input_dir (str): Directory containing input files. If None, uses DEFAULT_INPUT_FOLDER.
            output_dir (str): Directory for output files. If None, uses DEFAULT_OUTPUT_FOLDER.
        """
        # Get the directory where this script is located (now in main directory)
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        if input_dir is None:
            input_dir = os.path.join(project_root, self.DEFAULT_INPUT_FOLDER)
        if output_dir is None:
            output_dir = os.path.join(project_root, self.DEFAULT_OUTPUT_FOLDER)
        
        self.input_dir = input_dir
        self.output_dir = output_dir
    
    @abstractmethod
    def convert_to_text(self, file_path):
        """
        Convert a book file to text.
        
        Args:
            file_path (str): Path to the book file to convert.
            
        Returns:
            str: Path to the output text file.
        """
        pass
    
    def find_input_file(self, extension):
        """
        Find the first file with the given extension in the input directory.
        
        Args:
            extension (str): File extension to search for (e.g., '.pdf').
            
        Returns:
            str: Path to the found file.
            
        Raises:
            FileNotFoundError: If no files with the extension are found.
        """
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Input directory '{self.input_dir}' not found.")
        
        files = [f for f in os.listdir(self.input_dir) if f.lower().endswith(extension)]
        if not files:
            raise FileNotFoundError(f"No {extension} files found in '{self.input_dir}' directory.")
        
        return os.path.join(self.input_dir, files[0])
    
    def get_output_path(self, input_file_path, output_extension='.txt'):
        """
        Generate output file path based on input file path.
        
        Args:
            input_file_path (str): Path to the input file.
            output_extension (str): Extension for the output file.
            
        Returns:
            str: Path to the output file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        return os.path.join(self.output_dir, base_name + output_extension)


class PDFToText(BookToText):
    """
    Concrete class for converting PDF files to text.
    """
    
    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize PDF to text converter.
        
        Args:
            input_dir (str): Directory containing PDF files. If None, uses 'input_book'.
            output_dir (str): Directory for output text files. If None, uses 'text_output'.
        """
        super().__init__(input_dir, output_dir)
    
    def convert_to_text(self, file_path):
        """
        Convert a PDF file to text.
        
        Args:
            file_path (str): Path to the PDF file to convert.
            
        Returns:
            str: Path to the output text file.
        """
        output_path = self.get_output_path(file_path)
        
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            with open(output_path, "w", encoding="utf-8") as out:
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        out.write(text)
                        out.write("\n\n")
        
        return output_path
    
    def convert_first_pdf(self):
        """
        Find and convert the first PDF file in the input directory.
        
        Returns:
            str: Path to the output text file.
        """
        pdf_path = self.find_input_file('.pdf')
        return self.convert_to_text(pdf_path) 