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
- [ ] Kiểm tra 10 ảnh out-of-domain được phép sử dụng theo yêu cầu +24h; chưa có bộ này.
- [x] Kiểm tra Git author/email và repo URL từ cấu hình thực tế.
- [ ] Tag nộp bài theo quy định lớp; chưa tạo khi còn chờ GT.
- [x] Bổ sung calibration cố định và tools/prepare_t02_ood.py.
- [ ] Ảnh ngoài miền: người học xác nhận chưa có nguồn ảnh.

Thống kê counts/runtime không phải độ chính xác. Chưa khẳng định PoC tốt hơn baseline.
