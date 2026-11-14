# 1. T02 · Raw QC Triage

Trần Xuân Bắc · G06. Ưu tiên review 20 ảnh trong 96 ảnh synthetic; CPU, offline.
Ảnh minh họa: t02_examples.png.

---

# 2. Baseline và PoC

Baseline: Laplacian toàn ảnh, một ngưỡng global.
PoC: blur + brightness + local saturation + blockiness, ngưỡng camera/light.
Fit trên 56 ảnh dev, seed42, không đọc GT. Review không đổi score.

---

# 3. Human review và audit

Review đúng top20 PoC. CSV chứa reviewer/action/note; audit append-only lưu before/after.
REWORK nghĩa là có ảnh cần chụp lại, không phải chương trình bị lỗi.
Demo: make run TRACK=t02 OUT=out/t02.

---

# 4. Failure cases

Xem t02_failure_cases.png và reports/t02_failure_analysis.md.
Ảnh đêm hữu ích bị loại; glare biển số lọt baseline; cam_B/dusk fallback global báo nhầm.
Không khẳng định mọi failure đã được giải quyết.

---

# 5. Kết quả và giới hạn

61 passed, 39 skipped. 10 ảnh OOD CC0: review 5 KEEP, 5 RECAPTURE, sửa 6 đề xuất.
Đây là review định tính, không phải GT chính thức. Recall@20 và Precision@20 chờ giảng viên.
