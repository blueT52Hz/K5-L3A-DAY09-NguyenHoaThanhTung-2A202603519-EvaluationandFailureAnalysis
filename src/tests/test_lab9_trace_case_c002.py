"""Regression test for docs/trace_case.md: seeded_regression C-002@11, first wrong step = event #3
model_override (FM-03). Runs the real shapes on a temp store; graders must fail the buggy variant and
pass the fixed one on the same claim@seed. Run from src/."""
import pytest

pytestmark = pytest.mark.student


def _grade(shape: str):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9 import graders
    from lab9.trace_case import investigate

    case = investigate(shape, "C-002", 11)
    ctx = EvaluatorContext(name=f"{shape}-C-002@11", inputs={}, metadata=None, expected_output=case["label"],
                           output=case["trial"], duration=0.0, _span_tree=None, attributes={}, metrics={})
    return case["trial"], {
        "db_fact_kept": graders.DbFactKept().evaluate(ctx).value,
        "refund_amount_correct": graders.RefundAmountCorrect().evaluate(ctx).value,
    }


def test_seeded_regression_c002_first_wrong_step_is_model_override():
    trial, verdict = _grade("seeded_regression")
    kinds = [e.get("kind") for e in trial["events"]]
    assert kinds.index("model_override") == 2            # event #3 (1-based), after handoff + investigator
    assert trial["events"][2]["payload"] == {"delay_days": 5}
    assert trial["snapshot"]["refund_vnd"] == 20000      # label says 0
    assert verdict == {"db_fact_kept": False, "refund_amount_correct": False}


def test_fixed_c002_keeps_db_fact():
    trial, verdict = _grade("fixed")
    assert "model_override" not in [e.get("kind") for e in trial["events"]]
    assert trial["snapshot"]["refund_vnd"] == 0
    assert trial["result"]["status"] == "denied"
    assert verdict == {"db_fact_kept": True, "refund_amount_correct": True}
