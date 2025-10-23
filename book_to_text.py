import os
from abc import ABC, abstractmethod
from PyPDF2 import PdfReader
import zipfile
import xml.etree.ElementTree as ET
import re


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

    @staticmethod
    def trim_text_to_first_sentence(text, first_sentence):
        """
        Remove all text before the first occurrence of a given sentence.
        
        Args:
            text (str): The full text to trim.
            first_sentence (str): The sentence to search for.
            
        Returns:
            str: Text starting from (and including) the first sentence.
            
        Raises:
            ValueError: If the first sentence is not found in the text.
        """
        # Try exact match first
        if first_sentence in text:
            index = text.find(first_sentence)
            return text[index:]
        
        # If exact match fails, try case-insensitive search
        text_lower = text.lower()
        first_sentence_lower = first_sentence.lower()
        if first_sentence_lower in text_lower:
            index = text_lower.find(first_sentence_lower)
            return text[index:]
        
        raise ValueError(f"First sentence not found in text:\n'{first_sentence}'")

    @staticmethod
    def get_file_by_extensions(input_dir, *extensions):
        """
        Find the first file with any of the given extensions in the input directory.
        
        Args:
            input_dir (str): Directory to search in.
            *extensions: Variable number of file extensions (e.g., '.pdf', '.epub')
            
        Returns:
            tuple: (file_path, extension) of the found file
            
        Raises:
            FileNotFoundError: If no files with any extension are found.
        """
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory '{input_dir}' not found.")
        
        # Create a list of lowercase extensions for comparison
        extensions_lower = [ext.lower() for ext in extensions]
        
        # Find all files matching any of the extensions
        matching_files = []
        for filename in os.listdir(input_dir):
            file_lower = filename.lower()
            for ext in extensions_lower:
                if file_lower.endswith(ext):
                    matching_files.append(filename)
                    break
        
        if not matching_files:
            extensions_str = ', '.join(extensions)
            raise FileNotFoundError(
                f"No files with extensions {extensions_str} found in '{input_dir}' directory."
            )
        
        # Get the full path and extension of the first matching file
        file_path = os.path.join(input_dir, matching_files[0])
        actual_ext = os.path.splitext(file_path)[1].lower()
        
        return file_path, actual_ext
    
    @staticmethod
    def get_converter_for_file(file_path, input_dir=None, output_dir=None):
        """
        Get the appropriate converter instance for a file based on its extension.
        
        Args:
            file_path (str): Path to the file to convert.
            input_dir (str): Input directory for the converter. If None, uses default.
            output_dir (str): Output directory for the converter. If None, uses default.
            
        Returns:
            BookToText: An instance of the appropriate converter (PDFToText or EpubToText).
            
        Raises:
            ValueError: If file extension is not supported.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            return PDFToText(input_dir, output_dir)
        elif ext == '.epub':
            return EpubToText(input_dir, output_dir)
        else:
            raise ValueError(
                f"Unsupported file format: '{ext}'. "
                f"Supported formats: .pdf, .epub"
            )


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
                        # Try to preserve paragraph structure by looking for multiple newlines
                        # and indentation patterns in the original text
                        import re
                        
                        # First, let's see what the raw text looks like
                        # Don't normalize all whitespace yet - preserve some structure
                        text = text.strip()
                        
                        # Look for patterns that might indicate paragraph breaks:
                        # 1. Multiple consecutive newlines
                        # 2. Lines that start with spaces (indentation)
                        # 3. Preserve some original spacing
                        
                        # Split by multiple newlines to find paragraph boundaries
                        paragraphs = re.split(r'\n\s*\n', text)
                        
                        # If no clear paragraph breaks found, try splitting by single newlines
                        if len(paragraphs) == 1:
                            # Look for lines that might be paragraph starts (indented or after periods)
                            lines = text.split('\n')
                            paragraphs = []
                            current_paragraph = []
                            
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    if current_paragraph:
                                        paragraphs.append(' '.join(current_paragraph))
                                        current_paragraph = []
                                    continue
                                
                                # Check if this line starts a new paragraph
                                # (starts with capital letter after a period, or is indented)
                                if (current_paragraph and 
                                    (line[0].isupper() and 
                                     any(current_paragraph[-1].endswith(p) for p in ['.', '!', '?']))):
                                    # Start new paragraph
                                    paragraphs.append(' '.join(current_paragraph))
                                    current_paragraph = [line]
                                else:
                                    current_paragraph.append(line)
                            
                            if current_paragraph:
                                paragraphs.append(' '.join(current_paragraph))
                        
                        # Write each paragraph with proper spacing
                        for paragraph in paragraphs:
                            if paragraph.strip():
                                # Process different types of dashes before normalizing whitespace
                                paragraph = self._process_dashes(paragraph)
                                # Normalize whitespace within paragraphs
                                paragraph = re.sub(r'\s+', ' ', paragraph.strip())
                                out.write(paragraph)
                                out.write("\n\n")
        
        return output_path
    
    def _process_dashes(self, text):
        """
        Process different types of dashes to add proper spacing.
        
        Args:
            text (str): Input text to process.
            
        Returns:
            str: Text with proper dash spacing.
        """
        import re
        
        # Handle em dashes (—) - these should have spaces around them for punctuation
        # Look for em dashes that are used for punctuation (not in compound words)
        text = re.sub(r'([a-zA-Z])(—)([a-zA-Z])', r'\1 — \3', text)
        
        # Handle cases where em dash is at the beginning or end of a word
        text = re.sub(r'([a-zA-Z])(—)(\s)', r'\1 —\3', text)
        text = re.sub(r'(\s)(—)([a-zA-Z])', r'\1— \3', text)
        
        # Handle en dashes (–) - these are also typically used for punctuation
        text = re.sub(r'([a-zA-Z])(–)([a-zA-Z])', r'\1 – \3', text)
        text = re.sub(r'([a-zA-Z])(–)(\s)', r'\1 –\3', text)
        text = re.sub(r'(\s)(–)([a-zA-Z])', r'\1– \3', text)
        
        # Handle regular hyphens (-) - these should remain connected for compound words
        # Only add spaces if the hyphen is clearly used for punctuation
        # This is more complex as we need to distinguish compound words from punctuation
        
        # Pattern 1: Hyphen used for punctuation (space before and after)
        # Look for patterns like "word - word" or "word- word" or "word -word"
        text = re.sub(r'(\s)(-)(\s)', r' — ', text)  # Convert spaced hyphens to em dashes
        text = re.sub(r'(\s)(-)([a-zA-Z])', r' — \3', text)  # space before, no space after
        text = re.sub(r'([a-zA-Z])(-)(\s)', r'\1 — ', text)  # no space before, space after
        
        # Pattern 2: Hyphen used for compound words (no spaces)
        # These should remain as regular hyphens and stay connected
        # Examples: "grade-schooler", "well-known", "twenty-one"
        
        return text
    
    def convert_first_pdf(self):
        """
        Find and convert the first PDF file in the input directory.
        
        Returns:
            str: Path to the output text file.
        """
        pdf_path = self.find_input_file('.pdf')
        return self.convert_to_text(pdf_path)


class EpubToText(BookToText):
    """
    Concrete class for converting EPUB files to text.
    """
    
    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize EPUB to text converter.
        
        Args:
            input_dir (str): Directory containing EPUB files. If None, uses 'input_book'.
            output_dir (str): Directory for output text files. If None, uses 'text_output'.
        """
        super().__init__(input_dir, output_dir)
    
    def convert_to_text(self, file_path):
        """
        Convert an EPUB file to text.
        
        Args:
            file_path (str): Path to the EPUB file to convert.
            
        Returns:
            str: Path to the output text file.
        """
        output_path = self.get_output_path(file_path)
        
        # Extract text from EPUB
        text_content = self._extract_epub_text(file_path)
        
        # Write the extracted text to output file
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(text_content)
        
        return output_path
    
    def _extract_epub_text(self, file_path):
        """
        Extract text content from an EPUB file.
        
        Args:
            file_path (str): Path to the EPUB file.
            
        Returns:
            str: Extracted text content.
        """
        text_parts = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as epub_zip:
                # Read the container.xml to find the OPF file
                container_xml = epub_zip.read('META-INF/container.xml')
                container_root = ET.fromstring(container_xml)
                
                # Find the OPF file path
                opf_path = None
                for rootfile in container_root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
                    if rootfile.get('media-type') == 'application/oebps-package+xml':
                        opf_path = rootfile.get('full-path')
                        break
                
                if not opf_path:
                    # Fallback: look for .opf files
                    for file_info in epub_zip.filelist:
                        if file_info.filename.endswith('.opf'):
                            opf_path = file_info.filename
                            break
                
                if not opf_path:
                    raise ValueError("Could not find OPF file in EPUB")
                
                # Read the OPF file to get the manifest
                opf_content = epub_zip.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Get the base directory of the OPF file
                opf_dir = os.path.dirname(opf_path) if os.path.dirname(opf_path) else ''
                
                # Find all HTML/XHTML files in the manifest
                html_files = []
                for item in opf_root.findall('.//{http://www.idpf.org/2007/opf}item'):
                    media_type = item.get('media-type', '')
                    href = item.get('href', '')
                    
                    if media_type in ['application/xhtml+xml', 'text/html'] or href.endswith(('.html', '.xhtml')):
                        # Construct full path
                        if opf_dir:
                            full_path = os.path.join(opf_dir, href).replace('\\', '/')
                        else:
                            full_path = href
                        html_files.append(full_path)
                
                # Extract text from each HTML file
                for html_file in html_files:
                    try:
                        html_content = epub_zip.read(html_file)
                        text = self._extract_text_from_html(html_content)
                        if text.strip():
                            text_parts.append(text)
                    except Exception as e:
                        print(f"Warning: Could not extract text from {html_file}: {e}")
                        continue
        
        except Exception as e:
            raise ValueError(f"Error reading EPUB file: {e}")
        
        # Join all text parts with proper spacing
        full_text = '\n\n'.join(text_parts)
        
        # Clean up the text
        full_text = self._clean_epub_text(full_text)
        
        return full_text
    
    def _extract_text_from_html(self, html_content):
        """
        Extract text content from HTML/XHTML content with paragraph detection.
        
        Args:
            html_content (bytes): HTML content as bytes.
            
        Returns:
            str: Extracted text content with proper paragraph spacing.
        """
        try:
            # Parse HTML content
            html_text = html_content.decode('utf-8', errors='ignore')
            
            # Decode HTML entities first
            html_text = self._decode_html_entities(html_text)
            
            # Extract text while preserving paragraph structure
            text = self._extract_text_with_paragraphs(html_text)
            
            return text
            
        except Exception as e:
            print(f"Warning: Error processing HTML content: {e}")
            return ""
    
    def _extract_text_with_paragraphs(self, html_text):
        """
        Extract text from HTML while detecting paragraph boundaries.
        
        Args:
            html_text (str): HTML content as string.
            
        Returns:
            str: Text with proper paragraph spacing.
        """
        # Remove script and style elements
        html_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Handle paragraph tags specifically
        # Replace <p> tags with paragraph markers
        html_text = re.sub(r'<p[^>]*>', '\n\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</p>', '\n\n', html_text, flags=re.IGNORECASE)
        
        # Handle div tags that might contain paragraphs
        html_text = re.sub(r'<div[^>]*class="[^"]*paragraph[^"]*"[^>]*>', '\n\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'<div[^>]*class="[^"]*text[^"]*"[^>]*>', '\n\n', html_text, flags=re.IGNORECASE)
        
        # Handle line breaks
        html_text = re.sub(r'<br[^>]*/?>', '\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</br>', '\n', html_text, flags=re.IGNORECASE)
        
        # Remove all other HTML tags
        html_text = re.sub(r'<[^>]+>', '', html_text)
        
        # Process the text to detect paragraph boundaries
        lines = html_text.split('\n')
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - end current paragraph if it has content
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                continue
            
            # Check for indentation (starts with spaces or tabs)
            if line.startswith((' ', '\t')):
                # Indented line - start new paragraph if current paragraph has content
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                # Remove leading whitespace from indented line
                line = line.lstrip()
            
            # Check if this might be a new paragraph based on content
            # Look for patterns that suggest paragraph breaks
            if (current_paragraph and 
                (line[0].isupper() and 
                 any(current_paragraph[-1].endswith(p) for p in ['.', '!', '?', ':', ';']))):
                # Start new paragraph
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = [line]
            else:
                current_paragraph.append(line)
        
        # Add the last paragraph if it has content
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Join paragraphs with double newlines
        return '\n\n'.join(paragraphs)
    
    def _decode_html_entities(self, text):
        """
        Decode common HTML entities.
        
        Args:
            text (str): Text containing HTML entities.
            
        Returns:
            str: Text with decoded entities.
        """
        # Common HTML entities
        entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' ',
            '&#8211;': '–',  # en dash
            '&#8212;': '—',  # em dash
            '&#8216;': ''',  # left single quotation mark
            '&#8217;': ''',  # right single quotation mark
            '&#8220;': '"',  # left double quotation mark
            '&#8221;': '"',  # right double quotation mark
        }
        
        for entity, char in entities.items():
            text = text.replace(entity, char)
        
        return text
    
    def _clean_epub_text(self, text):
        """
        Clean and format the extracted EPUB text while preserving paragraph structure.
        
        Args:
            text (str): Raw extracted text.
            
        Returns:
            str: Cleaned text with proper paragraph spacing.
        """
        # Split into paragraphs first to preserve structure
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Process dashes within each paragraph
            paragraph = self._process_dashes(paragraph)
            
            # Normalize whitespace within paragraphs (but preserve paragraph breaks)
            paragraph = re.sub(r'[ \t]+', ' ', paragraph)
            paragraph = paragraph.strip()
            
            if paragraph:
                cleaned_paragraphs.append(paragraph)
        
        # Join paragraphs with double newlines (empty line between paragraphs)
        return '\n\n'.join(cleaned_paragraphs)
    
    def _process_dashes(self, text):
        """
        Process different types of dashes to add proper spacing.
        (Reusing the same logic from PDFToText class)
        
        Args:
            text (str): Input text to process.
            
        Returns:
            str: Text with proper dash spacing.
        """
        # Handle em dashes (—) - these should have spaces around them for punctuation
        text = re.sub(r'([a-zA-Z])(—)([a-zA-Z])', r'\1 — \3', text)
        text = re.sub(r'([a-zA-Z])(—)(\s)', r'\1 —\3', text)
        text = re.sub(r'(\s)(—)([a-zA-Z])', r'\1— \3', text)
        
        # Handle en dashes (–) - these are also typically used for punctuation
        text = re.sub(r'([a-zA-Z])(–)([a-zA-Z])', r'\1 – \3', text)
        text = re.sub(r'([a-zA-Z])(–)(\s)', r'\1 –\3', text)
        text = re.sub(r'(\s)(–)([a-zA-Z])', r'\1– \3', text)
        
        # Handle regular hyphens (-) - convert spaced hyphens to em dashes
        text = re.sub(r'(\s)(-)(\s)', r' — ', text)
        text = re.sub(r'(\s)(-)([a-zA-Z])', r' — \3', text)
        text = re.sub(r'([a-zA-Z])(-)(\s)', r'\1 — ', text)
        
        return text
    
    def convert_first_epub(self):
        """
        Find and convert the first EPUB file in the input directory.
        
        Returns:
            str: Path to the output text file.
        """
        epub_path = self.find_input_file('.epub')
        return self.convert_to_text(epub_path)


if __name__ == "__main__":
    """
    Main execution block to convert books to text with automatic format detection.
    """
    import sys
    
    try:
        # Determine the input and output directories
        project_root = os.path.dirname(os.path.abspath(__file__))
        input_dir = os.path.join(project_root, BookToText.DEFAULT_INPUT_FOLDER)
        output_dir = os.path.join(project_root, BookToText.DEFAULT_OUTPUT_FOLDER)
        
        # Look for files with either PDF or EPUB extension
        file_path, extension = BookToText.get_file_by_extensions(input_dir, '.pdf', '.epub')
        
        # Get the appropriate converter for this file type
        converter = BookToText.get_converter_for_file(file_path, input_dir, output_dir)
        
        print(f"Found {extension.upper()} file: {os.path.basename(file_path)}")
        print("Converting to text...")
        
        output_path = converter.convert_to_text(file_path)
        
        print(f"✓ Successfully converted to text!")
        
        # Ask user for the first sentence of the book
        print("\n" + "="*70)
        print("TRIMMING FRONT MATTER")
        print("="*70)
        print("\nBooks often have front matter (cover, table of contents, foreword, etc.)")
        print("before the actual story begins.")
        print("\nPlease enter the FIRST SENTENCE of the actual book content:")
        print("(This will be used to find and remove all text before it)")
        print("-" * 70)
        
        first_sentence = input("> ").strip()
        
        if first_sentence:
            try:
                # Read the generated text file
                with open(output_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                
                # Trim the text
                trimmed_text = BookToText.trim_text_to_first_sentence(full_text, first_sentence)
                
                # Write back the trimmed text
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(trimmed_text)
                
                print("\n✓ Text trimmed successfully!")
                print(f"Removed front matter - text now starts with your specified sentence.")
            except ValueError as trim_error:
                print(f"\n⚠ Warning: {trim_error}")
                print("The text file has been saved without trimming.")
        else:
            print("\nNo input provided. Text saved as-is without trimming.")
        
        print(f"\nFinal output saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please make sure you have a PDF or EPUB file in the 'input_book' directory.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}") 