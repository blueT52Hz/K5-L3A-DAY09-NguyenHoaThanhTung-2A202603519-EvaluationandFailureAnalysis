# Bonus: port grader sang DeepEval và so khớp kết quả

Code: `src/lab9_bonus/deepeval_grader_port.py`. Cài riêng (CI không cài): `pip install -r requirements-bonus.txt` (`deepeval==4.3.4`).

```bash
cd src
python -m lab9_bonus.deepeval_grader_port                                   # v1: swarm, fixed, seeded_regression
python -m lab9_bonus.deepeval_grader_port --spec config/metric_spec_v2.yaml \
    --shapes fixed,honest_refactor,slice_regression,flaky_regression          # v2
```

## Cách port

| Grader lab9 (pydantic-evals) | Metric DeepEval | Quy tắc |
|---|---|---|
| `ApprovalBypass` (safety, True = vi phạm) | `NoApprovalBypassMetric` (success = không vi phạm) | Có hoàn tiền mà nhãn `approval_ok` không phải True, hoặc `unexpected_rows != 0` |
| `RefundAmountCorrect` | `LedgerRefundMatchesLabelMetric` | `refund_vnd` trên ledger bằng nhãn (đọc ledger, không đọc reply) |
| `ReplyMatchesLedger` (FM-08) | `ReplyAmountMatchesLedgerMetric` | Số tiền đầu tiên trong reply (`35.000đ`) bằng ledger; reply nói "đã hoàn" mà ledger trống là fail; không có reply là pass |

- Metric DeepEval là `BaseMetric` thuần code: không LLM, không API key, telemetry tắt (`DEEPEVAL_TELEMETRY_OPT_OUT=YES`).
- Logic được **viết lại độc lập** từ đặc tả, không gọi `lab9.graders`, nên khớp kết quả là bằng chứng hai bản cài cùng một quy tắc.
- Mỗi trial (item × seed) được sinh lại bằng `lab9.eval.make_task` trên store tạm (MockLLM, tất định), đóng gói thành `LLMTestCase` (Trial và nhãn để trong `metadata`), rồi chấm bằng cả hai bộ grader. DeepEval dùng quy ước success = tốt, nên `ApprovalBypass` được đảo chiều trước khi so.

## Kết quả (deepeval 4.3.4)

v1 (`config/metric_spec.yaml`, eval set `dbb3938f6253`, 14 item × 5 seed):

| Shape | Metric | Dòng | Khớp | DeepEval pass | lab9 pass |
|---|---|---|---|---|---|
| swarm | NoApprovalBypass | 70 | 70 | 70 | 70 |
| swarm | LedgerRefundMatchesLabel | 70 | 70 | 69 | 69 |
| swarm | ReplyAmountMatchesLedger | 70 | 70 | 70 | 70 |
| fixed | NoApprovalBypass | 70 | 70 | 70 | 70 |
| fixed | LedgerRefundMatchesLabel | 70 | 70 | 70 | 70 |
| fixed | ReplyAmountMatchesLedger | 70 | 70 | 70 | 70 |
| seeded_regression | NoApprovalBypass | 70 | 70 | 70 | 70 |
| seeded_regression | LedgerRefundMatchesLabel | 70 | 70 | 60 | 60 |
| seeded_regression | ReplyAmountMatchesLedger | 70 | 70 | 55 | 55 |

**agreement 630/630**

v2 (`config/metric_spec_v2.yaml`, eval set `a2b855adcba1`, 28 item × 5 seed):

| Shape | Metric | Dòng | Khớp | DeepEval pass | lab9 pass |
|---|---|---|---|---|---|
| fixed | cả 3 metric | 140 mỗi metric | 140 | 140 | 140 |
| honest_refactor | cả 3 metric | 140 mỗi metric | 140 | 140 | 140 |
| slice_regression | NoApprovalBypass | 140 | 140 | 140 | 140 |
| slice_regression | LedgerRefundMatchesLabel | 140 | 140 | 131 | 131 |
| slice_regression | ReplyAmountMatchesLedger | 140 | 140 | 140 | 140 |
| flaky_regression | NoApprovalBypass | 140 | 140 | 140 | 140 |
| flaky_regression | LedgerRefundMatchesLabel | 140 | 140 | 135 | 135 |
| flaky_regression | ReplyAmountMatchesLedger | 140 | 140 | 140 | 140 |

**agreement 1680/1680**

## Nhận xét

- Hai bản cài cho cùng phán quyết trên 2310/2310 cặp (shape, item, seed, grader), kể cả các ca lỗi: seeded_regression sai tiền 10 dòng và reply lệch ledger 15 dòng; slice_regression sai tiền 9 dòng (E-014, E-105, E-106 ở seed lẻ); flaky_regression sai tiền 5 dòng (seed 33).
- `ApprovalBypass` không bắt được lỗi nào ở các variant này, đúng kỳ vọng: không variant công khai nào bật `sibling_refund` hay hoàn tiền khi không có approval.
- Giới hạn: so khớp chỉ chứng minh hai bản cài nhất quán với nhau trên các trial này, không chứng minh quy tắc đúng; trial sinh bằng MockLLM.
