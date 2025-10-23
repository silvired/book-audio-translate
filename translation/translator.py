import os
import json
import requests
import time
from typing import Optional, Dict, Any, List
from pathlib import Path


class Translator:
    """
    Universal translator that supports multiple translation APIs.
    Automatically selects the appropriate API based on the model name.
    """
    
    # Environment variable names for each provider
    ENV_VAR_MAP = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "alibaba": "DASHSCOPE_API_KEY"  # Primary env var for Alibaba
    }
    
    # Alternative environment variable names for Alibaba
    ALIBABA_ALT_ENV_VARS = ["ALIBABA_API_KEY", "ALIBABA_CLOUD_API_KEY"]
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Initialize the universal translator with a specific model.
        
        Args:
            model_name: Name of the model to use (e.g., "gemini-2.5-flash", "gpt-4o-mini")
            api_key: Optional API key. If not provided, will use environment variables.
        
        Raises:
            ValueError: If model_name is not found in mapping or API key is missing
        """
        self.model_name = model_name
        
        # Initialize token usage tracking attributes
        self.input_tokens = 0
        self.output_tokens = 0
        self.thinking_tokens = 0
        
        # Load model-to-provider mapping
        mapping_path = Path(__file__).parent / "model_api_mapping.json"
        try:
            with open(mapping_path, 'r') as f:
                self.model_mapping = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Mapping file not found at {mapping_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in mapping file: {e}")
        
        # Load translation prompt template
        prompt_path = Path(__file__).parent / "translation_prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            raise ValueError(f"Translation prompt file not found at {prompt_path}")
        
        # Validate model name
        if model_name not in self.model_mapping:
            available_models = ", ".join(self.model_mapping.keys())
            raise ValueError(
                f"Model '{model_name}' not found in mapping. "
                f"Available models: {available_models}"
            )
        
        # Get provider for this model
        self.provider = self.model_mapping[model_name]
        
        # Get API key
        self.api_key = self._get_api_key(api_key)
        
        # Initialize provider-specific configuration
        self._setup_provider()
    
    def _switch_model(self, new_model_name: str):
        """
        Switch the translator to a different model by reconfiguring all settings.
        This allows fallback between different providers without creating new instances.
        
        Args:
            new_model_name: Name of the new model to switch to
        """
        # Validate new model name
        if new_model_name not in self.model_mapping:
            available_models = ", ".join(self.model_mapping.keys())
            raise ValueError(
                f"Model '{new_model_name}' not found in mapping. "
                f"Available models: {available_models}"
            )
        
        # Store original model for potential rollback
        original_model = self.model_name
        original_provider = self.provider
        
        # Update model and provider
        self.model_name = new_model_name
        self.provider = self.model_mapping[new_model_name]
        
        # Get new API key if needed
        self.api_key = self._get_api_key(None)
        
        # Reconfigure provider-specific settings
        self._setup_provider()
        
        return original_model, original_provider
    
    def _get_api_key(self, provided_key: Optional[str]) -> str:
        """
        Get API key from provided parameter or environment variables.
        
        Args:
            provided_key: Optional API key provided by user
            
        Returns:
            API key string
            
        Raises:
            ValueError: If no API key is found
        """
        if provided_key:
            return provided_key
        
        # Get appropriate environment variable
        env_var = self.ENV_VAR_MAP.get(self.provider)
        if not env_var:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Try primary environment variable
        api_key = os.getenv(env_var)
        
        # For Alibaba, try alternative environment variable names
        if not api_key and self.provider == "alibaba":
            for alt_var in self.ALIBABA_ALT_ENV_VARS:
                api_key = os.getenv(alt_var)
                if api_key:
                    break
        
        if not api_key:
            alt_vars = f" or {', '.join(self.ALIBABA_ALT_ENV_VARS)}" if self.provider == "alibaba" else ""
            raise ValueError(
                f"API key not provided for {self.provider}. "
                f"Please set {env_var}{alt_vars} environment variable "
                f"or pass api_key parameter."
            )
        
        return api_key
    
    def _setup_provider(self):
        """Set up provider-specific configuration."""
        if self.provider == "openai":
            self.base_url = "https://api.openai.com/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "gemini":
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
            # Gemini uses API key as URL parameter, not in headers
        elif self.provider == "deepseek":
            self.base_url = "https://api.deepseek.com/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "alibaba":
            self.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    
    def _calculate_response_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate token usage from API response.
        
        Args:
            response_data: The response data from the API
            
        Returns:
            Dictionary with token counts
        """
        if self.provider == "gemini":
            # Gemini uses different field names
            usage_metadata = response_data.get('usageMetadata', {})
            return {
                'prompt_tokens': usage_metadata.get('promptTokenCount', 0),
                'completion_tokens': usage_metadata.get('candidatesTokenCount', 0),
                'thoughts_tokens': usage_metadata.get('thoughtsTokenCount', 0),
                'total_tokens': usage_metadata.get('totalTokenCount', 0)
            }
        elif self.provider == "deepseek":
            # DeepSeek uses standard format with additional reasoning_tokens in completion_tokens_details
            usage = response_data.get('usage', {})
            completion_details = usage.get('completion_tokens_details', {})
            return {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'reasoning_tokens': completion_details.get('reasoning_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        else:
            # OpenAI and Alibaba use standard usage format
            usage = response_data.get('usage', {})
            return {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
    
    def _format_prompt(self, text: str, target_language: str, source_language: str) -> str:
        """
        Format the translation prompt using the loaded template.
        
        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language
            
        Returns:
            Formatted prompt string
        """
        # Format the prompt template with the provided values
        prompt = self.prompt_template.format(
            source_language=source_language,
            target_language=target_language,
            text=text
        )
        
        # Add provider-specific additions
        if self.provider == "gemini":
            # Insert the Gemini-specific note after the main instructions
            lines = prompt.split('\n')
            # Find the line before "Text to translate:"
            for i, line in enumerate(lines):
                if "Text to translate:" in line:
                    lines.insert(i, "Do not use google search to perform the translation.")
                    break
            prompt = '\n'.join(lines)
        
        return prompt
    
    def _translate_openai(self, text: str, target_language: str, 
                          source_language: str) -> Dict[str, Any]:
        """Translate using OpenAI API."""
        prompt = self._format_prompt(text, target_language, source_language)
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        actual_tokens = self._calculate_response_tokens(result)
        
        # Store token usage
        self.input_tokens += actual_tokens.get('prompt_tokens', 0)
        self.output_tokens += actual_tokens.get('completion_tokens', 0)
        
        if 'choices' in result and len(result['choices']) > 0:
            translated_text = result['choices'][0]['message']['content'].strip()
            return {
                "success": True,
                "translated_text": translated_text,
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "error": "No translation found in API response",
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
    
    def _translate_gemini(self, text: str, target_language: str, 
                          source_language: str, thinking_budget: Optional[int] = None) -> Dict[str, Any]:
        """
        Translate using Gemini API.
        
        Args:
            text: Text to translate
            target_language: Target language for translation
            source_language: Source language of the text
            thinking_budget: Optional thinking budget parameter for Gemini models that support extended thinking
        """
        prompt = self._format_prompt(text, target_language, source_language)
        
        # Build generation config
        # For translation, output is typically similar size to input, so we need a high limit
        generation_config = {
            "temperature": 0.3,
            "maxOutputTokens": 45000  # Increased to handle larger translations
        }
        
        # Add thinking config if provided
        # - thinking_budget = 0: Explicitly disable thinking (thinkingBudget: 0)
        # - thinking_budget = -1: Unlimited thinking (omit thinkingBudget field)
        # - thinking_budget > 0: Specific budget (thinkingBudget: value)
        # - thinking_budget = None: Let model decide (omit thinkingConfig entirely)
        if thinking_budget is not None:
            if thinking_budget == -1:
                # For unlimited thinking, include thinkingConfig but omit thinkingBudget
                generation_config["thinkingConfig"] = {}
            else:
                # For specific budget (including 0 to disable), set thinkingBudget
                generation_config["thinkingConfig"] = {
                    "thinkingBudget": thinking_budget
                }
        
        # Configure safety settings to allow literary content
        # This prevents false positives on legitimate book translations
        # Using BLOCK_NONE to disable filtering for translation tasks
        safety_settings = [
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": generation_config,
            "safetySettings": safety_settings
        }
        
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=1000
        )
        response.raise_for_status()
        result = response.json()
        
        actual_tokens = self._calculate_response_tokens(result)
        
        # Store token usage
        self.input_tokens += actual_tokens.get('prompt_tokens', 0)
        self.output_tokens += actual_tokens.get('completion_tokens', 0)
        self.thinking_tokens += actual_tokens.get('thoughts_tokens', 0)
        
        # Check for content blocking by safety filters
        if 'promptFeedback' in result and 'blockReason' in result['promptFeedback']:
            block_reason = result['promptFeedback']['blockReason']
            safety_ratings = result['promptFeedback'].get('safetyRatings', [])
            
            print(f"  ⚠ Gemini blocked content ({block_reason}), falling back to DeepSeek...")
            
            # Fallback to DeepSeek for blocked content
            try:
                # Switch to DeepSeek model
                original_model, original_provider = self._switch_model("deepseek-chat")
                
                # Translate with DeepSeek
                fallback_result = self._translate_deepseek(text, target_language, source_language)
                
                # Switch back to original model
                self._switch_model(original_model)
                
                if fallback_result['success']:
                    # Add fallback metadata
                    fallback_result.update({
                        "fallback_used": True,
                        "original_provider": original_provider,
                        "fallback_provider": "deepseek",
                        "block_reason": block_reason,
                        "gemini_tokens": actual_tokens
                    })
                    print(f"  ✓ DeepSeek fallback successful!")
                    return fallback_result
                else:
                    # Both failed
                    return {
                        "success": False,
                        "error": f"Gemini blocked content ({block_reason}) and DeepSeek fallback failed: {fallback_result.get('error', 'Unknown error')}",
                        "actual_tokens": actual_tokens,
                        "raw_response": result,
                        "blocked": True,
                        "block_reason": block_reason,
                        "fallback_failed": True
                    }
            except Exception as e:
                # Try to switch back to original model even if fallback failed
                try:
                    self._switch_model(original_model)
                except:
                    pass
                return {
                    "success": False,
                    "error": f"Gemini blocked content ({block_reason}) and DeepSeek fallback failed with exception: {str(e)}",
                    "actual_tokens": actual_tokens,
                    "raw_response": result,
                    "blocked": True,
                    "block_reason": block_reason,
                    "fallback_exception": str(e)
                }
        
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            
            # Check for finish reason / blocking
            finish_reason = candidate.get('finishReason', 'UNKNOWN')
            
            if 'content' in candidate:
                if 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    
                    if len(parts) > 0:
                        first_part = parts[0]
                        
                        if 'text' in first_part:
                            text = first_part['text'].strip()
                            
                            # Check if this is a complete response
                            is_complete = finish_reason == 'STOP'
                            
                            return {
                                "success": True,
                                "translated_text": text,
                                "actual_tokens": actual_tokens,
                                "raw_response": result,
                                "is_complete": is_complete,
                                "finish_reason": finish_reason
                            }
        
        return {
            "success": False,
            "error": "No translation found in API response",
            "actual_tokens": actual_tokens,
            "raw_response": result
        }
    
    def _translate_deepseek(self, text: str, target_language: str, 
                            source_language: str) -> Dict[str, Any]:
        """Translate using DeepSeek API."""
        prompt = self._format_prompt(text, target_language, source_language)
        
        # Use the specified DeepSeek model (e.g., deepseek-chat or deepseek-reasoner)
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        actual_tokens = self._calculate_response_tokens(result)
        
        # Store token usage
        self.input_tokens += actual_tokens.get('prompt_tokens', 0)
        self.output_tokens += actual_tokens.get('completion_tokens', 0)
        self.thinking_tokens += actual_tokens.get('reasoning_tokens', 0)
        
        if 'choices' in result and len(result['choices']) > 0:
            translated_text = result['choices'][0]['message']['content'].strip()
            
            return {
                "success": True,
                "translated_text": translated_text,
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "error": "No translation found in API response",
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
    
    def _translate_alibaba(self, text: str, target_language: str, 
                           source_language: str) -> Dict[str, Any]:
        """Translate using Alibaba Cloud Qwen API."""
        prompt = self._format_prompt(text, target_language, source_language)
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        actual_tokens = self._calculate_response_tokens(result)
        
        # Store token usage
        self.input_tokens += actual_tokens.get('prompt_tokens', 0)
        self.output_tokens += actual_tokens.get('completion_tokens', 0)
        
        if 'choices' in result and len(result['choices']) > 0:
            translated_text = result['choices'][0]['message']['content'].strip()
            return {
                "success": True,
                "translated_text": translated_text,
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "error": "No translation found in API response",
                "actual_tokens": actual_tokens,
                "raw_response": result
            }
    
    def print_token_usage_summary(self) -> None:
        """
        Print a summary of the accumulated token usage across all translations.
        """
        print("\n" + "="*80)
        print("CUMULATIVE TOKEN USAGE SUMMARY")
        print("="*80)
        print(f"  Input Tokens:            {self.input_tokens:,}")
        print(f"  Output Tokens:           {self.output_tokens:,}")
        print(f"  Thinking Tokens:         {self.thinking_tokens:,}")
        print(f"  Total Tokens:            {self.input_tokens + self.output_tokens + self.thinking_tokens:,}")
        print("="*80 + "\n")
    
    def translate_text(self, text: str, target_language: str = "Italian", 
                      source_language: str = "English", thinking_budget: Optional[int] = None) -> Dict[str, Any]:
        """
        Translate text using the configured model.
        
        Args:
            text: Text to translate
            target_language: Target language for translation
            source_language: Source language of the text
            thinking_budget: Optional thinking budget parameter for Gemini models (ignored for other providers)
            
        Returns:
            Dictionary containing translation result and metadata
        """
        try:
            # Route to appropriate provider method
            if self.provider == "openai":
                result = self._translate_openai(text, target_language, source_language)
            elif self.provider == "gemini":
                result = self._translate_gemini(text, target_language, source_language, thinking_budget)
            elif self.provider == "deepseek":
                result = self._translate_deepseek(text, target_language, source_language)
            elif self.provider == "alibaba":
                result = self._translate_alibaba(text, target_language, source_language)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}",
                    "original_text": text
                }
            
            # Add common metadata
            result.update({
                "original_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "model_used": self.model_name,
                "provider": self.provider,
                "tokens_used": result.get("actual_tokens", {}).get("total_tokens", 0)
            })
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', '')}"
                    elif 'message' in error_data:
                        error_msg += f" - {error_data['message']}"
            except:
                pass
            return {
                "success": False,
                "error": error_msg,
                "original_text": text,
                "model_used": self.model_name,
                "provider": self.provider
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse API response: {str(e)}",
                "original_text": text,
                "model_used": self.model_name,
                "provider": self.provider
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "original_text": text,
                "model_used": self.model_name,
                "provider": self.provider
            }