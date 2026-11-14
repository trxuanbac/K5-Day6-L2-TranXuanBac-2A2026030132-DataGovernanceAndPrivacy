# T02 — Chạy và kiểm tra bài

## Môi trường

Python 3.11–3.13, CPU, không cần model hoặc OpenCV cho thuật toán hiện tại.
Môi trường `.venv` trên máy đã cài thành công bằng danh sách bỏ OpenCV.
Máy mới có thể `make setup`; nếu pip không tìm được OpenCV, dùng:

```bash
python3 -m venv .venv
sed '/^opencv-python-headless/d' requirements.txt > /tmp/t02-requirements.txt
.venv/bin/python -m pip install -r /tmp/t02-requirements.txt
```

Lần cài cần mạng hoặc wheelhouse; run/demo chạy offline.

## Một chuỗi chạy đầy đủ

```bash
make verify
make baseline TRACK=t02 OUT=out/t02
make run TRACK=t02 OUT=out/t02
make test
.venv/bin/python -m tools.t02_summary
open out/t02/poc/contact_sheet.html
```

`make baseline TRACK=t02` đã nối với baseline Laplacian, không còn random baseline.
Các track ví dụ khác vẫn giữ random module. `./run.sh t02` là lệnh tái lập PoC + tests;
output của run.sh ở out/poc, còn chuỗi phía trên dùng out/t02/poc.

## Review đã lưu

20 dòng được lưu tại reports/reviewed_images.csv, không chỉ trong Downloads/out.
Cấu hình params.review_import đọc cùng một tập review cho baseline và PoC.
Review này được thu từ queue Laplacian cũ, không phải đánh giá độc lập trên top20 mới của PoC.
Score không thay đổi sau review; official recall/precision chỉ dùng score và GT của giảng viên.
Không dùng review trên eval để chỉnh threshold; normalization chỉ fit dev.
File review gắn với checksum manifest; hidden input khác checksum thì bỏ qua review cũ và ghi audit.

Các lựa chọn:

- approve: giữ action hiện tại.
- edit/reject: override KEEP/RECAPTURE kèm note.
- escalate: action REVIEW, quyết định tổng HOLD.
- skip: chưa hoàn thành đánh giá.

Muốn review thêm ở queue mới, export review_queue_reviewed.csv vào thư mục output của run đó.
Tổng số ảnh được review không vượt budget 20; để thay tập review, bỏ `review_import`
trong config hoặc dùng bản config khác, và không so sánh can thiệp review khác nhau như cùng budget/protocol.
Không đổi score chỉ vì người duyệt sửa action. Giữ predictions_raw.csv để đối chiếu.

## Output

- ranked_review.csv: toàn bộ 96 ảnh, score và action sau review.
- predictions_raw.csv: dự đoán ban đầu, score gốc để tái lập ranking.
- features.csv: Laplacian, brightness, local saturation, blockiness.
- calibration.json: threshold global/group fit từ dev, params đã dùng.
- review_queue.csv, contact_sheet.html: queue mới top20 có ảnh.
- review_results.csv: những ảnh đã được review.
- audit_log.jsonl: ai/ảnh/quyết định cũ/mới/lý do/source.
- decision.json và decision_log.csv: HOLD khi có escalation, REWORK khi cần chụp lại;
  không tự GO chỉ vì thuật toán cho KEEP.
- run_info.json: seed/config hash/runtime/máy/git SHA.

## Khi có GT giảng viên

```bash
make eval-baseline TRACK=t02 OUT=out/t02
make eval-poc TRACK=t02 OUT=out/t02
make compare TRACK=t02
```

Không có GT thì evaluate exit 2 là dự kiến. Không có metrics_*.json chính thức được tạo giả.
Bảng descriptive có thể bị `make compare` ghi đè bằng bảng chính thức khi đã có metrics.

## Case demo

Xem demo/T02_SHOWCASE.md và demo/t02_examples.png. Ảnh từng escalate đã được xem lại từ ảnh gốc và chọn KEEP. Decision vẫn REWORK vì còn ảnh cần chụp lại.

## Bộ ảnh ngoài miền (khi có 10 ảnh được phép sử dụng)

```bash
.venv/bin/python -m tools.prepare_t02_ood --source /duong/dan/anh --provenance "Nguồn thực tế" --license "Quyền sử dụng thực tế"
.venv/bin/python -m src.main --config data/ood/t02/lab_ood.yaml --offline --seed 42
```

Công cụ giữ ảnh ở data/ood/ (gitignored), tạo metadata/manifest và sao chép calibration dev gốc.
Không fit lại trên ảnh OOD. Bộ web bên dưới đã được review; quyết định và lý do ở reports/t02_ood_reviewed.csv.

## Bộ ảnh web đã chuẩn bị

10 ảnh CC0 ở `data/ood/t02_web/images/`, nguồn/tác giả/checksum ở `reports/t02_ood_sources.csv`.

```bash
.venv/bin/python -m src.main --config data/ood/t02_web/lab_ood.yaml --offline --seed 42
open out/t02/ood/contact_sheet.html
```

Bộ ảnh có ảnh đường phố ban ngày, cảnh mưa, ảnh đen trắng và phơi sáng đêm; đây là stress test ngoài miền, không đại diện đầy đủ cho camera hành trình.
Ảnh và config bộ này được giữ local trong thư mục gitignored.
