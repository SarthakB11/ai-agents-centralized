"""
Benchmark Runner — Evaluate agent quality against a dataset.

Usage:
  python -m evaluation.benchmark --dataset evaluation/eval_dataset.json

The runner:
1. Loads the eval dataset
2. Runs each test case through the agent
3. Computes accuracy, latency, cost, and token metrics
4. Writes a report to evaluation/benchmark_report.json
"""

import json
import time
import argparse
import logging
from typing import List, Dict

from app.agent import Agent
from evaluation.metrics import accuracy_score, fuzzy_accuracy, latency_stats, cost_stats, token_efficiency

logger = logging.getLogger(__name__)


def load_dataset(path: str) -> List[Dict]:
    """Load evaluation dataset from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("test_cases", data) if isinstance(data, dict) else data


def run_benchmark(dataset_path: str, output_path: str = "evaluation/benchmark_report.json"):
    """Run the full benchmark suite."""
    agent = Agent()
    test_cases = load_dataset(dataset_path)

    print(f"🔬 Running benchmark with {len(test_cases)} test cases...\n")

    predictions = []
    ground_truths = []
    latencies = []
    costs = []
    tokens = []
    results = []

    for i, tc in enumerate(test_cases):
        input_text = tc.get("input", "")
        expected = tc.get("expected_output", "")

        start = time.time()
        try:
            response = agent.handle_request({
                "input": input_text,
                "session_id": f"eval-{i}",
                "request_id": f"eval-{i}",
            })
            output = response.get("output", "")
            cost = response.get("metadata", {}).get("cost_estimate", 0)
            tok_in = response.get("metadata", {}).get("tokens_input", 0)
            tok_out = response.get("metadata", {}).get("tokens_output", 0)
            status = "success"
        except Exception as e:
            output = ""
            cost = 0
            tok_in = tok_out = 0
            status = f"error: {e}"

        elapsed_ms = (time.time() - start) * 1000

        predictions.append(output)
        ground_truths.append(expected)
        latencies.append(elapsed_ms)
        costs.append(cost)
        tokens.append({"input": tok_in, "output": tok_out})

        result_entry = {
            "case_id": i,
            "input": input_text[:100],
            "expected": expected[:100],
            "output": output[:100],
            "latency_ms": round(elapsed_ms, 2),
            "status": status,
        }
        results.append(result_entry)
        print(f"  [{i+1}/{len(test_cases)}] {status} — {elapsed_ms:.0f}ms")

    # Compute metrics
    report = {
        "summary": {
            "total_cases": len(test_cases),
            "accuracy": accuracy_score(predictions, ground_truths),
            "fuzzy_accuracy": fuzzy_accuracy(predictions, ground_truths),
            "latency": latency_stats(latencies),
            "cost": cost_stats(costs),
            "tokens": token_efficiency(tokens),
        },
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Benchmark Report:")
    print(f"   Accuracy:       {report['summary']['accuracy']['score']:.1%}")
    print(f"   Fuzzy Accuracy: {report['summary']['fuzzy_accuracy']['score']:.1%}")
    print(f"   Mean Latency:   {report['summary']['latency']['mean']:.0f}ms")
    print(f"   Total Cost:     ${report['summary']['cost']['total']:.4f}")
    print(f"   Total Tokens:   {report['summary']['tokens']['total_tokens']}")
    print(f"\n   Report saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run agent benchmark")
    parser.add_argument("--dataset", default="evaluation/eval_dataset.json", help="Path to eval dataset")
    parser.add_argument("--output", default="evaluation/benchmark_report.json", help="Report output path")
    args = parser.parse_args()

    run_benchmark(args.dataset, args.output)
