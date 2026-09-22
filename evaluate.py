#!/usr/bin/env python3
"""Score a predictions file against multistep_decisions. Standard library only.

Predictions: one JSON object per line.

    {"id": "msd-arith-01", "answer": "2352"}
    {"id": "msd-cal-02", "answer": "yes", "probs": {"yes": 0.91, "no": 0.09}}

`answer` must be one of the item's `labels`. `probs` is optional; when every
prediction carries one, the report adds Brier score and expected calibration
error. A missing or invalid prediction counts as wrong.

Usage:
    python3 evaluate.py predictions.jsonl
    python3 evaluate.py predictions.jsonl --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "multistep_decisions.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def ece(pairs: list[tuple[float, bool]], bins: int = 10) -> float:
    """Expected calibration error on the top-label confidence, equal-width bins."""
    buckets: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for conf, ok in pairs:
        buckets[min(bins - 1, int(conf * bins))].append((conf, ok))
    n = len(pairs)
    return sum(
        len(b) / n * abs(sum(c for c, _ in b) / len(b) - sum(o for _, o in b) / len(b))
        for b in buckets.values()
    )


def evaluate(items: list[dict], preds: dict[str, dict]) -> dict:
    by_family: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    correct = invalid = missing = 0
    calib: list[tuple[float, bool]] = []
    brier: list[float] = []
    all_probs = True

    for it in items:
        p = preds.get(it["id"])
        ok = False
        if p is None:
            missing += 1
        elif str(p.get("answer")) not in it["labels"]:
            invalid += 1
        else:
            ok = str(p["answer"]) == str(it["expected"])
        correct += ok
        for table, key in ((by_family, it["family"]), (by_type, it["question"]["type"])):
            table[key][0] += ok
            table[key][1] += 1

        probs = (p or {}).get("probs")
        if isinstance(probs, dict) and set(map(str, probs)) == set(it["labels"]):
            top = max(probs, key=probs.get)
            calib.append((float(probs[top]), str(top) == str(it["expected"])))
            brier.append(sum((float(probs[k]) - (str(k) == str(it["expected"]))) ** 2 for k in probs))
        else:
            all_probs = False

    n = len(items)
    report = {
        "n": n,
        "correct": correct,
        "accuracy": correct / n,
        "missing": missing,
        "invalid": invalid,
        "by_family": {k: {"correct": c, "n": t, "accuracy": c / t} for k, (c, t) in sorted(by_family.items())},
        "by_type": {k: {"correct": c, "n": t, "accuracy": c / t} for k, (c, t) in sorted(by_type.items())},
    }
    if all_probs and calib:
        report["brier"] = sum(brier) / len(brier)
        report["ece"] = ece(calib)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("predictions", type=Path)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args()

    items = load_jsonl(args.data)
    preds = {p["id"]: p for p in load_jsonl(args.predictions)}
    unknown = sorted(set(preds) - {it["id"] for it in items})
    if unknown:
        print(f"warning: {len(unknown)} predictions for unknown ids, ignored (e.g. {unknown[0]})", file=sys.stderr)

    r = evaluate(items, preds)
    if args.json:
        print(json.dumps(r, indent=2))
        return 0

    print(f"accuracy  {r['accuracy']:.1%}  ({r['correct']} / {r['n']})")
    if r["missing"] or r["invalid"]:
        print(f"          {r['missing']} missing, {r['invalid']} invalid (counted wrong)")
    if "ece" in r:
        print(f"brier     {r['brier']:.3f}")
        print(f"ece       {r['ece']:.3f}")
    print("\nby family")
    for k, v in r["by_family"].items():
        print(f"  {k:<26}{v['correct']:>3} / {v['n']:<3} {v['accuracy']:6.1%}")
    print("\nby type")
    for k, v in r["by_type"].items():
        print(f"  {k:<26}{v['correct']:>3} / {v['n']:<3} {v['accuracy']:6.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
