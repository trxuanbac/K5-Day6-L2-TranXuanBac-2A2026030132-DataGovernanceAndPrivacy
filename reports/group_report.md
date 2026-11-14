# T02 — Raw QC Triage: ảnh mờ, lóa và thiếu sáng

## 00. Thông tin

- Người thực hiện: Trần Xuân Bắc, cá nhân; cấu hình nhóm G06.
- Challenge: T02, xếp hạng ảnh nghi lỗi cho ngân sách review B=20.
- Trạng thái: baseline và PoC chạy offline, đã nhập 20 review. Đã giải quyết escalation sau khi xem ảnh gốc; còn các ảnh cần RECAPTURE.
- Mã nguồn và lệnh tái lập: docs/T02_RUN.md.
- Repo: https://github.com/trxuanbac/K5-Day6-L2-TranXuanBac-2A2026030132-DataGovernanceAndPrivacy
- Git author đang cấu hình: Xuân Bắc <Bxuan964@gmail.com>. Tag nộp bài chưa tạo.

## 01. Bài toán và tiêu chí quyết định

Dữ liệu ảnh lỗi làm giảm chất lượng gán nhãn và mô hình phía sau. Khi chỉ đủ thời gian xem 20 ảnh,
xếp hạng tốt giúp người kiểm tra tìm được nhiều lỗi hơn chọn ngẫu nhiên hoặc chỉ đo một đặc trưng.
Ngược lại, loại mọi ảnh tối có thể làm mất các tình huống ban đêm hữu ích.

Input: ảnh và metadata. Output: image_id, score, loại lỗi gợi ý, action KEEP/RECAPTURE/REVIEW,
hàng đợi review có ảnh, quyết định cuối và audit log.

- KEEP: còn đủ thông tin nhận diện tổng thể theo review.
- RECAPTURE: chất lượng không đủ dùng theo heuristic hoặc quyết định reviewer.
- REVIEW: cần xem thêm, không khẳng định ảnh hỏng.
- HOLD cho toàn run nếu còn REVIEW; REWORK nếu có RECAPTURE mà không còn escalation.
- Không tự GO chỉ vì toàn bộ model prediction là KEEP: cần chủ sở hữu phê duyệt release.

## 02. Dữ liệu và provenance

Fixture synthetic CC0 theo manifest của repo: 96 ảnh 320×180 từ 24 cảnh gốc.
Split do repo cung cấp theo cảnh, thực tế 56 dev và 40 eval; không thay đổi split.
Metadata: image_id, path, camera_id, light, split. Không đọc tên biến thể ảnh để suy ra nhãn lỗi.
Pipeline kiểm manifest SHA256; từ chối ảnh mất, ID trùng, đường dẫn ra ngoài input hoặc vào gt/.
make verify kiểm toàn bộ 14 manifest. Không dùng ảnh thật, model pretrained hay API bên ngoài.

GT chính thức không phát trong repo học viên. 20 review đã lưu chỉ là can thiệp vận hành trên queue
Laplacian cũ, bao gồm cả dev/eval; không phải gold set ngẫu nhiên hay heldout độc lập.
Không dùng nhãn review để tối ưu trọng số, không báo độ chính xác tổng thể từ tập review bị chọn thiên lệch.

## 03. Thiết kế và trade-off

Pipeline 5 bước: load/provenance → feature scoring → rank top20 → review/override → decision/audit.

Baseline: phương sai Laplacian grayscale, score=1/(variance+1e-6), một ngưỡng global là quantile 0.25
trên dev. Ngưỡng chỉ quyết định action; ranking liên tục không phụ thuộc review.

PoC thêm:

- Blur score dựa ngưỡng camera×light khi có ít nhất 6 ảnh dev, thiếu thì fallback global.
- Dark score từ mean brightness và fraction pixel dưới 30.
- Glare score từ tỷ lệ pixel trên 245 trong vùng tile 4×4; phát hiện vùng cháy sáng nhỏ hơn thống kê toàn ảnh.
- JPEG blockiness proxy từ chênh lệch pixel tại ranh giới 8 pixel so với các vị trí còn lại.

Score là max của bốn score thành phần, mỗi score trong [0,1]. Defect threshold=.5.
Các tham số đọc từ config và calibration.json lưu giá trị fit cùng N dev.
Đây là heuristic có thể giải thích, chi phí CPU thấp; không có chứng cứ rằng max-score là tổ hợp tối ưu.
Không tự chỉnh tham số theo kết quả eval. Một số feature bão hòa tạo tie; thứ tự được giữ ổn định.

## 04. Baseline vs PoC

Bảng thống kê được script sinh ở reports/table1_baseline_vs_poc.md, số liệu gốc ở t02_run_summary.json.
Các dòng đếm KEEP/RECAPTURE và runtime không chứng minh độ chính xác hoặc mức cải thiện.

Cả hai run dùng cùng 96 ảnh, dev calibration, seed42, budget20 và cùng file review.
Review là tập cố định từ queue Laplacian cũ, không coi là review độc lập top20 PoC.
Điểm xếp hạng không thay đổi sau override nên official score không bị chỉnh bằng nhãn review.

Official Defect Recall@20 và Precision@20 đang chờ GT giảng viên. Chưa sinh metrics_baseline.json /
metrics_poc.json bằng số giả, chưa khẳng định PoC thắng baseline.
Khi có GT, chạy eval-baseline, eval-poc và compare theo hướng dẫn, báo cả kết quả âm/không cải thiện.

## 05. Protocol đánh giá

Primary = số ảnh lỗi GT trong top20 eval / tổng ảnh lỗi GT eval.
Precision = số ảnh lỗi GT top20 / 20 (xem denominator thực tế evaluator khi pool nhỏ).
Evaluator lọc eval rồi rank, do đó output phải giữ đủ 96 ảnh, không chỉ queue20.
Secondary: false alarm theo light, defect-type accuracy và runtime/100 ảnh.

Chốt threshold và B trước official evaluation, không thay testset hoặc đọc gt/ trong pipeline.
Protocol chi tiết trong metric_contract.md. Chưa có CI chính thức do thiếu GT; khi có nhãn phải báo
numerator/denominator và độ bất định phù hợp, không suy rộng từ mẫu nhỏ.

## 06. Slices và failure cases

reports/t02_slices.csv là số action theo split/light; không phải false alarm rate khi thiếu GT.
Ảnh minh họa ở demo/t02_examples.png.

- img_09_2: mờ mạnh, reviewer chọn RECAPTURE. Laplacian xếp rất cao vì thiếu cạnh và chi tiết.
- img_04_3: chạng vạng, ban đầu chọn escalate; sau khi kiểm tra ảnh gốc đã cập nhật KEEP vì còn nhận biết được xe, người và làn đường.
- img_12_0: chạng vạng nhưng hình người/xe còn rõ, reviewer giữ KEEP. Chỉ nhìn độ sáng có thể loại nhầm.
- img_15_3: thiếu sáng làm mất chi tiết; reviewer chọn RECAPTURE.

Failure bắt buộc của đề: ảnh đêm hữu ích có thể bị báo lỗi; camera mềm làm giảm sharpness;
glare cục bộ có thể bị bỏ sót nếu tile quá lớn hoặc vùng biển số quá nhỏ.
PoC group normalization và local saturation nhắm tới các lỗi này nhưng chưa chứng minh đã giải quyết chúng.
Không tự suy ra defect_type GT từ ID hay từ việc reviewer KEEP/RECAPTURE.

## 07. Human review và quyết định

reports/reviewed_images.csv lưu 20 quyết định: 11 KEEP, 9 RECAPTURE; escalation đã được xử lý sau kiểm tra ảnh gốc.
Tên reviewer theo yêu cầu người học; giữ các quyết định đã nhập và bổ sung các ô còn thiếu theo yêu cầu.
Không dùng file này làm GT chính thức. Note chỉ mô tả chất lượng ảnh.

Edit/reject cần override hợp lệ và lý do; approve giữ action; escalate tạo REVIEW; skip chưa hoàn thành.
Override không đổi score. predictions_raw.csv giữ trạng thái ban đầu, review_results.csv giữ kết quả review.
Audit JSONL append-only lưu actor, image_id, before/after, note và file nguồn.
Review import gắn checksum manifest, không tự áp sang hidden input khác checksum.
Một phiên review mới không được làm tổng số ảnh được review vượt budget20.

## 08. Tái lập và kiểm thử

```bash
make setup
make verify
make baseline TRACK=t02 OUT=out/t02
make run TRACK=t02 OUT=out/t02
make test
.venv/bin/python -m tools.t02_summary
```

OpenCV được để tùy chọn do thuật toán không dùng cv2; tránh lỗi cài gói trên máy hiện tại.
requirements-t02.lock.txt lưu phiên bản môi trường đã chạy, dành cho môi trường tương thích.
Lệnh ./run.sh t02 chạy PoC/test và chỉ evaluate khi có overlay.

Tests kiểm dev-only calibration, dark/glare signal, path/ID/ảnh lỗi, review invalid,
score bất biến sau override, escalation HOLD, review sai manifest bị bỏ qua và idempotency.
Kết quả suite cuối cùng ghi trong PROGRESS.md. Test cần GT được skip đúng thiết kế.
Machine, CPU, Python, runtime, seed, config hash và git SHA lấy từ run_info.json của mỗi run.
SHA hiện tại là commit gốc, không thay cho bằng chứng commit các thay đổi chưa commit.

## 09. Giới hạn và hướng cải tiến

Tập synthetic nhỏ, heuristic chưa kiểm chứng trên ảnh thực hoặc camera mới. Ảnh có texture thấp tự nhiên
có thể bị nhầm blur; đèn/biển báo sáng có thể bị nhầm glare; JPEG proxy nhạy với cạnh hình học.
Group ít mẫu fallback global, không bảo đảm calibration tốt cho night/camera mới.
Cần GT/hidden eval, ablation và 10 ảnh out-of-domain được phép dùng trước khi kết luận production-ready.
Không tuyên bố tuân thủ pháp luật từ pipeline QC, không đưa ảnh người thật chưa được phép lên repo/cloud.

## 10. Đóng góp

Trần Xuân Bắc thực hiện cá nhân. Bằng chứng commit/email/tag cần người học xác nhận và bổ sung;
không dùng commit tác giả starter làm bằng chứng đóng góp cá nhân, không tạo commit/tag giả.
Chi tiết file ở reports/team_contributions.csv. Phần còn lại trong PROGRESS.md.

## 11. References

Tài liệu đã đối chiếu ngày 14/11/2026:

- [OpenCV Laplace Operator](https://docs.opencv.org/4.13.0/d5/db5/tutorial_laplace_operator.html): cơ sở toán tử đạo hàm bậc hai; implementation dùng helper scipy của repo, không cần cv2.
- [NumPy quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html): định nghĩa phân vị dùng trong hiệu chỉnh dev; không phải nhãn lỗi.
- [Pillow ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html): các bộ lọc ảnh, tham khảo khi xây corruption/test; không coi là chứng minh hiệu quả QC.
- docs/tracks/T02.md; src/metrics/tracks.py::eval_t02; src/common/image_ops.py: contract, metric và feature helper của lab.
