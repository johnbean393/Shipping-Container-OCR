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
        
        correction_prompt = f"""Please correct the incorrect container IDs.

Containers with invalid IDs found:
{json.dumps(invalid_containers, indent=2)}

Please provide the COMPLETE JSON response again with the following corrections:

1. Examine the image closely and fix any invalid container IDs using proper container ID format (4 letters + 7 digits with valid check digit)
2. Ensure you output at least {original_count} containers (same or more than before)
3. Keep all other data exactly the same, only fix the invalid container IDs
4. Use the following schema:

```json
{json.dumps(schema, indent=2)}
```

Keep the JSON array in the same order as the containers in the image –– left to right, top to bottom.

Return only the corrected JSON array with all containers, with no additional text or formatting."""

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