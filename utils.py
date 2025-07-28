"""
Utility functions for Container OCR application.
"""

import json
import base64
from pathlib import Path
from typing import Dict, Any
from PIL import Image


def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error encoding image: {e}")


def validate_image(image_path: str) -> bool:
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


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load schema from {schema_path}: {e}")


def save_results(data: Dict[str, Any], output_path: str) -> None:
    """Save results to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_path}")
    except Exception as e:
        raise Exception(f"Failed to save results: {e}")


def clean_response_content(content: str) -> str:
    """Clean up API response content by removing markdown formatting."""
    if content.startswith("```json"):
        content = content.strip("```json").strip("```").strip()
    elif content.startswith("```"):
        content = content.strip("```").strip()
    return content 