"""
Evaluation Metrics — Scoring functions for agent quality.

Used by the benchmark runner to measure accuracy, latency,
cost efficiency, and output quality.
"""

from typing import List, Dict, Optional
import time


def accuracy_score(predictions: List[str], ground_truths: List[str]) -> Dict:
    """
    Exact match accuracy between predictions and ground truths.
    """
    if len(predictions) != len(ground_truths):
        return {"error": "Predictions and ground truths must be same length"}

    correct = sum(1 for p, gt in zip(predictions, ground_truths) if p.strip().lower() == gt.strip().lower())
    total = len(predictions)

    return {
        "metric": "accuracy",
        "score": round(correct / total, 4) if total > 0 else 0,
        "correct": correct,
        "total": total,
    }


def fuzzy_accuracy(predictions: List[str], ground_truths: List[str], threshold: float = 0.8) -> Dict:
    """
    Fuzzy match accuracy using sequence matching.
    Good for cases where output phrasing may vary.
    """
    from difflib import SequenceMatcher

    matches = 0
    scores = []
    for p, gt in zip(predictions, ground_truths):
        ratio = SequenceMatcher(None, p.strip().lower(), gt.strip().lower()).ratio()
        scores.append(ratio)
        if ratio >= threshold:
            matches += 1

    return {
        "metric": "fuzzy_accuracy",
        "score": round(matches / len(predictions), 4) if predictions else 0,
        "matches": matches,
        "total": len(predictions),
        "avg_similarity": round(sum(scores) / len(scores), 4) if scores else 0,
        "threshold": threshold,
    }


def latency_stats(latencies_ms: List[float]) -> Dict:
    """Compute latency statistics."""
    if not latencies_ms:
        return {"metric": "latency", "error": "No data"}

    sorted_lat = sorted(latencies_ms)
    return {
        "metric": "latency_ms",
        "mean": round(sum(sorted_lat) / len(sorted_lat), 2),
        "median": round(sorted_lat[len(sorted_lat) // 2], 2),
        "p95": round(sorted_lat[int(len(sorted_lat) * 0.95)], 2),
        "p99": round(sorted_lat[int(len(sorted_lat) * 0.99)], 2),
        "min": round(sorted_lat[0], 2),
        "max": round(sorted_lat[-1], 2),
        "count": len(sorted_lat),
    }


def cost_stats(costs: List[float]) -> Dict:
    """Compute cost statistics."""
    if not costs:
        return {"metric": "cost", "error": "No data"}

    return {
        "metric": "cost_usd",
        "total": round(sum(costs), 6),
        "mean_per_request": round(sum(costs) / len(costs), 6),
        "max": round(max(costs), 6),
        "count": len(costs),
    }


def token_efficiency(token_counts: List[Dict]) -> Dict:
    """
    Analyze token usage efficiency.

    token_counts: list of dicts with 'input' and 'output' keys
    """
    total_in = sum(t.get("input", 0) for t in token_counts)
    total_out = sum(t.get("output", 0) for t in token_counts)
    total = total_in + total_out

    return {
        "metric": "token_efficiency",
        "total_tokens": total,
        "total_input": total_in,
        "total_output": total_out,
        "avg_tokens_per_request": round(total / len(token_counts), 1) if token_counts else 0,
        "io_ratio": round(total_out / total_in, 2) if total_in > 0 else 0,
    }
