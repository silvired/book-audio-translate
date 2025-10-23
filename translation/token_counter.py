import requests
import json
from typing import Optional, Dict, List


class TokenCounter:
    """
    Token counter for different AI model providers.
    Provides accurate token counting for Gemini and DeepSeek models,
    and tiktoken-based estimation for other models.
    """
    
    def __init__(self, model_name: str, provider: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the token counter.
        
        Args:
            model_name: Name of the model (e.g., "gemini-2.5-flash", "deepseek-chat")
            provider: Provider name ("gemini", "deepseek", "openai", "alibaba")
            api_key: Optional API key (required for Gemini)
            base_url: Optional base URL (required for Gemini)
        """
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens for the given text using provider-specific methods.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Token count (accurate for Gemini/DeepSeek, estimated using tiktoken for others)
        """
        if self.provider == "gemini":
            return self.count_tokens_gemini(text)
        elif self.provider == "deepseek":
            return self.count_tokens_deepseek(text)
        else:
            # Fallback to tiktoken-based estimation for all other providers
            return self._estimate_tokens_tiktoken(text)
    
    def count_tokens_gemini(self, text: str) -> int:
        """
        Count tokens using Gemini's official countTokens API.
        This provides accurate token counts matching actual API usage.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Actual token count from Gemini API
        """
        if not self.api_key or not self.base_url:
            print("Warning: API key or base URL not provided for Gemini. Using tiktoken estimation.")
            return self._estimate_tokens_tiktoken(text)
        
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": text}]
                }]
            }
            
            url = f"{self.base_url}/{self.model_name}:countTokens?key={self.api_key}"
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract token count from response
            token_count = result.get('totalTokens', 0)
            return token_count
            
        except Exception as e:
            print(f"Warning: Failed to count tokens with Gemini API: {e}")
            print("Falling back to tiktoken estimation...")
            return self._estimate_tokens_tiktoken(text)
    
    def count_tokens_deepseek(self, text: str) -> int:
        """
        Count tokens using DeepSeek's tokenizer.
        DeepSeek uses the same tokenizer as OpenAI (tiktoken), so we can use that for accurate counting.
        
        Args:
            text: Input text to count tokens for
            
        Returns:
            Token count using tiktoken
        """
        return self._estimate_tokens_tiktoken(text)
    
    def _estimate_tokens_tiktoken(self, text: str) -> int:
        """
        General token estimation using tiktoken.
        This is used as a fallback for all models that don't have provider-specific counting.
        
        Args:
            text: Input text to estimate tokens for
            
        Returns:
            Token count using tiktoken (cl100k_base encoding)
        
        Raises:
            ImportError: If tiktoken is not installed
            Exception: If token counting fails for any other reason
        """
        try:
            import tiktoken
            
            # Use cl100k_base tokenizer as general estimator
            encoding = tiktoken.get_encoding("cl100k_base")
            token_count = len(encoding.encode(text))
            return token_count
            
        except ImportError:
            raise ImportError("tiktoken not installed. Install with: pip install tiktoken")
        except Exception as e:
            raise Exception(f"Failed to count tokens with tiktoken: {e}")
    
    def count_tokens_for_segmented_file(self, file_path: str, output_file_path: Optional[str] = None) -> Dict[str, any]:
        """
        Count tokens for each paragraph in a segmented JSON file.
        
        Args:
            file_path: Path to the segmented JSON file containing paragraphs with sentences
            output_file_path: Optional path to save the output JSON file with token counts.
                            If not provided, will auto-generate based on input file name.
            
        Returns:
            Dictionary containing the token count information for each paragraph
        """
        # Read the segmented JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            paragraphs = json.load(f)
        
        # Create result structure
        result = {
            "model_name": self.model_name,
            "provider": self.provider,
            "source_file": file_path,
            "paragraphs": []
        }
        
        total_input_tokens = 0
        
        # Process each paragraph
        for para in paragraphs:
            par_id = para.get("par_id")
            sentences = para.get("sentences", [])
            
            # Combine all sentences in the paragraph
            paragraph_text = " ".join(sentences)
            
            # Count tokens for this paragraph
            token_count = self.count_tokens(paragraph_text)
            total_input_tokens += token_count
            
            # Add to result
            result["paragraphs"].append({
                "par_id": par_id,
                "token_count": token_count,
                "text": paragraph_text
            })
        
        # Add summary statistics
        result["total_input_tokens"] = total_input_tokens
        result["total_paragraphs"] = len(paragraphs)
        result["average_tokens_per_paragraph"] = total_input_tokens / len(paragraphs) if paragraphs else 0
        
        # Save to file if output path provided or generate one
        if output_file_path is None:
            # Auto-generate output file name
            import os
            base_name = os.path.splitext(file_path)[0]
            output_file_path = f"{base_name}_token_counts_{self.provider}.json"
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Token counts saved to: {output_file_path}")
        print(f"Total tokens: {total_input_tokens}")
        print(f"Total paragraphs: {len(paragraphs)}")
        print(f"Average tokens per paragraph: {result['average_tokens_per_paragraph']:.2f}")
        
        return result
    
    def count_tokens_for_prompt(self, prompt_file_path: str, source_language: str, target_language: str) -> Dict[str, any]:
        """
        Count tokens for a translation prompt template.
        
        Args:
            prompt_file_path: Path to the prompt template file
            source_language: Source language to substitute in the prompt
            target_language: Target language to substitute in the prompt
            
        Returns:
            Dictionary containing the processed prompt and token count
        """
        # Read the prompt file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        
        # Substitute language placeholders
        prompt_text = prompt_text.replace("{source_language}", source_language)
        prompt_text = prompt_text.replace("{target_language}", target_language)
        
        # Remove lines containing {text}
        lines = prompt_text.split('\n')
        filtered_lines = [line for line in lines if '{text}' not in line]
        prompt_text = '\n'.join(filtered_lines)
        
        # Add Google search note for Gemini
        if self.provider == "gemini":
            prompt_text += "\nDo not use google search to perform the translation."
        
        # Count tokens
        token_count = self.count_tokens(prompt_text)
        
        result = {
            "model_name": self.model_name,
            "provider": self.provider,
            "source_language": source_language,
            "target_language": target_language,
            "prompt_file": prompt_file_path,
            "processed_prompt": prompt_text,
            "token_count": token_count
        }
        
        return result
    
    def count_chunk_input_tokens(self, segmented_tokens_data: Dict, prompt_tokens_data: Dict, chunk_mapping: Dict) -> Dict:
        """
        Count total input tokens for each chunk including paragraphs and prompt.
        
        Args:
            segmented_tokens_data: Output from count_tokens_for_segmented_file containing
                                  paragraph token counts
            prompt_tokens_data: Output from count_tokens_for_prompt containing prompt token count
            chunk_mapping: Output from ChunkMapper's map_chunk_paragraphs method mapping
                         chunk names to paragraph IDs
            
        Returns:
            Dictionary with chunk information including total input tokens for each chunk.
            Structure: {
                "chunk1": {
                    "paragraph_ids": [0, 1, 2, ...],
                    "paragraph_count": 28,
                    "paragraph_tokens": 2231,
                    "prompt_tokens": 123,
                    "tot_input_tokens": 2354
                },
                ...
            }
        """
        # Create a lookup dictionary for paragraph token counts
        paragraph_tokens = {}
        for para in segmented_tokens_data.get("paragraphs", []):
            par_id = para.get("par_id")
            token_count = para.get("token_count")
            paragraph_tokens[par_id] = token_count
        
        # Get the prompt token count
        prompt_token_count = prompt_tokens_data.get("token_count", 0)
        
        # Build result dictionary with chunk details and total input tokens
        result = {}
        
        for chunk_name, paragraph_ids in chunk_mapping.items():
            # Sum up tokens for all paragraphs in this chunk
            chunk_paragraph_tokens = sum(
                paragraph_tokens.get(par_id, 0) for par_id in paragraph_ids
            )
            
            # Calculate total input tokens (paragraphs + prompt)
            total_input_tokens = chunk_paragraph_tokens + prompt_token_count
            
            # Add chunk information to result
            result[chunk_name] = {
                "paragraph_ids": paragraph_ids,
                "paragraph_count": len(paragraph_ids),
                "paragraph_tokens": chunk_paragraph_tokens,
                "prompt_tokens": prompt_token_count,
                "tot_input_tokens": total_input_tokens
            }
        
        return result

    def estimate_output_thinking_tokens(
        self, 
        chunk_input_tokens_data: Dict, 
        output_input_ratio: float, 
        thinking_input_ratio: Optional[float] = None
    ) -> Dict:
        """
        Estimate output and optionally thinking tokens for each chunk based on input/output ratios.
        
        Args:
            chunk_input_tokens_data: Output from count_chunk_input_tokens containing
                                    chunk information with total input tokens
            output_input_ratio: Ratio of output tokens to input tokens (output/input)
            thinking_input_ratio: Optional ratio of thinking tokens to input tokens (thinking/input)
            
        Returns:
            Dictionary with same structure as input but with additional keys:
            - tot_output_tokens: estimated output tokens for each chunk
            - tot_thinking_tokens: estimated thinking tokens for each chunk (if thinking_input_ratio provided)
            
            Example output structure:
            {
                "chunk1": {
                    "paragraph_ids": [0, 1, 2, ...],
                    "paragraph_count": 28,
                    "paragraph_tokens": 2231,
                    "prompt_tokens": 123,
                    "tot_input_tokens": 2354,
                    "tot_output_tokens": 4708,  # if output_input_ratio = 2.0
                    "tot_thinking_tokens": 1177  # if thinking_input_ratio = 0.5
                },
                ...
            }
        """
        # Create a deep copy of the input data to avoid modifying the original
        import copy
        result = copy.deepcopy(chunk_input_tokens_data)
        
        # Calculate output and thinking tokens for each chunk
        for chunk_name, chunk_data in result.items():
            tot_input_tokens = chunk_data.get("tot_input_tokens", 0)
            
            # Calculate total output tokens based on the ratio
            tot_output_tokens = int(tot_input_tokens * output_input_ratio)
            chunk_data["tot_output_tokens"] = tot_output_tokens
            
            # If thinking ratio is provided, calculate thinking tokens
            if thinking_input_ratio is not None:
                tot_thinking_tokens = int(tot_input_tokens * thinking_input_ratio)
                chunk_data["tot_thinking_tokens"] = tot_thinking_tokens
        
        return result

    def estimate_total_tokens(self, chunk_tokens_data: Dict) -> Dict[str, int]:
        """
        Sum up total input, output, and thinking tokens across all chunks.
        
        Args:
            chunk_tokens_data: Output from estimate_output_thinking_tokens containing
                             chunk information with token counts
            
        Returns:
            Dictionary with total token counts:
            {
                "input": 13000,
                "output": 17000,
                "thinking": 15000  # only present if thinking tokens were estimated
            }
        """
        total_input = 0
        total_output = 0
        total_thinking = 0
        has_thinking = False
        
        # Sum up tokens from all chunks
        for chunk_name, chunk_data in chunk_tokens_data.items():
            total_input += chunk_data.get("tot_input_tokens", 0)
            total_output += chunk_data.get("tot_output_tokens", 0)
            
            # Check if thinking tokens are present
            if "tot_thinking_tokens" in chunk_data:
                total_thinking += chunk_data.get("tot_thinking_tokens", 0)
                has_thinking = True
        
        # Build result dictionary
        result = {
            "input": total_input,
            "output": total_output
        }
        
        # Only include thinking if it was present in the data
        if has_thinking:
            result["thinking"] = total_thinking
        
        return result

    def estimate_complete_pipeline(
        self,
        segmented_file_path: str,
        prompt_file_path: str,
        chunk_mapping: Dict,
        source_language: str,
        target_language: str,
        output_input_ratio: float,
        thinking_input_ratio: Optional[float] = None,
        save_intermediate: bool = False
    ) -> Dict:
        """
        Convenience method that runs the complete token estimation pipeline.
        This chains together all the individual steps for common use cases.
        
        Args:
            segmented_file_path: Path to the segmented JSON file
            prompt_file_path: Path to the prompt template file
            chunk_mapping: Chunk-to-paragraph mapping dictionary
            source_language: Source language for translation
            target_language: Target language for translation
            output_input_ratio: Ratio of output tokens to input tokens
            thinking_input_ratio: Optional ratio of thinking tokens to input tokens
            save_intermediate: Whether to save intermediate token count files
            
        Returns:
            Dictionary containing complete token estimation:
            {
                "segmented_tokens": {...},
                "prompt_tokens": {...},
                "chunk_input_tokens": {...},
                "chunk_tokens_with_estimates": {...},
                "total_tokens": {"input": 13000, "output": 17000, ...}
            }
        """
        # Step 1: Count tokens for segmented file
        print("Step 1: Counting tokens for segmented file...")
        segmented_tokens = self.count_tokens_for_segmented_file(
            file_path=segmented_file_path,
            output_file_path=None if save_intermediate else None
        )
        
        # Step 2: Count tokens for prompt
        print("Step 2: Counting tokens for prompt...")
        prompt_tokens = self.count_tokens_for_prompt(
            prompt_file_path=prompt_file_path,
            source_language=source_language,
            target_language=target_language
        )
        
        # Step 3: Count chunk input tokens
        print("Step 3: Calculating chunk input tokens...")
        chunk_input_tokens = self.count_chunk_input_tokens(
            segmented_tokens_data=segmented_tokens,
            prompt_tokens_data=prompt_tokens,
            chunk_mapping=chunk_mapping
        )
        
        # Step 4: Estimate output and thinking tokens
        print("Step 4: Estimating output and thinking tokens...")
        chunk_tokens_with_estimates = self.estimate_output_thinking_tokens(
            chunk_input_tokens_data=chunk_input_tokens,
            output_input_ratio=output_input_ratio,
            thinking_input_ratio=thinking_input_ratio
        )
        
        # Step 5: Calculate total tokens
        print("Step 5: Calculating total tokens...")
        total_tokens = self.estimate_total_tokens(
            chunk_tokens_data=chunk_tokens_with_estimates
        )
        
        # Build complete result
        result = {
            "model_name": self.model_name,
            "provider": self.provider,
            "segmented_tokens": segmented_tokens,
            "prompt_tokens": prompt_tokens,
            "chunk_input_tokens": chunk_input_tokens,
            "chunk_tokens_with_estimates": chunk_tokens_with_estimates,
            "total_tokens": total_tokens
        }
        
        print(f"\n=== Pipeline Complete ===")
        print(f"Total Input Tokens: {total_tokens['input']:,}")
        print(f"Total Output Tokens: {total_tokens['output']:,}")
        if 'thinking' in total_tokens:
            print(f"Total Thinking Tokens: {total_tokens['thinking']:,}")
        
        return result


