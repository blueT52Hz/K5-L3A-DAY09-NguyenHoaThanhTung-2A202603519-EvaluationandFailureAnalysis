# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (exit 0) | **dùng** (non-blocking, chỉ cho tone) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** κ và R (exit 1) | **loại**, không dùng làm gate |

Ma trận nhầm lẫn (FAIL là lớp dương: judge có nhiệm vụ tìm lỗi):

| Tiêu chí | tp | fp | fn | tn | Tỉ lệ fail quan sát | Sau Rogan-Gladen |
|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 |

Lệnh:
```
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 25
```

## ≥5 case audit thủ công

### tone_ok (đủ 10 bất đồng)

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em", kết bằng "nha": quá suồng sã với khách khiếu nại. Rubric: thêm luật xưng hô bắt buộc "LogiX" - "anh/chị", cấm "em/bạn" và các tiểu từ "nha/nhé" |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ ... rồi nha." | PASS | FAIL | Người | Có "Dạ" nhưng xưng "bạn". Judge bị đánh lừa bởi từ mở đầu lịch sự. Cùng luật xưng hô như #1, kèm ví dụ phản chứng "Dạ + bạn" trong prompt |
| 3 | H-029 "Dạ, vui lòng chờ. ... không cần nhắn thêm." | PASS | FAIL | Người | Giọng ra lệnh, gạt khách. Judge chỉ thấy "Dạ, vui lòng". Rubric: đánh giá cả câu, cấm câu mệnh lệnh phủ định ("không cần...", "khỏi...") |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3-5 ngày ạ." | FAIL | PASS | Người | Ngắn nhưng đủ ý, lễ độ. Judge phạt vì "thiếu xin lỗi". Rubric: ghi rõ xin lỗi **không bắt buộc**, ngắn gọn không phải lỗi tone |
| 5 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | CS LogiX cho phép từ "refund". Rubric: thêm danh sách từ tiếng Anh được phép (refund, ship) |
| 6 | H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người | Hứa "sẽ hoàn thêm" ngoài kết quả hệ thống. Đây là lỗi **nội dung**, không phải tone: không sửa rubric tone, chuyển sang grader code đối chiếu reply với ledger (FM-08, M3) |
| 7 | H-070 "Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂" | PASS | FAIL | Người | Emoji cười trong ngữ cảnh khiếu nại. Rubric: cấm emoji trong reply CS |
| 8 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | Judge (theo ghi chú của người gán nhãn) | Ghi chú: người gán nhãn đọc nhầm ticket, **sửa nhãn người** thành FAIL. Lưu ý: về mặt tone câu này lễ độ, nên lý do FAIL là đúng/sai nội dung. Sửa nhãn và tách tiêu chí nội dung khỏi tone để lần sau không lẫn |
| 9 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ cho đơn O-233 ạ." | FAIL | PASS | Người | Lặp "Dạ" do lỗi gõ, không thô lỗ. Rubric: lỗi gõ nhẹ không làm FAIL tone |
| 10 | H-094 "Da, LogiX da hoan 40.000đ cho don O-341, xin loi vi su bat tien." | PASS | FAIL | Người | Mất dấu tiếng Việt (dịch máy), không chuyên nghiệp. Rubric: reply phải là tiếng Việt có dấu |

Tóm tắt: 6 fn (judge bỏ sót) có 2 nhóm: bị đánh lừa bởi từ mở đầu lịch sự (#1, #2, #3, #7, #10) và lỗi nội dung lọt vào tiêu chí tone (#6). 4 fp (judge báo nhầm) do rubric quá chặt về hình thức (#4, #5, #9) và 1 nhãn người sai (#8).

### helpful (21 bất đồng, đều là fn: judge PASS, người FAIL)

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." | PASS | FAIL | Người | Sai tiền: ledger ghi 40.000đ. Judge không thấy ledger nên không thể chấm đúng |
| 2 | HL-016 xin lỗi dài, "đã hoàn 55.000đ cho đơn O-404" | PASS | FAIL | Người | Sai tiền (ledger 35.000đ). Câu xin lỗi dài làm judge chấm "hữu ích": thiên vị độ dài/xin lỗi |
| 3 | HL-020 "Dạ, LogiX đã hoàn 90.000đ cho đơn O-303 ạ." | PASS | FAIL | Người | Sai tiền (ledger 120.000đ) |
| 4 | HL-043 xin lỗi lặp 2 lần, "đã hoàn 35.000đ cho đơn O-202" | PASS | FAIL | Người | Sai tiền (ledger 20.000đ), lặp câu xin lỗi |
| 5 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Sai xưng hô, không nói kết quả cụ thể. Cùng lỗi ở HL-091, HL-097 |
| 6 | HL-090 xin lỗi, "đã hoàn 155.000đ cho đơn O-233" | PASS | FAIL | Người | Sai tiền (ledger 120.000đ), vượt cả trần bồi thường 150.000đ |

Phân loại đủ 21 ca: **18 sai tiền** (HL-015, 016, 020, 028, 035, 041, 043, 053, 058, 062, 070, 072, 074, 087, 090, 096, 098, 100) và **3 sai xưng hô** (HL-047, 091, 097). Judge chỉ bắt được 9 ca lỗi hiển nhiên (lạc đề, giọng cụt, không hỏi mã đơn).

Sửa rubric:
- Bỏ "đúng số tiền" ra khỏi rubric judge. Kiểm số tiền bằng grader code so reply với ledger (metric FM-08 ở M3).
- Thêm luật xưng hô như rubric tone.
- Thêm ví dụ phản chứng: reply dài, nhiều câu xin lỗi nhưng sai số vẫn là FAIL.

## Kết luận

- **tone_ok: dùng được** (κ 0.757, P 0.857, R 0.80 đều trên sàn). Chỉ dùng làm metric **non-blocking** cho giọng văn. Sau Rogan-Gladen, tỉ lệ fail tone thật khoảng 0.30 (quan sát 0.28). Vẫn bỏ sót 6/30 lỗi (R = 0.8), nên không giao cho judge những việc nặng như tiền hay approval.
- **helpful: loại, không được dùng làm gate.** Ma trận tp 9, fp 0, fn 21, tn 70: recall 0.30 nghĩa là judge **bỏ sót 70% reply không hữu ích**. κ 0.375 dưới sàn 0.6. Precision 1.0 không cứu được: một judge gần như luôn nói PASS thì không bao giờ báo nhầm, nhưng cũng không chặn được gì. Nguyên nhân gốc: 18/21 lỗi là sai tiền, và judge chỉ đọc reply, **không thấy ledger**. Nếu dùng làm gate, PR có lỗi FM-08 (reply lệch ledger) sẽ được merge. Đúng theo quy tắc của lab: tiền và approval luôn chấm bằng code, không bao giờ bằng judge.
- Rogan-Gladen của helpful cho 0.09 → 0.30, khớp tỉ lệ thật trên tập này. Nhưng với sensitivity 0.3, ước lượng rất nhạy với sai số của sens/spec, không đủ tin cậy để ra quyết định.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật. Nhãn người cũng có lỗi (H-081), nên cần người thứ hai review các ca bất đồng trước khi chốt nhãn.
