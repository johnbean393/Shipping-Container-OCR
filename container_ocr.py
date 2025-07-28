"""
Container OCR class for extracting shipping container information from images.
"""

import json
from typing import Dict, Any

from openai import OpenAI
from config import OPENROUTER_BASE_URL, MAX_TOKENS, TEMPERATURE, SCHEMA_FILE
from utils import encode_image, validate_image, load_schema, clean_response_content
from container_validator import validate_container_id, clean_container_id


class ContainerOCR:
    """OCR class for extracting container information from images."""

    def __init__(self, model: str, api_key: str):
        """Initialize the OCR client with OpenRouter API key."""
        # Initialize the OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL
        )

        # Set the model
        self.model = model

        # Load the schema from external file
        self.schema = load_schema(SCHEMA_FILE)

    def create_prompt(self) -> str:
        """Create the prompt for container OCR."""
        return f"""Extract all the text from each container in the image.

Output the information on each container as a structured JSON object according to the schema below.

```json
{json.dumps(self.schema, indent=2)}
```

Focus on:
1. Container IDs (e.g., CMCU 455 7748)
2. Carrier names (e.g., CROWLEY)
3. Container types (e.g., LPG1)
4. Dimensions (length and height)
5. Weight specifications (M.G.W, TARE, NET)
6. Cubic capacity (CUB.CAP)
7. Any additional markings

Return only the JSON array, no additional text or formatting."""

    def extract_container_data(self, image_path: str) -> Dict[str, Any]:
        """Extract container data from image using Gemini."""
        try:
            # Validate image
            validate_image(image_path)
            
            # Encode image
            base64_image = encode_image(image_path)
            
            # Create prompt
            prompt = self.create_prompt()
            
            # Make API call
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
            
            # Extract and parse response
            content = response.choices[0].message.content
            
            # Clean up response (remove markdown formatting if present)
            content = clean_response_content(content)
            
            # Parse JSON
            try:
                result = json.loads(content)
                # Clean and normalize container IDs
                for container in result:
                    if 'container_id' in container:
                        # Clean the container ID by removing non-alphanumeric characters and converting to uppercase
                        original_id = container['container_id']
                        cleaned_id = clean_container_id(original_id)
                        container['container_id'] = cleaned_id
                
                # Validate container IDs
                for index, container in enumerate(result):
                    container_id = container.get('container_id', 'Unknown')
                    if container_id != 'Unknown' and not validate_container_id(container_id):
                        print(f"Invalid container ID: {container_id} at index {index}")
                
                return result
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON response: {e}\nResponse: {content}")
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {e}") 