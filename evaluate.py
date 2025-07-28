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
            raise Exception(f"main.py failed: {result.stderr}")
        
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
    """Run all tests in parallel."""
    
    # Create all test combinations
    test_jobs = []
    for model in models:
        for test_case in test_cases:
            test_jobs.append((model, test_case))
    
    print(f"Running {len(test_jobs)} tests in parallel (max {max_workers} workers)...")
    
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
                
                # Print progress
                if result['success']:
                    print(f"✅ {model} on {test_case}: F1={result['metrics']['f1_score']:.3f} ({result['execution_time']:.1f}s)")
                else:
                    print(f"❌ {model} on {test_case}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ {model} on {test_case}: Unexpected error: {e}")
                results.append({
                    'model': model,
                    'test_case': test_case,
                    'success': False,
                    'execution_time': 0,
                    'metrics': None,
                    'error': f"Unexpected error: {e}"
                })
    
    return results

# Function to print a comprehensive summary of test results
def print_summary(results: List[Dict], models: List[str], test_cases: List[str]):
    """Print a comprehensive summary of test results."""
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    # Overall statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
    
    # Per-model summary
    print("\n" + "-"*60)
    print("PER-MODEL SUMMARY")
    print("-"*60)
    
    for model in models:
        model_results = [r for r in results if r['model'] == model and r['success']]
        all_model_results = [r for r in results if r['model'] == model]
        
        if not model_results:
            print(f"\n{model}: No successful tests")
            continue
            
        avg_f1 = sum(r['metrics']['f1_score'] for r in model_results) / len(model_results)
        avg_precision = sum(r['metrics']['precision'] for r in model_results) / len(model_results)
        avg_recall = sum(r['metrics']['recall'] for r in model_results) / len(model_results)
        avg_time = sum(r['execution_time'] for r in model_results) / len(model_results)
        
        # Calculate accuracy (percentage of perfect F1 scores)
        perfect_results = sum(1 for r in model_results if r['metrics']['f1_score'] == 1.0)
        accuracy = perfect_results / len(all_model_results) if all_model_results else 0
        
        print(f"\n{model}:")
        print(f"  Overall Accuracy: {accuracy:.1%} ({perfect_results}/{len(all_model_results)} perfect)")
        print(f"  Average F1 Score: {avg_f1:.3f}")
        print(f"  Average Precision: {avg_precision:.3f}")
        print(f"  Average Recall: {avg_recall:.3f}")
        print(f"  Average Execution Time: {avg_time:.1f}s")
        print(f"  Successful Tests: {len(model_results)}/{len(all_model_results)}")
    
    # Per-test-case summary
    print("\n" + "-"*60)
    print("PER-TEST-CASE SUMMARY")
    print("-"*60)
    
    for test_case in test_cases:
        case_results = [r for r in results if r['test_case'] == test_case and r['success']]
        if not case_results:
            print(f"\n{test_case}: No successful tests")
            continue
            
        avg_f1 = sum(r['metrics']['f1_score'] for r in case_results) / len(case_results)
        avg_time = sum(r['execution_time'] for r in case_results) / len(case_results)
        
        print(f"\n{test_case}:")
        print(f"  Average F1 Score: {avg_f1:.3f}")
        print(f"  Average Execution Time: {avg_time:.1f}s")
        print(f"  Successful Tests: {len(case_results)}/{len([r for r in results if r['test_case'] == test_case])}")
    
    # Detailed results table
    print("\n" + "-"*80)
    print("DETAILED RESULTS")
    print("-"*80)
    print(f"{'Model':<25} {'Test Case':<12} {'F1':<6} {'Prec':<6} {'Rec':<6} {'Time':<6} {'Status'}")
    print("-"*80)
    
    for result in sorted(results, key=lambda x: (x['model'], x['test_case'])):
        if result['success']:
            metrics = result['metrics']
            print(f"{result['model']:<25} {result['test_case']:<12} "
                  f"{metrics['f1_score']:.3f}  {metrics['precision']:.3f}  "
                  f"{metrics['recall']:.3f}  {result['execution_time']:5.1f}s  ✅")
        else:
            print(f"{result['model']:<25} {result['test_case']:<12} "
                  f"{'N/A':<6} {'N/A':<6} {'N/A':<6} {'N/A':<6} ❌ {result['error'][:30]}")
    
    # Failed tests details
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print("\n" + "-"*60)
        print("FAILED TESTS DETAILS")
        print("-"*60)
        for result in failed_results:
            print(f"\n{result['model']} on {result['test_case']}:")
            print(f"  Error: {result['error']}")

# Function to save detailed results to JSON file
def save_detailed_results(results: List[Dict], output_file: str):
    """Save detailed results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    summary_data = {
        'timestamp': timestamp,
        'total_tests': len(results),
        'successful_tests': sum(1 for r in results if r['success']),
        'results': results
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

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
    
    parser.add_argument(
        "--output",
        default="output/test_results_{timestamp}.json",
        help="Output file for detailed results"
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
    
    print(f"Testing {len(models)} models on {len(test_cases)} test cases")
    print(f"Models: {', '.join(models)}")
    print(f"Test cases: {', '.join(test_cases)}")
    print()
    
    # Run tests
    start_time = time.time()
    results = run_tests_parallel(models, test_cases, api_key, args.max_iterations, args.max_workers)
    total_time = time.time() - start_time
    
    print(f"\nAll tests completed in {total_time:.1f}s")
    
    # Print summary
    print_summary(results, models, test_cases)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output.format(timestamp=timestamp)
    save_detailed_results(results, output_file)

if __name__ == "__main__":
    main() 