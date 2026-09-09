# Kế Hoạch Mô Hình Dữ Liệu (Data Model Plan)

## Giai Đoạn 1 (MVP) - Các Model Pydantic Trong Bộ Nhớ (In-Memory)

### `Member` (Model Nội Bộ Chuẩn)
- `first_name` (str)
- `last_name` (str)
- `email` (EmailStr)
- `student_id` (str | None)
- `phone` (str | None)
- `school` (str | None)
- `role` (str | None)
- `class_name` (str | None)
- `major` (str | None)

### `SyncResult` (Tóm Tắt Output)
- `total_members` (int)
- `existing_accounts` (int)
- `accounts_created` (int)
- `already_enrolled` (int)
- `new_enrollments` (int)
- `failed` (int)
- `errors` (list of strings/dicts - danh sách lỗi)

## Giai Đoạn 2 (Tương Lai) - Cấu Trúc Relational Schema Cho PostgreSQL

*(Sẽ được triển khai thông qua SQLAlchemy & Alembic sau khi MVP hoàn tất)*

### Bảng `users`
- `id` (UUID, Khóa chính - PK)
- `moodle_user_id` (int, có thể null)
- `student_id` (varchar, duy nhất - unique)
- `email` (varchar, duy nhất - unique)
- `first_name`, `last_name`

### Bảng `courses`
- `id` (UUID, PK)
- `moodle_course_id` (int, duy nhất)
- `name` (varchar)

### Bảng `enrollment_batches`
- `id` (UUID, PK)
- `source_url` (varchar)
- `status` (enum: RECEIVED, PARSING, VALIDATING, READY, SYNCING, COMPLETED, FAILED)
- `created_at`, `completed_at`

### Bảng `enrollment_records`
- `id` (UUID, PK)
- `batch_id` (Khóa ngoại - FK tới enrollment_batches)
- `user_id` (FK tới users)
- `course_id` (FK tới courses)
- `status` (enum: SUCCESS, ALREADY_ENROLLED, FAILED)
- `error_message` (text)

## Cập Nhật: Moodle Analytics Bronze V0

Đã bắt đầu mở rộng schema để phục vụ nền tảng phân tích học tập Moodle.

### Bảng `raw_moodle_log_files`
- **Grain**: Một dòng = một file log Moodle được nạp vào hệ thống.
- **Mục đích**: Theo dõi metadata của từng lần nạp file để audit và debug pipeline.
- **Cột chính**: `source_file_name`, `source_type`, `row_count`, `inserted_count`, `duplicate_count`, `failed_count`, `time_min`, `time_max`, `load_status`, `loaded_at`.

### Bảng `bronze_moodle_log_events`
- **Grain**: Một dòng = một dòng event log từ Moodle.
- **Mục đích**: Lưu log Moodle đã parse cơ bản, vẫn giữ raw text để truy ngược nguồn.
- **Cột chính**: `raw_file_id`, `source_row_number`, `event_time`, `user_full_name_raw`, `event_context_raw`, `component_raw`, `event_name_raw`, `description_raw`, `moodle_user_id`, `moodle_course_id`, `moodle_course_module_id`, `moodle_group_id`, `context_type`, `context_name`, `event_category`, `is_learning_event`, `event_hash`.
- **Quy tắc chống trùng v0**: `event_hash` được tạo từ `source_file_name`, `source_row_number` và toàn bộ giá trị raw của dòng log.
