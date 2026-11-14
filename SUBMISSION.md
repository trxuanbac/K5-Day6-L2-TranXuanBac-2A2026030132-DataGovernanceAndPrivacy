# Bài nộp T02 — Trần Xuân Bắc

- Repository: https://github.com/trxuanbac/K5-Day6-L2-TranXuanBac-2A2026030132-DataGovernanceAndPrivacy
- Bản nộp: tag `final-24h` (đóng băng hiện tại, không chứng nhận thời hạn lớp).
- Báo cáo: [reports/group_report.md](reports/group_report.md).
- Slide: [demo/T02_SLIDES.html](demo/T02_SLIDES.html), 5 slide offline, dùng ←/→ để trình bày; tải cả repo để ảnh đi kèm hiển thị.
- Nội dung slide dạng văn bản: [demo/T02_SLIDES.md](demo/T02_SLIDES.md).
- Hướng dẫn chạy: [docs/T02_RUN.md](docs/T02_RUN.md).

## Chạy từ clean checkout

```bash
git checkout final-24h
make setup
make verify
make baseline TRACK=t02 OUT=out/t02
make run TRACK=t02 OUT=out/t02
make test
.venv/bin/python -m tools.t02_summary
```

PoC xử lý 96 ảnh, queue20; kết quả hiện tại REWORK do còn ảnh cần chụp lại.
Kiểm thử: 61 passed, 39 skipped (các test cần GT); không có failed.
Review đúng top20 PoC lưu ở reports/poc_reviewed_images.csv. Ba failure mode có bằng chứng ảnh trong reports/t02_failure_analysis.md.

## Metric chờ giảng viên chấm

Repo học viên không có gt/labels.csv. Chưa có điểm Recall@20, Precision@20 và không điền số giả.
Sau khi giảng viên cài GT overlay:

```bash
make eval-baseline TRACK=t02 OUT=out/t02
make eval-poc TRACK=t02 OUT=out/t02
make compare TRACK=t02
```

## Ảnh ngoài miền

Đã chạy/review 10 ảnh CC0; nguồn, checksum và kết quả review được commit trong reports/t02_ood_*.csv/json.
Ảnh thật giữ local ở data/ood/ và không đưa lên Git. Để tải lại cần mạng:

```bash
.venv/bin/python -m tools.download_t02_ood
```

Bộ slide là HTML/Markdown, không phải PowerPoint. Chưa tạo tag demo-180m vì không có bằng chứng mốc thời gian đó.
