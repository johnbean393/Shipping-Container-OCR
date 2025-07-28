"""
Container ID validation utilities.
"""

import re
from src.config import CONTAINER_ID_LENGTH, CONTAINER_ID_PATTERN, LETTER_VALUES


def validate_container_id(container_id: str) -> bool:
    """Validate that the container ID is in the correct format."""
    try:
        # Clean the container ID by removing spaces and converting to uppercase
        cleaned_id = re.sub(r'[^A-Z0-9]', '', container_id.upper())
        
        # Check if the cleaned container ID is in the correct format (4 letters + 6 digits + 1 check digit)
        if not re.match(CONTAINER_ID_PATTERN, cleaned_id):
            return False
        
        # More explicit: ensure total length is 11
        if len(cleaned_id) != CONTAINER_ID_LENGTH:
            return False
        
        # Extract check digit (last digit)
        checkdigit = cleaned_id[-1]
        if not checkdigit.isdigit():
            return False
        
        # Calculate check digit for validation (first 10 characters: 4 letters + 6 digits)
        calculated_checkdigit = calculate_check_digit(cleaned_id[:-1])
        return str(calculated_checkdigit) == checkdigit
        
    except (ValueError, IndexError, AttributeError):
        return False


def calculate_check_digit(container_code: str) -> int:
    """Calculate check digit for a container code (first 10 characters)."""
    # Clean the container code by removing any non-alphanumeric characters
    container_code = re.sub(r'[^A-Z0-9]', '', container_code.upper())
    
    # Ensure we have exactly 10 characters for calculation
    if len(container_code) != 10:
        raise ValueError(f"Container code must be exactly 10 characters after cleaning, got {len(container_code)}: '{container_code}'")
    
    # Calculate sum using position-based multiplication factors
    total_sum = 0
    for i, char in enumerate(container_code):
        if char.isalpha():
            if char not in LETTER_VALUES:
                raise ValueError(f"Invalid letter '{char}' in container code")
            value = LETTER_VALUES[char]
        elif char.isdigit():
            value = int(char)
        else:
            raise ValueError(f"Invalid character '{char}' in container code")
        
        # Multiply by 2^position where position starts at 0
        multiplier = 2 ** i
        total_sum += value * multiplier
    
    # Calculate check digit
    remainder = total_sum % 11
    # If remainder is 10, check digit becomes 0
    return 0 if remainder == 10 else remainder


def clean_container_id(container_id: str) -> str:
    """Clean and normalize a container ID."""
    return re.sub(r'[^A-Z0-9]', '', str(container_id).upper()) 