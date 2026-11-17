# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case: seeded_regression C-002@11

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, report `reports/eval_seeded_regression.json`, run ID `E-seeded_regression-20261117-dbb3` (eval set `dbb3938f6253`), item E-002 |
| Triệu chứng | Grader Lab 8 FAIL `status resolved != denied`. `db_fact_kept` và `refund_amount_correct` fail. Ledger ghi `refund_vnd = 20000`, `refund_count = 1`; nhãn `0` / `0`, status `denied`. Reply "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." khớp ledger nhưng cả hai đều sai so với nhãn |
| Bước sai đầu tiên | Event #3 `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | #1 `handoff`: task `check_applicable_policy`, `principal_scope: owner_order_only`, đúng. #2 `investigator`: `lookup_order` visible, đọc đúng DB `O-202 delay_days = 2`. Tới #3, agent thay số 2 của DB bằng số 5 trong ticket ("giao trễ 5 ngày"). #4 `quote` 20.000 (`SHIP-LATE-03`, ngưỡng 3 ngày) chỉ là hệ quả: phép tính đúng trên đầu vào sai. #5 `refund_history` = 0, công tắc `pre_deducted` không đổi gì. #6 `reply` khớp ledger |
| Failure mode | FM-03 ticket_trust (tin ticket hơn DB) |
| Đối chứng | `fixed C-002@11`: không có `model_override`; #3 `quote {"amount_vnd": 0, "reason": "no_entitlement"}`; #4 reply "chưa đủ điều kiện hoàn"; ledger 0, status denied, grader Lab 8 PASS |
| Regression test | `src/tests/test_lab9_trace_case_c002.py`: chạy thật hai shape trên store tạm. `test_seeded_regression_c002_first_wrong_step_is_model_override` assert event #3 là `model_override {"delay_days": 5}`, ledger 20.000, và `DbFactKept` + `RefundAmountCorrect` cùng False. `test_fixed_c002_keeps_db_fact` assert không có override, ledger 0, status denied, hai grader True. Ngoài ra item E-002 trong eval set có `provenance.from_trace = "seeded_regression C-002@11"`, nên mọi lần chạy gate đều chấm lại case này. Đã thấy fail trên `seeded_regression` và pass trên `fixed` |
| Chưa chắc chắn | Trace không có event riêng cho `issue_refund`; việc host chấp nhận ghi 20.000 (approval A-002 còn hạn, duyệt đúng 20.000) chỉ suy ra từ ledger. Swarm gốc cũng mắc lỗi này nhưng chỉ ở `seed % 5 == 0` (C-002@55); trace không cho biết agent thật có lý do gì để tin ticket ở seed đó. Biến thể `quiet_override` cùng lỗi nhưng không ghi event #3: khi đó chỉ `refund_amount_correct` (đọc ledger) bắt được, `db_fact_kept` thì không |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
