"""
Container OCR Package
Extracts shipping container IDs from images using AI-powered OCR.
"""

from .container_ocr import ContainerOCR
from .config import DEFAULT_MODEL, DEFAULT_OUTPUT_FILE, DEFAULT_MAX_ITERATIONS

__version__ = "1.0.0"
__all__ = ["ContainerOCR", "DEFAULT_MODEL", "DEFAULT_OUTPUT_FILE", "DEFAULT_MAX_ITERATIONS"] 