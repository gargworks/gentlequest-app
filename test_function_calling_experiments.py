"""
Function Calling Experiments - Test Framework

Systematically test different approaches to improve Gemini's function calling rate.
Currently: ~0% native function calling (all keyword fallback)
Goal: >50% native function calling

Usage:
    python test_function_calling_experiments.py --baseline
    python test_function_calling_experiments.py --experiment prompt_directive
    python test_function_calling_experiments.py --compare
"""

import requests
import time
import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Test configuration
BASE_URL = "https://gentlequest.onrender.com"
# BASE_URL = "http://localhost:5055"  # For local testing

# Test messages covering different mental health issues
TEST_MESSAGES = [
    # Anxiety
    "I feel really anxious about my exams",
    "I'm so nervous about the presentation tomorrow",
    "I can't stop worrying about everything",
    "My anxiety is getting worse",
    
    # Stress
    "I'm feeling overwhelmed with work",
    "There's too much pressure on me",
    "I'm stressed about my deadlines",
    "Everything feels too much right now",
    
    # Panic
    "I think I'm having a panic attack",
    "My heart is racing and I can't breathe",
    "I feel like something terrible is going to happen",
    
    # Sleep
    "I can't fall asleep at night",
    "I'm exhausted but can't sleep",
    "Insomnia is killing me",
    
    # Sadness
    "I feel really sad and lonely",
    "I'm feeling down today",
    "Everything feels hopeless",
    
    # General distress
    "I need help",
    "I don't know what to do",
    "Can you help me feel better?",
]


def test_function_calling_rate(
    num_tests: int = 20,
    experiment_name: str = "baseline",
    delay_seconds: int = 2
) -> Dict:
    """
    Test function calling success rate
    
    Args:
        num_tests: Number of messages to test
        experiment_name: Name of this experiment (for logging)
        delay_seconds: Delay between requests
        
    Returns:
        {
            'experiment': str,
            'timestamp': str,
            'total_tests': int,
            'gemini_called': int,
            'keyword_fallback': int,
            'no_intervention': int,
            'success_rate': float,
            'results': List[dict]
        }
    """
    results = {
        'experiment': experiment_name,
        'timestamp': datetime.now().isoformat(),
        'total_tests': num_tests,
        'gemini_called': 0,
        'keyword_fallback': 0,
        'no_intervention': 0,
        'success_rate': 0.0,
        'results': []
    }
    
    print(f"\n{'='*60}")
    print(f"Experiment: {experiment_name}")
    print(f"Testing {num_tests} messages...")
    print(f"{'='*60}\n")
    
    for i in range(num_tests):
        # Use different message each time
        message = TEST_MESSAGES[i % len(TEST_MESSAGES)]
        session_id = f"fc-test-{experiment_name}-{int(time.time())}-{i}"
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                headers={
                    "Content-Type": "application/json",
                    "X-Session-ID": session_id
                },
                json={"message": message},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Test {i+1}: HTTP {response.status_code}")
                results['results'].append({
                    'test_num': i+1,
                    'message': message,
                    'error': f"HTTP {response.status_code}"
                })
                continue
            
            data = response.json()
            
            # Check if intervention was triggered
            exercise_type = data.get('exercise_type')
            offer_stage = data.get('offer_stage')
            source = data.get('function_call_source', 'unknown')
            
            if exercise_type:
                if source == 'gemini':
                    results['gemini_called'] += 1
                    status = "✅ GEMINI"
                elif source == 'keyword_fallback':
                    results['keyword_fallback'] += 1
                    status = "⚠️  FALLBACK"
                else:
                    status = f"❓ {source}"
            else:
                results['no_intervention'] += 1
                status = "❌ NO INTERVENTION"
            
            print(f"Test {i+1:2d}: {status:20s} | {message[:40]}")
            
            results['results'].append({
                'test_num': i+1,
                'message': message,
                'exercise_type': exercise_type,
                'offer_stage': offer_stage,
                'source': source,
                'has_intervention': bool(exercise_type)
            })
            
        except Exception as e:
            print(f"❌ Test {i+1}: Error - {e}")
            results['results'].append({
                'test_num': i+1,
                'message': message,
                'error': str(e)
            })
        
        # Rate limiting
        if i < num_tests - 1:
            time.sleep(delay_seconds)
    
    # Calculate success rate
    total_interventions = results['gemini_called'] + results['keyword_fallback']
    if total_interventions > 0:
        results['success_rate'] = results['gemini_called'] / total_interventions
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {experiment_name}")
    print(f"{'='*60}")
    print(f"Total Tests:        {results['total_tests']}")
    print(f"Gemini Called:      {results['gemini_called']} ({results['success_rate']*100:.1f}%)")
    print(f"Keyword Fallback:   {results['keyword_fallback']}")
    print(f"No Intervention:    {results['no_intervention']}")
    print(f"{'='*60}\n")
    
    return results


def save_results(results: Dict, filename: str = "function_calling_results.csv"):
    """Save results to CSV for analysis"""
    
    # Check if file exists to determine if we need headers
    try:
        with open(filename, 'r') as f:
            write_header = False
    except FileNotFoundError:
        write_header = True
    
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        
        if write_header:
            writer.writerow([
                'timestamp', 'experiment', 'total_tests', 
                'gemini_called', 'keyword_fallback', 'no_intervention',
                'success_rate'
            ])
        
        writer.writerow([
            results['timestamp'],
            results['experiment'],
            results['total_tests'],
            results['gemini_called'],
            results['keyword_fallback'],
            results['no_intervention'],
            f"{results['success_rate']:.3f}"
        ])
    
    print(f"✅ Results saved to {filename}")


def compare_experiments(filename: str = "function_calling_results.csv"):
    """Compare all experiments from CSV"""
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            experiments = list(reader)
        
        if not experiments:
            print("No experiments found in CSV")
            return
        
        print(f"\n{'='*80}")
        print(f"COMPARISON: All Experiments")
        print(f"{'='*80}")
        print(f"{'Experiment':<30} {'Tests':<8} {'Gemini':<10} {'Fallback':<10} {'Success Rate':<12}")
        print(f"{'-'*80}")
        
        for exp in experiments:
            print(f"{exp['experiment']:<30} "
                  f"{exp['total_tests']:<8} "
                  f"{exp['gemini_called']:<10} "
                  f"{exp['keyword_fallback']:<10} "
                  f"{float(exp['success_rate'])*100:>6.1f}%")
        
        print(f"{'='*80}\n")
        
    except FileNotFoundError:
        print(f"❌ File {filename} not found. Run some experiments first.")


def main():
    parser = argparse.ArgumentParser(description='Test Gemini function calling')
    parser.add_argument('--baseline', action='store_true', 
                       help='Run baseline test (current implementation)')
    parser.add_argument('--experiment', type=str,
                       help='Run specific experiment (e.g., prompt_directive)')
    parser.add_argument('--compare', action='store_true',
                       help='Compare all experiments from CSV')
    parser.add_argument('--num-tests', type=int, default=20,
                       help='Number of test messages (default: 20)')
    parser.add_argument('--delay', type=int, default=2,
                       help='Delay between requests in seconds (default: 2)')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_experiments()
    elif args.baseline:
        results = test_function_calling_rate(
            num_tests=args.num_tests,
            experiment_name='baseline',
            delay_seconds=args.delay
        )
        save_results(results)
    elif args.experiment:
        results = test_function_calling_rate(
            num_tests=args.num_tests,
            experiment_name=args.experiment,
            delay_seconds=args.delay
        )
        save_results(results)
    else:
        print("Usage:")
        print("  python test_function_calling_experiments.py --baseline")
        print("  python test_function_calling_experiments.py --experiment prompt_directive")
        print("  python test_function_calling_experiments.py --compare")


if __name__ == "__main__":
    main()
