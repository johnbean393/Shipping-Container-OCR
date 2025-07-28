#!/usr/bin/env python3
"""
Test script for Container OCR models.
Tests multiple models on test data and evaluates performance.
"""

import argparse
import os
import sys
import json
import time
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Any
import tempfile
from tqdm import tqdm

# Function to load expected results for a test case
def load_expected_results(test_case: str) -> List[Dict[str, str]]:
    """Load expected results for a test case."""
    answer_file = f"test_data/answers/{test_case}.json"
    with open(answer_file, 'r') as f:
        return json.load(f)

# Function to run main.py for a specific image and model
def run_main_py(image_path: str, model: str, api_key: str, max_iterations: int = 3) -> Tuple[List[Dict], float, str]:
    """
    Run main.py for a specific image and model.
    Returns (results, execution_time, output_file).
    """
    start_time = time.time()
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        output_file = tmp_file.name
    
    try:
        # Build command
        cmd = [
            sys.executable, "main.py",
            image_path,
            "--output", output_file,
            "--model", model,
            "--api-key", api_key,
            "--max-iterations", str(max_iterations)
        ]
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise Exception(f"main.py failed: {error_msg}")
        
        # Load results
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                results = json.load(f)
        else:
            results = []
            
        return results, execution_time, output_file
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        raise Exception(f"Timeout after {execution_time:.2f}s")
    except Exception as e:
        execution_time = time.time() - start_time
        raise Exception(f"Error after {execution_time:.2f}s: {str(e)}")

# Function to calculate evaluation metrics between predicted and expected results
def calculate_metrics(predicted: List[Dict], expected: List[Dict]) -> Dict[str, Any]:
    """Calculate evaluation metrics between predicted and expected results."""
    predicted_ids = set(item.get('container_id', '') for item in predicted)
    expected_ids = set(item.get('container_id', '') for item in expected)
    
    # Remove empty strings
    predicted_ids.discard('')
    expected_ids.discard('')
    
    true_positives = len(predicted_ids & expected_ids)
    false_positives = len(predicted_ids - expected_ids)
    false_negatives = len(expected_ids - predicted_ids)
    
    precision = true_positives / len(predicted_ids) if predicted_ids else 0
    recall = true_positives / len(expected_ids) if expected_ids else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'total_predicted': len(predicted_ids),
        'total_expected': len(expected_ids),
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'predicted_ids': sorted(list(predicted_ids)),
        'expected_ids': sorted(list(expected_ids)),
        'missing_ids': sorted(list(expected_ids - predicted_ids)),
        'extra_ids': sorted(list(predicted_ids - expected_ids))
    }

# Function to test a single model on a single test case
def test_single_case(model: str, test_case: str, api_key: str, max_iterations: int) -> Dict[str, Any]:
    """Test a single model on a single test case."""
    image_path = f"test_data/images/{test_case}.jpeg"
    
    try:
        # Run the test
        predicted_results, execution_time, output_file = run_main_py(
            image_path, model, api_key, max_iterations
        )
        
        # Load expected results
        expected_results = load_expected_results(test_case)
        
        # Calculate metrics
        metrics = calculate_metrics(predicted_results, expected_results)
        
        # Clean up temporary file
        try:
            os.unlink(output_file)
        except:
            pass
        
        return {
            'model': model,
            'test_case': test_case,
            'success': True,
            'execution_time': execution_time,
            'metrics': metrics,
            'error': None
        }
        
    except Exception as e:
        return {
            'model': model,
            'test_case': test_case,
            'success': False,
            'execution_time': 0,
            'metrics': None,
            'error': str(e)
        }

# Function to run all tests in parallel
def run_tests_parallel(models: List[str], test_cases: List[str], api_key: str, max_iterations: int, max_workers: int = 4) -> List[Dict]:
    """Run all tests in parallel with progress bars for each model."""
    
    # Create all test combinations
    test_jobs = []
    for model in models:
        for test_case in test_cases:
            test_jobs.append((model, test_case))
    
    # Create progress bars for each model
    progress_bars = {}
    for model in models:
        progress_bars[model] = tqdm(
            total=len(test_cases), 
            desc=f"{model:<30}", 
            position=models.index(model),
            leave=True,
            unit="test"
        )
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_job = {
            executor.submit(test_single_case, model, test_case, api_key, max_iterations): (model, test_case)
            for model, test_case in test_jobs
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_job):
            model, test_case = future_to_job[future]
            try:
                result = future.result()
                results.append(result)
                
                # Update progress bar for this model
                if result['success']:
                    progress_bars[model].set_postfix_str("✓", refresh=False)
                else:
                    progress_bars[model].set_postfix_str("✗", refresh=False)
                progress_bars[model].update(1)
                    
            except Exception as e:
                results.append({
                    'model': model,
                    'test_case': test_case,
                    'success': False,
                    'execution_time': 0,
                    'metrics': None,
                    'error': f"Unexpected error: {e}"
                })
                
                # Update progress bar for this model
                progress_bars[model].set_postfix_str("✗", refresh=False)
                progress_bars[model].update(1)
    
    # Close all progress bars
    for pbar in progress_bars.values():
        pbar.close()
    
    # Add some spacing after progress bars
    print()
    
    return results

# Function to print a simple accuracy summary
def print_summary(results: List[Dict], models: List[str], test_cases: List[str]):
    """Print a simple accuracy summary."""
    
    print("Average Accuracy (correctly extracted IDs / total containers):")
    
    for model in models:
        model_results = [r for r in results if r['model'] == model]
        
        if not model_results:
            print(f"{model}: No tests completed")
            continue
        
        # Calculate accuracy across all test cases for this model
        total_correct = 0
        total_containers = 0
        successful_tests = 0
        
        for result in model_results:
            if result['success'] and result['metrics']:
                # Count containers that were correctly identified (true positives)
                total_correct += result['metrics']['true_positives']
                # Count total containers that should have been found
                total_containers += result['metrics']['total_expected']
                successful_tests += 1
        
        if total_containers > 0:
            accuracy = total_correct / total_containers
            print(f"{model}: {accuracy:.1%} ({total_correct}/{total_containers} containers correct)")
        else:
            print(f"{model}: No valid test results")
    
    # Overall statistics
    failed_tests = sum(1 for r in results if not r['success'])
    if failed_tests > 0:
        print(f"\nNote: {failed_tests} tests failed and were excluded from accuracy calculation")



# Main function to run the tests
def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(
        description="Test multiple models on container OCR test data"
    )
    
    parser.add_argument(
        "--models",
        required=True,
        help="Semicolon-separated list of model IDs to test (e.g., 'model1;model2;model3')"
    )
    
    parser.add_argument(
        "--test-cases",
        default="container_0;container_1;container_2;container_3",
        help="Semicolon-separated list of test cases (default: all available)"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of correction iterations (default: 3)"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of parallel workers (default: 8)"
    )
    
    args = parser.parse_args()
    
    # Parse models and test cases
    models = [model.strip() for model in args.models.split(';') if model.strip()]
    test_cases = [case.strip() for case in args.test_cases.split(';') if case.strip()]
    
    if not models:
        print("Error: No models specified")
        sys.exit(1)
    
    if not test_cases:
        print("Error: No test cases specified")
        sys.exit(1)
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required. Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Validate test cases exist
    for test_case in test_cases:
        image_path = f"test_data/images/{test_case}.jpeg"
        answer_path = f"test_data/answers/{test_case}.json"
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            sys.exit(1)
        if not os.path.exists(answer_path):
            print(f"Error: Answer file not found: {answer_path}")
            sys.exit(1)
    
    # Run tests
    results = run_tests_parallel(models, test_cases, api_key, args.max_iterations, args.max_workers)
    
    # Print summary
    print_summary(results, models, test_cases)

if __name__ == "__main__":
    main() 