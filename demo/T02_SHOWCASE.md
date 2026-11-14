# T02 — Kịch bản showcase 3–5 phút

## 1. Bài toán (30 giây)

96 ảnh synthetic; chỉ đủ ngân sách review 20 ảnh. Cần ưu tiên lỗi và tránh loại nhầm ảnh đêm hữu ích.
Mở demo/t02_examples.png để minh họa blur, dusk, dark và escalation.

## 2. Baseline và PoC (45 giây)

Baseline: một chỉ số Laplacian, một ngưỡng global fit dev.
PoC: blur chuẩn hóa theo camera/light, thiếu sáng, vùng cháy sáng cục bộ, dấu hiệu JPEG blockiness.
Không đọc GT, không gọi API/model. calibration.json chứng minh fit dev.

## 3. Demo thật (90 giây)

```bash
make baseline TRACK=t02 OUT=out/t02
make run TRACK=t02 OUT=out/t02
open out/t02/poc/contact_sheet.html
```

Mở reports/reviewed_images.csv, chỉ một dòng override; mở out/t02/poc/review_results.csv
và audit_log.jsonl để đối chiếu. Ảnh img_04_3 đã cập nhật KEEP sau kiểm tra ảnh gốc.
Không bấm export ghi đè review nếu chưa hoàn thành phiên mới.

## 4. Kết quả và giới hạn (45 giây)

Mở reports/table1_baseline_vs_poc.md. Đây là runtime/counts, chưa phải độ chính xác.
Official recall/precision cần GT giảng viên; không khẳng định PoC tốt hơn baseline khi chưa chấm.
Failure 1: global sharpness có thể đánh nhầm ảnh đêm/camera mềm. Failure 2: ảnh nét toàn cảnh
nhưng vùng nhỏ glare có thể lọt. PoC local tiles chỉ là heuristic, chưa phải detector biển số.

## 5. Reliability và chốt (30 giây)

```bash
make test
make verify
```

Nêu test calibration không fit eval; review không đổi ranking; invalid override bị chặn;
run hai lần cho prediction giống nhau. REWORK hiện tại phản ánh các ảnh cần chụp lại.
