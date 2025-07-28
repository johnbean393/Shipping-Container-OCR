"""
Container OCR class for extracting shipping container information from images.
"""

import json
from typing import Dict, Any

from config import SCHEMA_FILE
from utils import encode_image, validate_image, load_schema
from container_validator import validate_container_id, clean_container_id
from llm_client import LLMClient


class ContainerOCR:
    """OCR class for extracting container information from images."""

    def __init__(self, model: str, api_key: str):
        """Initialize the OCR client with OpenRouter API key."""
        # Initialize the LLM client
        self.llm_client = LLMClient(model, api_key)

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

The JSON array should be in the same order as the containers in the image –– left to right, top to bottom.

Return only the JSON array, no additional text or formatting."""

    def extract_container_data(self, image_path: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Extract container data from image using LLM with validation and correction loop."""
        try:
            # Validate image
            validate_image(image_path)
            
            # Encode image
            base64_image = encode_image(image_path)
            
            # Create initial prompt
            prompt = self.create_prompt()
            
            # Initialize chat history
            chat_history = [
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
            ]
            
            result = None
            iteration = 0
            
            while iteration < max_iterations:
                try:
                    if iteration == 0:
                        # Initial extraction
                        print(f"Attempt {iteration + 1}: Initial container data extraction...")
                        content = self.llm_client.extract_text_from_image(prompt, base64_image)
                        
                        # Add LLM response to chat history
                        chat_history.append({
                            "role": "assistant",
                            "content": content
                        })
                    else:
                        # Correction attempt
                        print(f"Attempt {iteration + 1}: Requesting corrections for invalid container IDs...")
                        content = self.llm_client.correct_container_data(
                            chat_history, invalid_containers, original_count, self.schema
                        )
                        
                        # Add correction response to chat history
                        chat_history.append({
                            "role": "assistant", 
                            "content": content
                        })
                    
                    # Parse JSON response
                    result = self.llm_client.parse_json_response(content)
                    
                    # Store original count for validation
                    if iteration == 0:
                        original_count = len(result) if isinstance(result, list) else 0
                    
                    # Clean and normalize container IDs
                    for container in result:
                        if 'container_id' in container:
                            original_id = container['container_id']
                            cleaned_id = clean_container_id(original_id)
                            container['container_id'] = cleaned_id
                    
                    # Validate container IDs and collect invalid ones
                    invalid_containers = []
                    validation_errors = []
                    
                    for index, container in enumerate(result):
                        container_id = container.get('container_id', 'Unknown')
                        if container_id != 'Unknown' and not validate_container_id(container_id):
                            invalid_containers.append(container)
                            validation_errors.append(f"Invalid container ID: {container_id} at index {index}")
                    
                    # Check if container count decreased
                    current_count = len(result) if isinstance(result, list) else 0
                    if iteration > 0 and current_count < original_count:
                        error_msg = f"Container count decreased from {original_count} to {current_count}"
                        validation_errors.append(error_msg)
                        print(f"Warning: {error_msg}")
                    
                    # If no validation errors, we're done
                    if not invalid_containers and current_count >= original_count:
                        if iteration > 0:
                            print(f"✓ Successfully corrected container IDs after {iteration + 1} attempts")
                        break
                    
                    # If we have validation errors but this is the last iteration
                    if iteration == max_iterations - 1:
                        print(f"⚠ Max iterations ({max_iterations}) reached. Remaining validation errors:")
                        for error in validation_errors:
                            print(f"  - {error}")
                        break
                    
                    # Print validation errors for this iteration
                    if validation_errors:
                        print(f"Validation errors found in attempt {iteration + 1}:")
                        for error in validation_errors:
                            print(f"  - {error}")
                    
                    iteration += 1
                    
                except json.JSONDecodeError as e:
                    if iteration == max_iterations - 1:
                        raise Exception(f"Failed to parse JSON response after {max_iterations} attempts: {e}")
                    print(f"JSON parsing failed in attempt {iteration + 1}, retrying...")
                    iteration += 1
                    continue
            
            return result
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {e}") 