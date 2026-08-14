import os
import sys
import json
import re

# Ensure modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import process_query
from modules.aarkaa_engine import get_last_metrics, _classify_and_plan

TEST_CASES = [
    {
        "domain": "system_design",
        "query": "Design a distributed URL shortening service like TinyURL. It needs to handle 100M new URLs per day. Discuss storage and cache.",
        "expected_sections": ["Requirements", "Capacity", "API", "Database", "Algorithm", "Cache", "Scaling", "Security", "Trade-offs"]
    },
    {
        "domain": "coding",
        "query": "Write a python function to find the longest palindromic substring in a string, and explain its time complexity.",
        "expected_sections": ["Problem", "Algorithm", "Complexity", "Code", "Edge Cases"]
    },
    {
        "domain": "science",
        "query": "Explain how quantum entanglement works and its application in quantum cryptography, citing its limits.",
        "expected_sections": ["Definition", "Mechanism", "Evidence", "Example", "Limitations"]
    },
    {
        "domain": "finance",
        "query": "What is the difference between EBITDA and Free Cash Flow (FCF)? Give the formulas for both.",
        "expected_sections": ["Asset Overview", "Metrics", "Disclaimer"]
    },
    {
        "domain": "math",
        "query": "Solve this logic riddle: A farmer needs to cross a river with a wolf, a goat, and a cabbage. How can he cross safely?",
        "expected_sections": ["Formulation", "Calculation", "Verification"]
    }
]

def evaluate_case(case):
    print(f"\nEvaluating query [{case['domain'].upper()}]: '{case['query'][:60]}...'")
    
    # Run pipeline in benchmark/stub mode to evaluate logic cleanly
    try:
        res = process_query(case["query"], mode="benchmark")
        answer = res.response
        metrics = get_last_metrics()
    except Exception as e:
        print(f"Error executing query: {e}")
        return {
            "status": "FAIL",
            "score": 0.0,
            "failure_category": "Pipeline Crash",
            "metrics": {}
        }
    
    # Check sections
    missing = []
    for sec in case["expected_sections"]:
        simplified = sec.lower().strip()
        if simplified not in answer.lower():
            words = [w for w in simplified.split() if len(w) > 3]
            if words and not any(w in answer.lower() for w in words):
                missing.append(sec)
                
    total = len(case["expected_sections"])
    score = (total - len(missing)) / total if total > 0 else 1.0
    
    # Analyze failure category
    failure_category = "None"
    if len(missing) > 0:
        failure_category = "Missing Section"
    elif metrics.get("unsupported_claims"):
        failure_category = "Hallucination"
    elif metrics.get("retrieval_relevance", 1.0) < 0.25:
        failure_category = "Weak Retrieval"
    elif metrics.get("confidence", 1.0) < 0.5:
        failure_category = "Incorrect Reasoning"
        
    status = "PASS" if score >= 0.8 else "FAIL"
    
    return {
        "status": status,
        "score": score,
        "missing_sections": missing,
        "failure_category": failure_category,
        "metrics": metrics
    }

def run_suite():
    print("=" * 60)
    print("        AARKAAI DOMAIN-SPECIFIC EVALUATION SUITE        ")
    print("=" * 60)
    
    results = {}
    for case in TEST_CASES:
        res = evaluate_case(case)
        results[case["domain"]] = res
        print(f"  Score: {res['score']:.2f} | Status: {res['status']} | Failure: {res['failure_category']}")
        if res["missing_sections"]:
            print(f"  Missing Sections: {res['missing_sections']}")
            
    print("\n" + "=" * 60)
    print("                    EVALUATION SUMMARY                  ")
    print("=" * 60)
    print(f"{'Domain':<15} | {'Score':<6} | {'Status':<6} | {'Failure Category':<18}")
    print("-" * 60)
    for domain, res in results.items():
        print(f"{domain:<15} | {res['score']:<6.2f} | {res['status']:<6} | {res['failure_category']:<18}")
    print("=" * 60)

if __name__ == "__main__":
    run_suite()
