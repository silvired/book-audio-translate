import os
import glob
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black


class TextToPDFConverter:
    """
    A class to convert translated text files to PDF format.
    Reads the first file from translated_text folder and creates a PDF
    with title page and content pages.
    """
    
    def __init__(self, translated_text_folder="translated_text", pdf_output_folder="pdf_output"):
        """
        Initialize the converter with folder paths.
        
        Args:
            translated_text_folder (str): Path to folder containing translated text files
            pdf_output_folder (str): Path to folder where PDF will be saved
        """
        self.translated_text_folder = translated_text_folder
        self.pdf_output_folder = pdf_output_folder
        self.styles = getSampleStyleSheet()
        
        # Create output folder if it doesn't exist
        os.makedirs(self.pdf_output_folder, exist_ok=True)
        
        # Setup custom styles
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Title style for the first page
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=black
        )
        
        # Main content style
        self.content_style = ParagraphStyle(
            'CustomContent',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            textColor=black
        )
        
        # Author style (if needed)
        self.author_style = ParagraphStyle(
            'CustomAuthor',
            parent=self.styles['Normal'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=black
        )
    
    def get_first_translated_file(self):
        """
        Get the first file from the translated_text folder.
        
        Returns:
            str: Path to the first translated text file
        """
        if not os.path.exists(self.translated_text_folder):
            raise FileNotFoundError(f"Translated text folder '{self.translated_text_folder}' not found")
        
        # Get all .txt files in the translated_text folder
        txt_files = glob.glob(os.path.join(self.translated_text_folder, "*.txt"))
        
        if not txt_files:
            raise FileNotFoundError(f"No .txt files found in '{self.translated_text_folder}'")
        
        # Sort files and return the first one
        txt_files.sort()
        return txt_files[0]
    
    def extract_book_title(self, file_path):
        """
        Extract book title from the filename.
        
        Args:
            file_path (str): Path to the translated text file
            
        Returns:
            str: Extracted book title
        """
        filename = os.path.basename(file_path)
        # Remove the '_segmented_translated.txt' suffix and clean up
        title = filename.replace('_segmented_translated.txt', '')
        title = title.replace('_', ' ')
        return title
    
    def read_translated_text(self, file_path):
        """
        Read the translated text from the file.
        
        Args:
            file_path (str): Path to the translated text file
            
        Returns:
            list: List of text lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            raise Exception(f"Error reading file '{file_path}': {str(e)}")
    
    def create_pdf(self):
        """
        Create PDF from the first translated text file.
        
        Returns:
            str: Path to the created PDF file
        """
        try:
            # Get the first translated file
            file_path = self.get_first_translated_file()
            print(f"Processing file: {file_path}")
            
            # Extract book title
            book_title = self.extract_book_title(file_path)
            print(f"Book title: {book_title}")
            
            # Read translated text
            text_lines = self.read_translated_text(file_path)
            print(f"Read {len(text_lines)} lines of text")
            
            # Create PDF filename
            pdf_filename = f"{book_title}.pdf"
            pdf_path = os.path.join(self.pdf_output_folder, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            
            # Add title page
            story.append(Spacer(1, 2*inch))  # Add space at top
            story.append(Paragraph(book_title, self.title_style))
            story.append(Spacer(1, 0.5*inch))
            
            # Add page break after title
            story.append(PageBreak())
            
            # Add content pages
            for line in text_lines:
                if line.strip():  # Skip empty lines
                    # Clean up the text (remove extra spaces, handle special characters)
                    cleaned_line = line.strip()
                    if cleaned_line:
                        story.append(Paragraph(cleaned_line, self.content_style))
                        story.append(Spacer(1, 6))  # Small space between paragraphs
            
            # Build PDF
            doc.build(story)
            
            print(f"PDF created successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            raise


def main():
    """Main function to run the text to PDF conversion."""
    try:
        # Create converter instance
        converter = TextToPDFConverter()
        
        # Convert text to PDF
        pdf_path = converter.create_pdf()
        
        print(f"\nConversion completed successfully!")
        print(f"PDF saved to: {pdf_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()

