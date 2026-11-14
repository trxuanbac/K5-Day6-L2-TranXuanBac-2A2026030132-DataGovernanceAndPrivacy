# T02 — Metric contract

| Mục | Khai báo |
|---|---|
| Track | T02 Raw QC Triage |
| Primary | Defect Recall@B, higher |
| Unit | image, join bằng image_id |
| Numerator | GT defects trong top20 của split eval |
| Denominator | Toàn bộ GT defects trong split eval |
| Secondary | Precision@B; false alarm theo light; defect-type accuracy; runtime/100 ảnh |
| Budget | B=20, seed=42 |
| Pool | fixtures/t02_raw_qc; split và scene do fixture cung cấp, không thay testset |
| Split fit | Chỉ dev cho quantile và normalization camera/light |
| Eval | Mặc định split eval; hidden eval do giảng viên giữ |
| Baseline | Score=1/(Laplacian variance+1e-6), một threshold global quantile 0.25 trên dev |
| PoC | Blur theo camera/light nếu dev group >=6, fallback global; dark, glare ROI và blockiness |
| Threshold | dark_mean=35; dark_fraction=.75; glare_fraction=.20; compression_ratio=1.8; defect_threshold=.5 |
| Ranking | Score liên tục, descending; không sửa score bằng review |
| Review | Mỗi run review top20 của ranking tương ứng; PoC dùng poc_reviewed_images.csv; baseline dùng reviewed_images.csv; không dùng làm gold heldout |
| Slices | light=day/dusk/night; defect_type từ GT khi có; camera hỗ trợ phân tích nội bộ |
| Uncertainty | Báo numerator/denominator, từng failure case, không suy rộng khi N nhỏ; chưa có CI GT |
| Trạng thái | Chưa xem GT; official metric pending; tham số ban đầu được khai báo trước official eval |
| Người phụ trách | Trần Xuân Bắc; ngày xác nhận chốt protocol: người học xác nhận trước chấm |

Review đã thực hiện trước khi viết PoC; không dùng các nhãn review để tìm tham số tối ưu.
Thống kê descriptive trong t02_run_summary.json không thay thế Defect Recall/Precision.
