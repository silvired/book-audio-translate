"""
ChunkMapper class for splitting paragraphs into chunks based on token limits.
"""

import json
from typing import Dict, List, Union


class ChunkMapper:
    """
    A class to map paragraphs into chunks based on token count limits.
    
    Attributes:
        max_output_token (int): Maximum number of output tokens allowed.
        output_input_token_ratio (float): Ratio between output and input tokens.
    """
    
    def __init__(self, max_output_token: int, output_input_token_ratio: float):
        """
        Initialize the ChunkMapper.
        
        Args:
            max_output_token (int): Maximum number of output tokens allowed.
            output_input_token_ratio (float): Ratio between output and input tokens.
        """
        self.max_output_token = max_output_token
        self.output_input_token_ratio = output_input_token_ratio
    
    def calculate_max_input_token(self) -> int:
        """
        Calculate the maximum number of input tokens allowed.
        
        Given the ratio between output and input tokens and the maximum output token,
        this method calculates the maximum number of input tokens and applies an 80%
        buffer to ensure safe operation.
        
        Returns:
            int: Maximum number of input tokens allowed (reduced to 80% for buffer).
        """
        # Calculate max input tokens based on the ratio
        max_input_token = self.max_output_token / self.output_input_token_ratio
        
        # Apply 80% buffer
        max_input_token_with_buffer = int(max_input_token * 0.8)
        
        return max_input_token_with_buffer
    
    def map_chunk_paragraphs(self, paragraphs_data: Union[List[Dict], str]) -> Dict[str, List]:
        """
        Map paragraphs into chunks based on token count limits.
        
        Args:
            paragraphs_data (Union[List[Dict], str]): Either a list of dictionaries or a JSON string.
                Each entry should have:
                - paragraph_id: Identifier for the paragraph
                - sentences: The sentences in the paragraph
                - token_count: Number of tokens in the paragraph
        
        Returns:
            Dict[str, List]: Dictionary mapping chunk names to lists of paragraph IDs.
                Example: {"chunk1": [1, 2], "chunk2": [3, 4]}
        """
        # Parse JSON if string is provided
        if isinstance(paragraphs_data, str):
            paragraphs_data = json.loads(paragraphs_data)
        
        # Get the maximum input tokens allowed
        max_input_token = self.calculate_max_input_token()
        
        # Initialize result dictionary and tracking variables
        chunks = {}
        current_chunk_id = 1
        current_chunk_paragraphs = []
        current_chunk_token_count = 0
        
        # Iterate through paragraphs and group them into chunks
        for paragraph in paragraphs_data:
            paragraph_id = paragraph['paragraph_id']
            token_count = paragraph['token_count']
            
            # Check if adding this paragraph would exceed the limit
            if current_chunk_token_count + token_count < max_input_token:
                # Add to current chunk
                current_chunk_paragraphs.append(paragraph_id)
                current_chunk_token_count += token_count
            else:
                # Save current chunk if it has paragraphs
                if current_chunk_paragraphs:
                    chunks[f"chunk{current_chunk_id}"] = current_chunk_paragraphs
                    current_chunk_id += 1
                
                # Start new chunk with current paragraph
                current_chunk_paragraphs = [paragraph_id]
                current_chunk_token_count = token_count
        
        # Don't forget to add the last chunk
        if current_chunk_paragraphs:
            chunks[f"chunk{current_chunk_id}"] = current_chunk_paragraphs
        
        return chunks

