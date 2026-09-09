# Kiến Trúc Lấy Moodle Logs Liên Tục

Ngày tạo: 2026-09-09

Mục tiêu dài hạn là tự động lấy Moodle logs về theo chu kỳ, xử lý theo lớp `raw -> bronze -> silver -> gold`, rồi cập nhật dashboard học tập gần real-time.

## Nguyên Tắc Nguồn Dữ Liệu

Không nên scrape giao diện Live logs HTML để làm pipeline chính.

Lý do:

- UI Live logs sinh ra cho con người xem, không phải nguồn dữ liệu ổn định.
- HTML có thể đổi theo theme, phiên bản Moodle hoặc quyền người dùng.
- Việc scrape dễ hỏng và khó audit trong portfolio data engineer.

Nguồn dữ liệu tốt hơn là log store/database của Moodle hoặc một API/plugin chính thức do mình kiểm soát.

## Phương Án Ưu Tiên

### Phương Án A: External Database Log Store

Moodle ghi log sang một database ngoài. Pipeline của ThinkSpace đọc incrementally từ database log đó.

Luồng:

```text
Moodle
  -> External database log store
  -> extractor theo watermark
  -> raw_moodle_log_files hoặc raw_moodle_log_batches
  -> bronze_moodle_log_events
  -> silver_moodle_learning_events
  -> gold summaries
  -> dashboard
```

Ưu điểm:

- Gần với data engineering thực tế.
- Không phụ thuộc thao tác download file thủ công.
- Có thể chạy mỗi 60 giây, 2 phút hoặc 2 tiếng tùy nhu cầu.

Nhược điểm:

- Cần quyền admin Moodle để bật và cấu hình log store.
- Cần thống nhất nơi đặt external log database.

### Phương Án B: Đọc Trực Tiếp Từ Moodle Database

Nếu có quyền read-only vào database Moodle, extractor đọc bảng log chuẩn của Moodle theo `id` hoặc thời gian.

Ưu điểm:

- Dữ liệu đầy đủ.
- Không cần người dùng download file.

Nhược điểm:

- Đụng trực tiếp database Moodle production nên cần phân quyền rất chặt.
- Không nên để app dashboard dùng quyền ghi hoặc quyền admin database Moodle.

### Phương Án C: Custom Moodle Plugin/API

Tạo endpoint trong Moodle trả logs đã lọc theo course và thời gian.

Ưu điểm:

- Kiểm soát schema trả về.
- Dễ áp dụng rule quyền truy cập.

Nhược điểm:

- Cần phát triển plugin Moodle/PHP.
- Phù hợp giai đoạn sau khi pipeline local đã ổn.

## Thiết Kế Incremental

Pipeline không nên lấy lại toàn bộ logs mỗi lần. Cần có bảng trạng thái:

```text
moodle_log_ingestion_state
```

Cột đề xuất:

```text
source_name
course_id
last_moodle_log_id
last_event_time
last_success_at
status
error_message
```

Cách chạy:

1. Đọc `last_moodle_log_id` hoặc `last_event_time`.
2. Lấy các log mới hơn watermark.
3. Ghi batch raw.
4. Upsert hoặc insert có chống trùng vào bronze bằng `event_hash`.
5. Refresh view/model silver và gold.
6. Cập nhật dashboard.

## Tần Suất Cập Nhật

Giai đoạn demo:

```text
Import thủ công file log -> dashboard cập nhật ngay
```

Giai đoạn pipeline local:

```text
Extractor chạy mỗi 2 tiếng bằng script hoặc scheduler đơn giản
```

Giai đoạn gần real-time:

```text
Extractor chạy mỗi 60 giây đến 5 phút
```

Không cần cloud ngay từ đầu. Ta nên làm local trước để chắc data model, metric và rule mapping đúng. Khi ổn, chuyển database sang cloud hoặc thêm job scheduler sau.

## Dashboard Sẽ Đọc Từ Đâu

Dashboard không đọc trực tiếp Live logs.

Dashboard đọc:

```text
gold_registered_user_learning_summary
gold_team_learning_summary
gold_individual_learning_summary
dim_moodle_course_activities
silver_moodle_learning_events cho drill-down chi tiết
```

## Bài Tập Nhỏ Cho Bạn

Trong DBeaver, hãy tạo thử câu SQL mô phỏng incremental:

```sql
SELECT *
FROM bronze_moodle_log_events
WHERE event_time > TIMESTAMP '2026-09-09 00:00:00'
ORDER BY event_time;
```

Sau đó đổi điều kiện sang `id > ...` nếu bảng log nguồn có id tăng dần. Đây là tư duy watermark, một trong những nền tảng quan trọng của pipeline incremental.
