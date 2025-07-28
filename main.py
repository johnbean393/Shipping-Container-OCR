#!/usr/bin/env python3
"""
Container OCR Script using OpenRouter and Gemini 2.5 Flash
Extracts shipping container IDs from images and returns structured JSON.
"""

import argparse
import sys
import os
import json
from datetime import datetime

from src.container_ocr import ContainerOCR
from src.utils import save_results
from src.config import DEFAULT_MODEL, DEFAULT_OUTPUT_FILE, DEFAULT_MAX_ITERATIONS


def main():
    """Main function to run the container OCR."""
    parser = argparse.ArgumentParser(
        description="Extract container IDs from images using OCR"
    )
    parser.add_argument(
        "image_path",
        help="Path to the container image file"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT_FILE})"
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use for OCR (default: {DEFAULT_MODEL})"
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum number of correction iterations (default: {DEFAULT_MAX_ITERATIONS})"
    )
    
    args = parser.parse_args()
    
    # Generate timestamp and update output path if using default
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output == DEFAULT_OUTPUT_FILE:
        args.output = DEFAULT_OUTPUT_FILE.format(timestamp=timestamp)
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required. Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    try:
        # Initialize OCR
        ocr = ContainerOCR(args.model, api_key)
        # Extract data
        print(f"Processing image: {args.image_path}")
        container_data = ocr.extract_container_data(args.image_path, max_iterations=args.max_iterations)
        # Save results
        save_results(container_data, args.output)
        # Print summary
        container_count = len(container_data) if isinstance(container_data, list) else 0
        print(f"Successfully extracted {container_count} container IDs")
        # Print brief summary
        if container_count > 0:
            # Print container IDs
            print("\nContainer IDs:")
            for container in container_data:
                print(container.get('container_id', 'Unknown'))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 