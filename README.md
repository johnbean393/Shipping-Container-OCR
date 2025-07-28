# Container OCR

A Python script that extracts shipping container IDs from images using OCR technology powered by AI models via OpenRouter API.

## Features

- **Automated OCR**: Extract container IDs from shipping container images
- **Multiple AI Models**: Support for various vision-capable AI models through OpenRouter
- **Structured Output**: Returns container IDs in structured JSON format
- **Container ID Focus**: Specifically designed to extract only container identification numbers
- **Container ID Validation**: Automatic validation of container IDs using industry-standard check digit algorithms
- **Intelligent Correction**: Iterative correction of invalid container IDs using AI with conversation context
- **Image Validation**: Built-in image format validation and error handling
- **Organized Output**: Saves results to the `output/` directory with automatic timestamping

## What Data is Extracted

The script extracts only the **Container IDs** from container images:

- **Container ID**: Unique identifiers (e.g., "CMCU4557748", "SEKU9206534")
  - 4 letters (owner code) + 7 digits
  - Follows ISO 6346 standard format
  - Includes automatic check digit validation

## Project Structure

```
Container OCR/
├── src/                    # Source code directory
│   ├── __init__.py
│   ├── container_ocr.py    # Main OCR logic
│   ├── container_validator.py  # Container ID validation
│   ├── llm_client.py      # OpenRouter API client
│   ├── utils.py           # Utility functions
│   ├── config.py          # Configuration settings
│   └── schema.json        # JSON schema for container IDs
├── test_data/              # Test dataset
│   ├── images/            # Test container images
│   └── answers/           # Expected results for evaluation
├── output/                 # Output directory for JSON files
├── main.py                # Main entry point
├── evaluate.py            # Model evaluation script
├── requirements.txt       # Python dependencies
└── README.md
```

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
python main.py image.jpg

# Allow up to 5 correction attempts for challenging images
python main.py image.jpg --max-iterations 5

# Disable corrections (single attempt only)
python main.py image.jpg --max-iterations 1
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
     python main.py image.jpg --api-key your_api_key_here
     ```

## Usage

### Basic Usage

```bash
python main.py path/to/container/image.jpg
```

This will:
- Process the image
- Extract container IDs
- Save results to `output/container_data_YYYYMMDD_HHMMSS.json` (with timestamp)

### Advanced Usage

```bash
python main.py image.jpg --output output/custom_output.json --api-key your_key
```

### Output File Naming

- **Default**: `output/container_data_20241216_143022.json` (includes timestamp)
- **Custom**: Any path you specify with `--output` or `-o`

The timestamp format is `YYYYMMDD_HHMMSS` to ensure files are sorted chronologically and prevent overwrites.

### Command Line Options

- `image_path`: Path to the container image file (required)
- `--output`, `-o`: Output JSON file path (default: `output/container_data_{timestamp}.json`)
- `--model`: AI model to use for OCR (default: `google/gemini-2.5-flash`)
- `--api-key`: OpenRouter API key (alternative to environment variable)
- `--max-iterations`: Maximum number of validation correction attempts (default: `3`)

## AI Models

This application supports various AI models through the OpenRouter API. Different models have different capabilities, speeds, and costs.

### Specifying Models

You can specify which model to use with the `--model` parameter:

```bash
python main.py image.jpg --model google/gemini-2.5-flash
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
python main.py image.jpg --model google/gemini-2.5-flash
```

**For High Accuracy (complex/poor quality images):**
```bash
python main.py image.jpg --model google/gemini-2.5-pro
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

## Model Evaluation

The project includes a comprehensive evaluation system to test and compare multiple models on a standardized test dataset.

### Evaluation Script: `evaluate.py`

The evaluation script allows you to:
- **Test Multiple Models**: Compare different AI models side-by-side
- **Parallel Execution**: Run all tests concurrently for maximum efficiency
- **Comprehensive Metrics**: Get detailed performance analysis
- **Automated Validation**: Compare results against ground truth data

### Test Dataset

The `test_data/` directory contains:
- **4 Test Images**: `container_0.jpeg` through `container_3.jpeg`
- **Ground Truth Answers**: Expected container IDs for each image
- **Standardized Format**: Consistent evaluation across all models

### Usage Examples

#### Test a Single Model
```bash
python evaluate.py --models "google/gemini-2.5-flash"
```

#### Compare Multiple Models
```bash
python evaluate.py --models "google/gemini-2.5-flash;anthropic/claude-3-haiku;openai/gpt-4o-mini"
```

#### Test Specific Cases
```bash
python evaluate.py --models "google/gemini-2.5-flash" --test-cases "container_0;container_1"
```

#### Customize Performance Settings
```bash
python evaluate.py --models "google/gemini-2.5-flash" --max-workers 8 --max-iterations 5
```

### Command Line Options

- `--models`: **Required** - Semicolon-separated list of model IDs to test
- `--test-cases`: Test cases to run (default: all available)
- `--api-key`: OpenRouter API key (or use `OPENROUTER_API_KEY` environment variable)
- `--max-iterations`: Maximum correction iterations per test (default: 3)
- `--max-workers`: Number of parallel workers (default: 4)
- `--output`: Output file for detailed results (default: `output/test_results_{timestamp}.json`)

### Evaluation Metrics

The evaluation provides comprehensive performance metrics:

#### **Precision**: How many predicted container IDs were correct
- `Precision = True Positives / (True Positives + False Positives)`

#### **Recall**: How many actual container IDs were found
- `Recall = True Positives / (True Positives + False Negatives)`

#### **F1-Score**: Harmonic mean of precision and recall
- `F1 = 2 × (Precision × Recall) / (Precision + Recall)`

#### **Execution Time**: Processing time for each test case

### Sample Output

```
Testing 3 models on 4 test cases
Models: google/gemini-2.5-flash, anthropic/claude-3-haiku, openai/gpt-4o-mini
Test cases: container_0, container_1, container_2, container_3

Running 12 tests in parallel (max 4 workers)...
✅ google/gemini-2.5-flash on container_0: F1=1.000 (12.3s)
✅ anthropic/claude-3-haiku on container_1: F1=0.950 (8.7s)
✅ openai/gpt-4o-mini on container_2: F1=0.889 (15.2s)
...

================================================================================
TEST RESULTS SUMMARY
================================================================================
Total tests: 12
Successful: 11
Failed: 1
Success rate: 91.7%

------------------------------------------------------------
PER-MODEL SUMMARY
------------------------------------------------------------

google/gemini-2.5-flash:
  Average F1 Score: 0.975
  Average Precision: 0.980
  Average Recall: 0.971
  Average Execution Time: 11.2s
  Successful Tests: 4/4

anthropic/claude-3-haiku:
  Average F1 Score: 0.923
  Average Precision: 0.935
  Average Recall: 0.912
  Average Execution Time: 9.8s
  Successful Tests: 4/4
...
```

### Detailed Results

All evaluation results are automatically saved to timestamped JSON files in the `output/` directory, containing:
- Individual test results and metrics
- Detailed ID-level analysis (missing/extra container IDs)
- Execution times and error details
- Complete evaluation metadata

### Parallel Processing

The evaluation system runs tests in parallel by default:
- **Multiple Models**: All model+test_case combinations run simultaneously
- **Configurable Workers**: Adjust `--max-workers` based on your system and API limits
- **Real-time Progress**: Live updates as tests complete
- **Error Resilience**: Failed tests don't block other tests

### Best Practices

1. **Start Small**: Test with one model first to verify setup
2. **Manage API Limits**: Use `--max-workers` to control concurrent API calls
3. **Save Results**: Always review the detailed JSON output files
4. **Compare Systematically**: Use consistent `--max-iterations` across model comparisons
5. **Monitor Performance**: Track both accuracy and execution time

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the script.

## License

This project is open source. Please check the license file for details. 