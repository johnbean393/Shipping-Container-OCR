"""
LLM Client for handling OpenAI/OpenRouter API interactions.
"""

import json
from typing import Dict, Any

from openai import OpenAI
from config import OPENROUTER_BASE_URL, MAX_TOKENS, TEMPERATURE
from utils import clean_response_content


class LLMClient:
    """Client for handling LLM API interactions."""

    def __init__(self, model: str, api_key: str):
        """Initialize the LLM client with OpenRouter API key."""
        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL
        )
        self.model = model

    def extract_text_from_image(self, prompt: str, base64_image: str) -> str:
        """
        Extract text from image using the LLM.
        
        Args:
            prompt: The text prompt for the LLM
            base64_image: Base64 encoded image data
            
        Returns:
            The LLM's response content
            
        Raises:
            Exception: If the API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            # Extract and clean response
            content = response.choices[0].message.content
            return clean_response_content(content)
            
        except Exception as e:
            raise Exception(f"LLM API call failed: {e}")

    def parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        
        Args:
            content: The response content from the LLM
            
        Returns:
            Parsed JSON data
            
        Raises:
            Exception: If JSON parsing fails
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}\nResponse: {content}")

    def correct_container_data(self, chat_history: list, invalid_containers: list, original_count: int, schema: dict) -> str:
        """
        Request corrections for invalid container IDs using chat history.
        
        Args:
            chat_history: List of previous messages in the conversation
            invalid_containers: List of full container objects with invalid IDs that need correction
            original_count: Original number of containers detected
            schema: JSON schema for validation
            
        Returns:
            The LLM's corrected response content
            
        Raises:
            Exception: If the API call fails
        """
        
        # Extract just the invalid container IDs for clearer messaging
        invalid_ids = [container.get('container_id', 'Unknown') for container in invalid_containers]
        
        correction_prompt = f"""IMPORTANT: Only correct the INVALID container IDs listed below. Do NOT change any container IDs that are already correct.

The following {len(invalid_ids)} container IDs are INVALID and need correction:
{', '.join(invalid_ids)}

Requirements for correction:
1. Look at the image again and ONLY fix the invalid container IDs listed above
2. Keep ALL other valid container IDs exactly as they were in your previous response
3. Maintain the exact same number of containers ({original_count}) and the same order
4. Only change the invalid container IDs to match what you actually see in the image
5. Use proper container ID format: 4 letters + 7 digits with valid check digit

Container ID format rules:
- 4 letters (owner code) + 7 digits 
- The 7th digit is a check digit calculated from the first 10 characters
- Example: ABCD1234567 (where 7 is the check digit)

Please provide the COMPLETE JSON response with ONLY the invalid IDs corrected.

Return only the corrected JSON array with all containers, maintaining the same order as before."""

        try:
            # Build messages including chat history
            messages = chat_history.copy()
            messages.append({
                "role": "user",
                "content": correction_prompt
            })
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            # Extract and clean response
            content = response.choices[0].message.content
            return clean_response_content(content)
            
        except Exception as e:
            raise Exception(f"LLM correction API call failed: {e}") 