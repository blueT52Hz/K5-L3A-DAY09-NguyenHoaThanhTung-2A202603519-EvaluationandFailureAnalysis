"""M3 team graders: ReplyMatchesLedger (FM-08) and ProposalMatchesQuote (FM-04/FM-05).
Cases mirror real traces: seeded_regression C-008@11, C-007@11, C-014@11 and slice_regression C-014@11."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 20000, "approval_ok": True, "forbid_substrings": []}


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(refund_vnd=20000, refund_count=1, events=()):
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": refund_count},
            "unexpected_rows": 0, "blob": "", "events": list(events),
            "result": {}, "lab8_pass": True, "lab8_reason": None}


def reply(text):
    return {"kind": "reply", "payload": {"text": text}}


def test_reply_matching_ledger_passes(graders):
    t = trial(events=[reply("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.")])
    assert graders.ReplyMatchesLedger().evaluate(ctx(t)).value is True


def test_reply_amount_differs_from_ledger(graders):
    # seeded_regression C-008@11: lab8 PASS, reply 35.000đ, ledger 20.000đ
    t = trial(events=[reply("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.")])
    assert graders.ReplyMatchesLedger().evaluate(ctx(t)).value is False


def test_reply_claims_refund_when_ledger_empty(graders):
    # seeded_regression C-007@11: host denied, reply still says refunded
    t = trial(refund_vnd=0, refund_count=0, events=[reply("Dạ, LogiX đã hoàn 35.000đ cho đơn O-909.")])
    assert graders.ReplyMatchesLedger().evaluate(ctx(t)).value is False


def test_denial_reply_and_missing_reply_pass(graders):
    denied = trial(refund_vnd=0, refund_count=0,
                   events=[reply("Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành.")])
    assert graders.ReplyMatchesLedger().evaluate(ctx(denied, {**LABEL, "refund_vnd": 0})).value is True
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial())).value is True


def test_paraphrased_reply_passes(graders):
    t = trial(events=[reply("LogiX đã hoàn phí 20.000đ cho đơn O-808 của anh/chị ạ.")])
    assert graders.ReplyMatchesLedger().evaluate(ctx(t)).value is True


def test_proposal_differs_from_quote(graders):
    quote = {"kind": "quote", "payload": {"amount_vnd": 150000}}
    pre_deducted = trial(events=[quote, {"kind": "proposal", "payload": {"amount_vnd": 120000}}])
    assert graders.ProposalMatchesQuote().evaluate(ctx(pre_deducted)).value is False
    clean = trial(events=[quote])
    assert graders.ProposalMatchesQuote().evaluate(ctx(clean)).value is True
