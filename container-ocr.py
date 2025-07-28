#!/usr/bin/env python3
"""
Container OCR Script using OpenRouter and Gemini 2.5 Flash
Extracts shipping container information from images and returns structured JSON.
"""

import json
import base64
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from openai import OpenAI
from PIL import Image

class ContainerOCR:
    def __init__(self, api_key: str):
        """Initialize the OCR client with OpenRouter API key."""
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Container Data",
            "description": "Schema for an array of shipping container information.",
            "type": "array",
            "items": {
                "type": "object",
                "title": "Container",
                "description": "Details about a single shipping container.",
                "required": [
                    "container_id",
                    "carrier",
                    "type",
                    "dimensions",
                    "marked_details",
                    "weight_capacity"
                ],
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Unique identifier for the container, e.g., 'CMCU 455 7748' or 'SEKU 920653 4'."
                    },
                    "carrier": {
                        "type": "string",
                        "description": "The name of the shipping carrier.",
                        "enum": [
                            "CROWLEY",
                            "Unknown"
                        ]
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of container, e.g., 'LPG1' or 'Reefer (45R1)'."
                    },
                    "dimensions": {
                        "type": "object",
                        "description": "Physical dimensions of the container.",
                        "required": [
                            "length",
                            "height"
                        ],
                        "properties": {
                            "length": {
                                "type": "string",
                                "description": "Length of the container, e.g., '45''."
                            },
                            "height": {
                                "type": "string",
                                "description": "Height of the container, e.g., '102\"' or 'Unknown'."
                            }
                        },
                        "additionalProperties": False
                    },
                    "marked_details": {
                        "type": "object",
                        "description": "Additional details marked on the container, which can vary.",
                        "patternProperties": {
                            "^(location|code|identifier|additional_mark|additional_info_\\d+)$": {
                                "type": "string"
                            }
                        },
                        "additionalProperties": False
                    },
                    "weight_capacity": {
                        "type": "object",
                        "description": "Detailed weight and volume capacities of the container.",
                        "properties": {
                            "M.G.W": {
                                "type": "object",
                                "description": "Maximum Gross Weight.",
                                "required": [
                                    "kgs",
                                    "lbs"
                                ],
                                "properties": {
                                    "kgs": {
                                        "type": "string",
                                        "description": "Maximum Gross Weight in kilograms."
                                    },
                                    "lbs": {
                                        "type": "string",
                                        "description": "Maximum Gross Weight in pounds."
                                    }
                                },
                                "additionalProperties": False
                            },
                            "TARE": {
                                "type": "object",
                                "description": "Tare Weight (empty weight).",
                                "required": [
                                    "kgs",
                                    "lbs"
                                ],
                                "properties": {
                                    "kgs": {
                                        "type": "string",
                                        "description": "Tare Weight in kilograms."
                                    },
                                    "lbs": {
                                        "type": "string",
                                        "description": "Tare Weight in pounds."
                                    }
                                },
                                "additionalProperties": False
                            },
                            "NET": {
                                "type": "object",
                                "description": "Net Weight (payload capacity).",
                                "required": [
                                    "kgs",
                                    "lbs"
                                ],
                                "properties": {
                                    "kgs": {
                                        "type": "string",
                                        "description": "Net Weight in kilograms."
                                    },
                                    "lbs": {
                                        "type": "string",
                                        "description": "Net Weight in pounds."
                                    }
                                },
                                "additionalProperties": False
                            },
                            "CUB.CAP": {
                                "type": "object",
                                "description": "Cubic Capacity.",
                                "required": [
                                    "cum",
                                    "cuft"
                                ],
                                "properties": {
                                    "cum": {
                                        "type": "string",
                                        "description": "Cubic Capacity in cubic meters."
                                    },
                                    "cuft": {
                                        "type": "string",
                                        "description": "Cubic Capacity in cubic feet."
                                    }
                                },
                                "additionalProperties": False
                            }
                        },
                        "additionalProperties": False
                    }
                }
            }
        }

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encoding image: {e}")

    def validate_image(self, image_path: str) -> bool:
        """Validate that the image file exists and is readable."""
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Try to open with PIL to validate format
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            raise Exception(f"Invalid image file: {e}")

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
            self.validate_image(image_path)
            
            # Encode image
            base64_image = self.encode_image(image_path)
            
            # Create prompt
            prompt = self.create_prompt()
            
            # Make API call
            response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash",
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
                max_tokens=64000,
                temperature=0.0
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            
            # Clean up response (remove markdown formatting if present)
            if content.startswith("```json"):
                content = content.strip("```json").strip("```").strip()
            elif content.startswith("```"):
                content = content.strip("```").strip()
            
            # Parse JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON response: {e}\nResponse: {content}")
                
        except Exception as e:
            raise Exception(f"OCR extraction failed: {e}")

    def save_results(self, data: Dict[str, Any], output_path: str) -> None:
        """Save results to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_path}")
        except Exception as e:
            raise Exception(f"Failed to save results: {e}")


def main():
    """Main function to run the container OCR."""
    parser = argparse.ArgumentParser(
        description="Extract shipping container information from images using OCR"
    )
    parser.add_argument(
        "image_path",
        help="Path to the container image file"
    )
    parser.add_argument(
        "--output", "-o",
        default="container_data.json",
        help="Output JSON file path (default: container_data.json)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    import os
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required. Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    try:
        # Initialize OCR
        ocr = ContainerOCR(api_key)
        
        # Extract data
        print(f"Processing image: {args.image_path}")
        container_data = ocr.extract_container_data(args.image_path)
        
        # Save results
        ocr.save_results(container_data, args.output)
        
        # Print summary
        container_count = len(container_data) if isinstance(container_data, list) else 0
        print(f"Successfully extracted data for {container_count} containers")
        
        # Print brief summary
        if container_count > 0:
            print("\nContainer Summary:")
            for i, container in enumerate(container_data[:5], 1):  # Show first 5
                container_id = container.get('container_id', 'Unknown')
                carrier = container.get('carrier', 'Unknown')
                print(f"  {i}. {container_id} ({carrier})")
            
            if container_count > 5:
                print(f"  ... and {container_count - 5} more containers")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()