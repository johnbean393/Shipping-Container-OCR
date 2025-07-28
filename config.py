"""
Configuration settings for Container OCR application.
"""

# API Configuration
DEFAULT_MODEL = "google/gemini-2.5-flash"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# File paths
SCHEMA_FILE = "schema.json"
DEFAULT_OUTPUT_FILE = "container_data.json"

# API limits
MAX_TOKENS = 64000
TEMPERATURE = 0.0

# Container ID validation
CONTAINER_ID_LENGTH = 11
CONTAINER_ID_PATTERN = r'^[A-Z]{4}[0-9]{6}[0-9]$'

# Letter to number mapping for check digit calculation (excluding multiples of 11)
LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17,
    'H': 18, 'I': 19, 'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25,
    'O': 26, 'P': 27, 'Q': 28, 'R': 29, 'S': 30, 'T': 31, 'U': 32,
    'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
} 