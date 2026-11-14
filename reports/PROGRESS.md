# Tiến độ T02

## Đã hoàn thành

- [x] Chuyển cấu hình T02, giữ G06 và Trần Xuân Bắc.
- [x] Baseline Laplacian một ngưỡng global fit trên dev.
- [x] PoC blur + dark + local glare + blockiness; calibration chỉ dùng dev.
- [x] Output đủ 96 ảnh, queue20 và contact sheet có ảnh.
- [x] Lưu 20 review: 11 KEEP, 9 RECAPTURE; không đổi score xếp hạng.
- [x] Override validation, audit append-only, reason/owner và risk gate.
- [x] Ràng buộc review import theo checksum input manifest.
- [x] Kiểm thử: **61 passed, 39 skipped**, không có failed.
- [x] Baseline, PoC và ./run.sh t02 chạy offline exit 0.
- [x] Preflight: 0 FAIL, 3 WARN (cv2, real data, optional models đều tùy chọn).
- [x] 14 manifest hợp lệ; git diff --check không lỗi.
- [x] Báo cáo, metric contract, bảng descriptive/slices sinh bằng script.
- [x] Kịch bản demo và hình minh họa; hướng dẫn tái lập docs/T02_RUN.md.
- [x] OpenCV tùy chọn, snapshot dependency versions.

## Còn cần thông tin hoặc hành động bên ngoài

- [x] Đã xem ảnh gốc img_04_3, cập nhật KEEP kèm lý do; decision chuyển REWORK do còn ảnh cần chụp lại.
- [ ] GT/hidden eval giảng viên để chấm Recall@20, Precision@20 và failure slices chính thức.
- [x] Đã tải 10 ảnh đường phố CC0 từ Wikimedia Commons và chạy OOD với calibration cố định.
- [x] Đã xem và review 10 ảnh OOD theo yêu cầu: 5 KEEP, 5 RECAPTURE; đã áp override và ghi audit. Chưa có GT độc lập để báo accuracy.
- [x] Kiểm tra Git author/email và repo URL từ cấu hình thực tế.
- [x] Đóng băng bản nộp hiện tại bằng tag final-24h; metric chính thức vẫn chờ GT.
- [x] Bổ sung calibration cố định và tools/prepare_t02_ood.py.
- [x] Nguồn ảnh ngoài miền đã bổ sung trong reports/t02_ood_sources.csv.

Thống kê counts/runtime không phải độ chính xác. Chưa khẳng định PoC tốt hơn baseline.

- [x] Commit triển khai: `780c1e9`, author Xuân Bắc <Bxuan964@gmail.com>. Chưa push hoặc tạo tag nộp bài.

- [x] Kiểm tra cuối: pytest exit 0, 14 fixture manifests hợp lệ; manifest bộ 10 ảnh OOD hợp lệ; 10 review có đủ lý do.

- [x] Hoàn thiện review đúng 20/20 ảnh queue PoC; baseline và PoC mỗi phiên budget20.
- [x] Ba failure modes bắt buộc có ảnh, feature, raw prediction và root cause: reports/t02_failure_analysis.md.

- [x] Có 5 slide HTML offline và bản Markdown, đã kiểm tra hiển thị từng slide.
- [x] Hướng dẫn nộp và chấm lại với GT: SUBMISSION.md.
