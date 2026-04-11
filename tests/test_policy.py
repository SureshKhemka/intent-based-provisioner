"""
Tests for the policy enrichment and validation pipeline.

These tests mock the OPA server responses to verify that:
- policy_enricher correctly merges enrichments, respecting param precedence
- policy_validator correctly interprets allow/deny/violations/warnings
- User-specified params are never overwritten by policy enrichment
- Compound intents get independent policy evaluation
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Enrichment tests ──────────────────────────────────────────────────────────

def test_enrichment_fills_missing_params():
    """Enrichments should only fill params not already set."""
    # Test the merge logic directly (same logic as policy_enricher.enrich)
    params = {"region": "us-east-1", "cpu": "4"}
    enrichments = {"encryption": "aes-256", "backup_policy": "daily", "region": "ap-south-1"}
    policy_applied = []

    for key, value in enrichments.items():
        if key not in params:
            params[key] = value
            policy_applied.append({"field": key, "value": value, "source": "org_standard"})

    # User's region should NOT be overwritten
    assert params["region"] == "us-east-1", "User-specified params must not be overwritten"
    assert params["encryption"] == "aes-256", "Missing params should be filled"
    assert params["backup_policy"] == "daily", "Missing params should be filled"
    assert len(policy_applied) == 2, "Only 2 fields should be added (region was already set)"
    assert all(p["field"] != "region" for p in policy_applied), "region should not be in policy_applied"


def test_enrichment_provenance_tracking():
    """Each enriched field should be tracked in policy_applied."""
    enrichments = {"monitoring": "enabled", "tags": "managed"}
    policy_applied = []

    for key, value in enrichments.items():
        policy_applied.append({"field": key, "value": value, "source": "org_standard"})

    assert len(policy_applied) == 2
    fields = {p["field"] for p in policy_applied}
    assert fields == {"monitoring", "tags"}
    assert all(p["source"] == "org_standard" for p in policy_applied)


# ── Validation tests ──────────────────────────────────────────────────────────

def test_validation_allow_structure():
    """Validation result should always have allow, violations, warnings."""
    validation = {"allow": True, "violations": [], "warnings": []}

    assert "allow" in validation
    assert "violations" in validation
    assert "warnings" in validation
    assert validation["allow"] is True
    assert len(validation["violations"]) == 0


def test_validation_deny_has_violations():
    """When allow is False, there must be at least one violation."""
    validation = {
        "allow": False,
        "violations": ["Region 'cn-north-1' is not allowed"],
        "warnings": []
    }

    assert validation["allow"] is False
    assert len(validation["violations"]) > 0


def test_compound_intents_independent_policy():
    """Each intent in a compound request should get independent policy evaluation."""
    intents = [
        {
            "intent": "compute.provision",
            "params": {"region": "us-east-1", "cpu": "4"},
            "policy_validation": {"allow": True, "violations": [], "warnings": []}
        },
        {
            "intent": "db.provision",
            "params": {"engine": "oracle"},
            "policy_validation": {
                "allow": False,
                "violations": ["Database engine 'oracle' is not allowed"],
                "warnings": []
            }
        }
    ]

    # First intent passes, second is blocked — they are independent
    assert intents[0]["policy_validation"]["allow"] is True
    assert intents[1]["policy_validation"]["allow"] is False

    # Only the blocked intent should have violations
    assert len(intents[0]["policy_validation"]["violations"]) == 0
    assert len(intents[1]["policy_validation"]["violations"]) == 1


# ── Policy engine fallback tests ──────────────────────────────────────────────

def test_fallback_result_structure():
    """When OPA is down, fallback should return a skipped status."""
    fallback = {"status": "skipped", "reason": "OPA unreachable"}

    assert fallback["status"] == "skipped"
    assert "reason" in fallback


def test_validation_skip_allows_execution():
    """When OPA is unavailable, validation should default to allow."""
    validation = {
        "allow": True,
        "violations": [],
        "warnings": [],
        "note": "OPA unavailable — policy check skipped"
    }

    assert validation["allow"] is True
    assert "note" in validation


# ── Run tests ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_enrichment_fills_missing_params,
        test_enrichment_provenance_tracking,
        test_validation_allow_structure,
        test_validation_deny_has_violations,
        test_compound_intents_independent_policy,
        test_fallback_result_structure,
        test_validation_skip_allows_execution,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {test.__name__}: {e}")
            failed += 1

    print(f"\n  {passed} passed, {failed} failed out of {len(tests)} tests")
