# Container OCR

A Python script that extracts shipping container information from images using OCR technology powered by Google's Gemini 2.5 Flash model via OpenRouter API.

## Features

- **Automated OCR**: Extract text and data from shipping container images
- **Structured Output**: Returns container information in structured JSON format
- **Comprehensive Data Extraction**: Captures container IDs, carriers, dimensions, weight specifications, and more
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

## Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Requirements

- Python 3.7+
- OpenRouter API key (for accessing Gemini 2.5 Flash)
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
     python container-ocr.py image.jpg --api-key your_api_key_here
     ```

## Usage

### Basic Usage

```bash
python container-ocr.py path/to/container/image.jpg
```

This will:
- Process the image
- Extract container data
- Save results to `container_data.json`

### Advanced Usage

```bash
python container-ocr.py image.jpg --output custom_output.json --api-key your_key
```

### Command Line Options

- `image_path`: Path to the container image file (required)
- `--output`, `-o`: Output JSON file path (default: `container_data.json`)
- `--api-key`: OpenRouter API key (alternative to environment variable)

## Example Output

```json
[
  {
    "container_id": "CMCU 455 7748",
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