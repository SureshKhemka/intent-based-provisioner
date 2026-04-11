import json
import os
import time
from datetime import datetime

from classify import load_config, build_system_prompt, classify_intent

CONFIG_DIR  = os.path.join(os.path.dirname(__file__), "config")
TESTS_DIR   = os.path.join(os.path.dirname(__file__), "tests")
RESULTS_DIR = os.path.join(TESTS_DIR, "results")
TEST_FILE   = os.path.join(TESTS_DIR, "test_cases.json")


def score_intent_accuracy(expected: list, actual_intents: list) -> dict:
    actual_names = set(i["intent"] for i in actual_intents)
    expected_set = set(expected)
    correct      = actual_names == expected_set
    missing      = list(expected_set - actual_names)
    extra        = list(actual_names - expected_set)
    return {"correct": correct, "missing": missing, "extra": extra}


def score_compound_detection(expected_compound: bool, actual_compound: bool) -> bool:
    return expected_compound == actual_compound


def score_param_extraction(actual_intents: list) -> dict:
    """
    Full param scoring requires expected_params in the test case.
    We flag intents that returned empty params as a warning.
    """
    empty_params = [
        i["intent"] for i in actual_intents
        if not i.get("params")
    ]
    return {
        "intents_with_params":  len(actual_intents) - len(empty_params),
        "intents_empty_params": empty_params
    }


def classify(utterance: str, system_prompt: str, defaults: dict,
             confirmation: dict, model_config: dict) -> tuple:
    start  = time.time()
    result = classify_intent(utterance, system_prompt, defaults, confirmation, model_config)
    return result, result.get("latency_s", round(time.time() - start, 2))


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    taxonomy, defaults, confirmation, model_config = load_config()
    system_prompt = build_system_prompt(taxonomy)
    model_name    = model_config.get("model", "qwen3:4b")

    with open(TEST_FILE) as f:
        data = json.load(f)

    all_cases  = data["test_cases"]
    cases      = [c for c in all_cases if c.get("reviewed", False)]
    unreviewed = len(all_cases) - len(cases)

    if not cases:
        print("\n  ⚠ No reviewed test cases found.")
        print("  Open tests/test_cases.json, verify each case,")
        print("  and set 'reviewed': true on cases you've confirmed.")
        return

    print("=" * 60)
    print("  Evaluation Run")
    print(f"  Model     : {model_name}")
    print(f"  Running   : {len(cases)} reviewed cases")
    print(f"  Skipped   : {unreviewed} unreviewed")
    print("=" * 60)

    results          = []
    latencies        = []
    intent_correct   = 0
    compound_correct = 0
    compound_total   = 0
    failures         = []
    errors           = []

    # Per-intent tracking
    per_intent = {}

    for idx, case in enumerate(cases, 1):
        utterance   = case["utterance"]
        expected    = case["expected_intents"]
        is_compound = case.get("compound", False)

        print(f"  [{idx:03d}/{len(cases)}] {utterance[:55]:<55}", end="\r")

        try:
            result, latency = classify(utterance, system_prompt, defaults, confirmation, model_config)
            actual_intents  = result.get("intents", [])
            actual_compound = result.get("compound", False)

            intent_score   = score_intent_accuracy(expected, actual_intents)
            compound_score = score_compound_detection(is_compound, actual_compound)
            param_score    = score_param_extraction(actual_intents)

            if intent_score["correct"]:
                intent_correct += 1

            if is_compound:
                compound_total += 1
                if compound_score:
                    compound_correct += 1

            # Per-intent breakdown
            for exp_intent in expected:
                if exp_intent not in per_intent:
                    per_intent[exp_intent] = {"total": 0, "correct": 0}
                per_intent[exp_intent]["total"] += 1
                if intent_score["correct"]:
                    per_intent[exp_intent]["correct"] += 1

            latencies.append(latency)

            result_record = {
                "id":                case["id"],
                "utterance":         utterance,
                "expected_intents":  expected,
                "actual_intents":    [i["intent"] for i in actual_intents],
                "intent_correct":    intent_score["correct"],
                "missing_intents":   intent_score["missing"],
                "extra_intents":     intent_score["extra"],
                "compound_expected": is_compound,
                "compound_actual":   actual_compound,
                "compound_correct":  compound_score,
                "param_score":       param_score,
                "latency_s":         latency
            }
            results.append(result_record)

            if not intent_score["correct"]:
                failures.append(result_record)

        except Exception as e:
            errors.append({"id": case["id"], "utterance": utterance, "error": str(e)})

    # ── Summary ───────────────────────────────────────────────────────────────
    total        = len(cases)
    intent_acc   = round((intent_correct / total) * 100, 1) if total else 0
    compound_acc = round((compound_correct / compound_total) * 100, 1) if compound_total else None
    avg_latency  = round(sum(latencies) / len(latencies), 2) if latencies else 0
    p95_latency  = round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if latencies else 0

    print(" " * 65)  # clear the \r line
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Intent accuracy     : {intent_acc}%  ({intent_correct}/{total} correct)")
    if compound_acc is not None:
        print(f"  Compound detection  : {compound_acc}%  ({compound_correct}/{compound_total} correct)")
    print(f"  Avg latency         : {avg_latency}s")
    print(f"  P95 latency         : {p95_latency}s")
    print(f"  Failures            : {len(failures)}")
    print(f"  Errors              : {len(errors)}")

    # ── Per-intent breakdown ──────────────────────────────────────────────────
    if per_intent:
        print(f"\n  ── Per-intent accuracy ─────────────────────────────")
        for intent_name in sorted(per_intent.keys()):
            d       = per_intent[intent_name]
            pct     = round((d["correct"] / d["total"]) * 100) if d["total"] else 0
            bar     = "█" * (pct // 10) + "░" * (10 - pct // 10)
            flag    = "  ⚠" if pct < 80 else ""
            print(f"  {intent_name:<30} [{bar}] {pct:3d}%  ({d['correct']}/{d['total']}){flag}")

    # ── Failures ──────────────────────────────────────────────────────────────
    if failures:
        print(f"\n  ── Failures ─────────────────────────────────────────")
        for f in failures:
            print(f"\n  Input    : {f['utterance']}")
            print(f"  Expected : {f['expected_intents']}")
            print(f"  Got      : {f['actual_intents']}")
            if f["missing_intents"]:
                print(f"  Missing  : {f['missing_intents']}")
            if f["extra_intents"]:
                print(f"  Extra    : {f['extra_intents']}")

    if errors:
        print(f"\n  ── Errors ───────────────────────────────────────────")
        for e in errors:
            print(f"  {e['id']}: {e['error']}")

    # ── Save report ───────────────────────────────────────────────────────────
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(RESULTS_DIR, f"report_{timestamp}.json")

    with open(report_file, "w") as f:
        json.dump({
            "summary": {
                "run_at":             datetime.now().isoformat(),
                "total_cases":        total,
                "unreviewed_skipped": unreviewed,
                "intent_accuracy":    f"{intent_acc}%",
                "compound_accuracy":  f"{compound_acc}%" if compound_acc else "n/a",
                "avg_latency_s":      avg_latency,
                "p95_latency_s":      p95_latency,
                "failures":           len(failures),
                "errors":             len(errors)
            },
            "per_intent": per_intent,
            "results":    results
        }, f, indent=2)

    print(f"\n  ✓ Report saved → tests/results/report_{timestamp}.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
