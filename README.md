# Container OCR

A Python script that extracts shipping container information from images using OCR technology powered by AI models via OpenRouter API.

## Features

- **Automated OCR**: Extract text and data from shipping container images
- **Multiple AI Models**: Support for various vision-capable AI models through OpenRouter
- **Structured Output**: Returns container information in structured JSON format
- **Comprehensive Data Extraction**: Captures container IDs, carriers, dimensions, weight specifications, and more
- **Container ID Validation**: Automatic validation of container IDs using industry-standard check digit algorithms
- **Intelligent Correction**: Iterative correction of invalid container IDs using AI with conversation context
- **Image Validation**: Built-in image format validation and error handling
- **Flexible Output**: Save results to custom JSON files

## What Data is Extracted

The script extracts the following information from container images:

- **Container ID**: Unique identifiers (e.g., "CMCU 455 7748")
- **Carrier**: Shipping company name (e.g., "CROWLEY")
- **Container Type**: Type classification (e.g., "LPG1", "Reefer")
- **Dimensions**: Length and height measurements
- **Weight Specifications**:
  - M.G.W (Maximum Gross Weight)
  - TARE (Empty weight)
  - NET (Payload capacity)
- **Cubic Capacity**: Volume in cubic meters and cubic feet
- **Additional Markings**: Any other visible markings or codes

## Container ID Validation & Correction

The script includes advanced container ID validation and correction capabilities:

### Automatic Validation
- **Check Digit Verification**: Validates container IDs using ISO 6346 standard check digit algorithms
- **Format Validation**: Ensures container IDs follow the correct 4-letter + 7-digit format
- **Real-time Detection**: Identifies invalid container IDs immediately after extraction

### Intelligent Correction Process
- **Iterative Correction**: Automatically attempts to correct invalid container IDs using AI
- **Context Preservation**: Maintains full conversation history for accurate corrections
- **Container Count Protection**: Ensures corrections don't reduce the number of detected containers
- **Configurable Attempts**: Set maximum correction iterations (default: 3 attempts)

### How It Works
1. **Initial Extraction**: OCR processes the image and extracts container data
2. **Validation Check**: Each container ID is validated against industry standards
3. **Correction Loop**: If invalid IDs are found, the AI is prompted to correct them using:
   - Full conversation context from previous attempts
   - List of specific invalid container IDs
   - Requirement to maintain or increase container count
4. **Success or Timeout**: Process continues until all IDs are valid or max iterations reached

### Usage Examples
```bash
# Use default 3 correction attempts
python container_ocr.py image.jpg

# Allow up to 5 correction attempts for challenging images
python container_ocr.py image.jpg --max-iterations 5

# Disable corrections (single attempt only)
python container_ocr.py image.jpg --max-iterations 1
```

## Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Requirements

- Python 3.7+
- OpenRouter API key (for accessing AI vision models)
- Required packages:
  - `openai>=1.50.0`
  - `Pillow>=10.0.0`

## API Setup

1. **Get an OpenRouter API key**:
   - Visit [OpenRouter](https://openrouter.ai/)
   - Create an account and generate an API key

2. **Set your API key** (choose one method):
   - **Environment variable** (recommended):
     ```bash
     export OPENROUTER_API_KEY="your_api_key_here"
     ```
   - **Command line argument**:
     ```bash
     python container_ocr.py image.jpg --api-key your_api_key_here
     ```

## Usage

### Basic Usage

```bash
python container_ocr.py path/to/container/image.jpg
```

This will:
- Process the image
- Extract container data
- Save results to `container_data.json`

### Advanced Usage

```bash
python container_ocr.py image.jpg --output custom_output.json --api-key your_key
```

### Command Line Options

- `image_path`: Path to the container image file (required)
- `--output`, `-o`: Output JSON file path (default: `container_data.json`)
- `--model`: AI model to use for OCR (default: `google/gemini-2.5-flash`)
- `--api-key`: OpenRouter API key (alternative to environment variable)
- `--max-iterations`: Maximum number of validation correction attempts (default: `3`)

## AI Models

This application supports various AI models through the OpenRouter API. Different models have different capabilities, speeds, and costs.

### Specifying Models

You can specify which model to use with the `--model` parameter:

```bash
python container_ocr.py image.jpg --model google/gemini-2.5-flash
```

### Recommended Models

#### **Google Gemini Models** (Recommended)
- **`google/gemini-2.5-flash`** (Default)
  - Excellent vision capabilities
  - Fast processing
  - Good cost-performance ratio
  - Best for most container OCR tasks

- **`google/gemini-2.5-pro`**
  - Higher accuracy for complex images
  - Better at handling poor quality images
  - Higher cost than Flash model
  - Best for challenging or critical extractions

### Model Selection Guidelines

**For General Use:**
```bash
python container_ocr.py image.jpg --model google/gemini-2.5-flash
```

**For High Accuracy (complex/poor quality images):**
```bash
python container_ocr.py image.jpg --model google/gemini-2.5-pro
```

## Example Output

```json
[
  {
    "container_id": "CMCU4557748",
    "carrier": "CROWLEY",
    "type": "LPG1",
    "dimensions": {
      "length": "45'",
      "height": "102\""
    },
    "marked_details": {
      "location": "Some Location",
      "code": "ABC123"
    },
    "weight_capacity": {
      "M.G.W": {
        "kgs": "30480",
        "lbs": "67200"
      },
      "TARE": {
        "kgs": "4200",
        "lbs": "9260"
      },
      "NET": {
        "kgs": "26280",
        "lbs": "57940"
      },
      "CUB.CAP": {
        "cum": "76.4",
        "cuft": "2700"
      }
    }
  }
]
```

## Supported Image Formats

- JPEG
- PNG
- Other formats supported by PIL/Pillow

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid image files
- API connection issues
- JSON parsing errors
- Invalid API responses

## Limitations

- Requires internet connection for API access
- Processing time depends on image size and complexity
- API usage is subject to OpenRouter rate limits and pricing

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the script.

## License

This project is open source. Please check the license file for details. 