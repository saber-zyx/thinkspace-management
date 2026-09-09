# Mô Hình Dữ Liệu Moodle Analytics V0

## Mục Tiêu Của Bước Này
Thiết kế mô hình dữ liệu đầu tiên cho việc phân tích hành vi học tập trên Moodle, dựa trên file log mẫu:

`example/logs_SANDBOX2026_20260907-2141.csv`

Bước này chỉ tập trung vào mô hình dữ liệu và cách hiểu log. Chưa triển khai pipeline code.

## Câu Hỏi Nghiệp Vụ Đầu Tiên
Quản lý chương trình cần trả lời:

1. Người dùng nào đã từng truy cập Moodle?
2. Người dùng nào chưa từng truy cập và vẫn có trạng thái `Never`?
3. Người dùng đang xem nội dung nào nhiều nhất?
4. Mỗi đội nhóm đang có bao nhiêu thành viên active?
5. Nội dung nào có ít lượt xem để ban tổ chức cần nhắc nhở hoặc cải thiện?

## Quan Sát Từ File Log Mẫu
File log mẫu có 3.691 dòng.

Các cột hiện có:
- `Time`
- `User full name`
- `Affected user`
- `Event context`
- `Component`
- `Event name`
- `Description`
- `Origin`
- `IP address`

Khoảng thời gian trong file:
- Sớm nhất: `2026-08-05 18:45:32`
- Muộn nhất: `2026-09-07 21:40:58`

Một số event phổ biến:
- `Course module viewed`
- `Course viewed`
- `Section viewed`
- `H5P content viewed`
- `xAPI statement received`
- `User enrolled in course`
- `Role assigned`

Nhận xét quan trọng: file log đang trộn cả hành vi học tập của thí sinh và hành vi quản trị của admin/support. Vì vậy pipeline cần phân loại event trước khi đưa lên dashboard.

## Khái Niệm Cốt Lõi: Grain
Grain là câu trả lời cho câu hỏi:

> Một dòng trong bảng này đại diện cho điều gì?

Nếu grain không rõ, dashboard rất dễ bị đếm sai.

Grain được chọn cho bảng log chính:

> Một dòng = một event Moodle xảy ra bởi một user tại một thời điểm.

Ví dụ từ log:

```text
Time = 7/09/26, 21:40:58
User full name = Châu Bùi Trần Minh
Event context = Page: FAQ
Component = Page
Event name = Course module viewed
Description = The user with id '1046' viewed the 'page' activity with course module id '643'.
```

Dòng này có nghĩa:

```text
User Moodle 1046 đã xem activity dạng page, course module id 643, tên hiển thị là FAQ.
```

## Mô Hình Tổng Quan V0
Mô hình v0 gồm 4 lớp:

```text
raw_moodle_log_files
        ↓
bronze_moodle_log_events
        ↓
silver_moodle_learning_events
        ↓
gold_user_learning_summary
gold_team_learning_summary
gold_content_attention_summary
```

## Lớp Raw

### Bảng `raw_moodle_log_files`
Mục đích: lưu metadata của mỗi file log được nạp vào hệ thống.

Grain:

> Một dòng = một file log Moodle được upload hoặc được kéo về.

Cột đề xuất:
- `id`: khóa chính nội bộ.
- `source_file_name`: tên file gốc.
- `source_type`: `manual_upload`, `scheduled_export`, `moodle_api`, `live_log`.
- `course_id`: Moodle course id nếu xác định được.
- `row_count`: số dòng trong file.
- `time_min`: thời điểm event sớm nhất trong file.
- `time_max`: thời điểm event muộn nhất trong file.
- `loaded_at`: thời điểm hệ thống nạp file.
- `load_status`: trạng thái nạp.
- `error_message`: lỗi nếu có.

Lý do cần bảng này: sau này khi dashboard có số liệu lạ, ta biết số liệu đến từ file nào.

## Lớp Bronze

### Bảng `bronze_moodle_log_events`
Mục đích: lưu từng dòng log sau khi parse CSV và ép kiểu cơ bản.

Grain:

> Một dòng = một dòng log từ Moodle.

Cột đề xuất:
- `id`: khóa chính nội bộ.
- `raw_file_id`: khóa ngoại tới `raw_moodle_log_files`.
- `source_row_number`: số dòng trong file CSV nguồn.
- `event_time`: thời gian event sau khi parse từ `Time`.
- `user_full_name_raw`: giá trị gốc từ `User full name`.
- `affected_user_raw`: giá trị gốc từ `Affected user`.
- `event_context_raw`: giá trị gốc từ `Event context`.
- `component_raw`: giá trị gốc từ `Component`.
- `event_name_raw`: giá trị gốc từ `Event name`.
- `description_raw`: giá trị gốc từ `Description`.
- `origin_raw`: giá trị gốc từ `Origin`.
- `ip_address_raw`: giá trị gốc từ `IP address`.
- `moodle_user_id`: bóc từ `Description`, ví dụ `1046`.
- `moodle_affected_user_id`: bóc từ `Description` nếu có.
- `moodle_course_id`: bóc từ `Description` nếu có, ví dụ `12`.
- `moodle_course_module_id`: bóc từ `Description` nếu có, ví dụ `643`.
- `moodle_group_id`: bóc từ `Description` nếu có.
- `context_type`: phần trước dấu `:` trong `Event context`, ví dụ `Page`, `Course`, `Forum`.
- `context_name`: phần sau dấu `:` trong `Event context`, ví dụ `FAQ`.
- `event_hash`: khóa tự nhiên để chống trùng.

Khóa chống trùng đề xuất:

```text
event_hash = hash(source_file_name + source_row_number + toàn bộ giá trị raw của dòng log)
```

Lý do thêm `source_row_number`: nếu Moodle export hai dòng giống hệt nhau trong cùng một file, bronze vẫn giữ cả hai dòng vì grain của bronze là một dòng log nguồn.

Giới hạn v0: nếu cùng một file được đổi tên rồi import lại, hệ thống có thể xem đó là nguồn mới. Nếu sau này lấy được `log_id` thật từ Moodle API thì nên dùng `log_id` làm khóa tự nhiên tốt hơn.

## Lớp Silver

### Bảng `silver_moodle_learning_events`
Mục đích: biến log thô thành event đã có nhãn, phân loại và sẵn sàng phân tích.

Grain:

> Một dòng = một event Moodle đã được làm sạch, gắn nhãn và phân loại.

Cột đề xuất:
- `event_id`: khóa chính tham chiếu từ bronze.
- `event_time`
- `event_date`
- `moodle_user_id`
- `registration_id`: nối về bảng `registrations` nếu map được.
- `full_name`
- `email`
- `student_id`
- `team_name`
- `role`
- `moodle_course_id`
- `course_name`
- `moodle_course_module_id`
- `activity_type`: ví dụ `page`, `forum`, `h5p`, `assignment`, `file`.
- `activity_name`
- `event_name`
- `event_category`: `learning`, `admin`, `system`, `report`, `unknown`.
- `is_learning_event`: true/false.
- `is_view_event`: true/false.
- `is_completion_event`: true/false.
- `origin`
- `loaded_at`

Quy tắc phân loại ban đầu:

```text
Nếu event_name nằm trong:
- Course viewed
- Course module viewed
- Section viewed
- H5P content viewed
- xAPI statement received

thì event_category = learning.
```

```text
Nếu user_full_name_raw là UII ThinkSpace Admin hoặc Component là Logs/Live logs/Grader report,
thì event_category có thể là admin/report thay vì learning.
```

Quy tắc này là v0. Sau khi xem thêm dữ liệu thật, ta sẽ tinh chỉnh.

## Lớp Gold

### Bảng `gold_user_learning_summary`
Mục đích: dashboard cấp từng người dùng.

Grain:

> Một dòng = một user trong một course tại một ngày snapshot.

Cột đề xuất:
- `snapshot_date`
- `moodle_course_id`
- `registration_id`
- `moodle_user_id`
- `full_name`
- `email`
- `student_id`
- `team_name`
- `role`
- `first_access_at`
- `last_access_at`
- `days_since_last_access`
- `has_ever_accessed`
- `learning_event_count`
- `view_event_count`
- `active_days_count`
- `viewed_activity_count`
- `viewed_section_count`
- `completion_percent`
- `risk_status`: `not_started`, `active`, `inactive`, `at_risk`.

### Bảng `gold_team_learning_summary`
Mục đích: dashboard cấp đội nhóm.

Grain:

> Một dòng = một team trong một course tại một ngày snapshot.

Cột đề xuất:
- `snapshot_date`
- `moodle_course_id`
- `team_name`
- `member_count`
- `active_member_count`
- `never_accessed_member_count`
- `avg_view_event_count`
- `avg_completion_percent`
- `last_team_activity_at`
- `team_risk_status`

### Bảng `gold_content_attention_summary`
Mục đích: biết nội dung nào được xem nhiều/ít.

Grain:

> Một dòng = một activity hoặc section trong một course tại một ngày snapshot.

Cột đề xuất:
- `snapshot_date`
- `moodle_course_id`
- `activity_type`
- `activity_id`
- `activity_name`
- `view_count`
- `unique_viewer_count`
- `last_viewed_at`
- `attention_status`: `high`, `normal`, `low`, `no_attention`.

## Cách Nối Với Dữ Liệu Onboarding Hiện Tại
Hiện tại hệ thống đã có bảng `registrations`.

Bảng này đang giữ:
- `full_name`
- `email`
- `student_id`
- `role`
- `team_name`
- `school`
- `project_domain`
- `source`

Trong pipeline analytics, `registrations` sẽ đóng vai trò nguồn mapping nội bộ:

```text
Moodle log user -> registrations -> team_name, role, email, student_id
```

Ở v0, cách map có thể dùng:

```text
silver_moodle_learning_events.full_name = registrations.full_name
```

Nhưng đây chỉ là fallback. Cách tốt hơn là lưu thêm `moodle_user_id` vào `registrations` khi onboarding hoặc khi đồng bộ user từ Moodle.

## Cập Nhật: Dùng File Participants Làm Nguồn Ánh Xạ Danh Tính
Người dùng đã bổ sung file Moodle participants export:

```text
example/courseid_12_participants.csv
```

File này có các cột quan trọng:
- `First name`
- `Last name`
- `Email address`
- `Groups`

Quan sát từ dữ liệu mẫu:

```text
participants rows = 119
bronze learning users = 48
match log -> participants bằng First name + Last name = 46
match participants -> registrations bằng Email address = 107
```

Điều này cho thấy `participants` là nguồn ánh xạ danh tính tốt hơn so với việc map trực tiếp `bronze_moodle_log_events.user_full_name_raw` sang `registrations.full_name`.

Luồng ánh xạ đề xuất cho silver v0:

```text
bronze_moodle_log_events.user_full_name_raw
  -> participants.full_name_moodle = First name + ' ' + Last name
  -> participants.email
  -> registrations.email
  -> registrations.team_name / role / student_id
```

Lý do không nên bỏ qua lớp participants:
- Moodle log không có email, trong khi email là khóa ổn định hơn tên.
- Tên trong Moodle có thể thiếu dấu, đảo thứ tự hoặc khác định dạng so với form đăng ký.
- File participants có `Groups`, giúp kiểm tra chéo team từ Moodle với team trong `registrations`.
- Nếu map thẳng từ log sang registrations bằng tên, kết quả hiện tại không đáng tin.

Thiết kế silver nên xem participants như một bảng dimension/staging, không phải là công đoạn thừa:

```text
raw/bronze participants
  -> dim_moodle_participants hoặc stg_moodle_participants
  -> silver_moodle_learning_events
```

Trong giai đoạn dùng dbt, model `stg_moodle_participants` sẽ chuẩn hóa tên, email, groups. Model `silver_moodle_learning_events` sẽ join từ bronze logs sang staging participants, rồi join tiếp sang registrations bằng email.

Giới hạn v0:
- Nếu hai Moodle users có cùng full name, join bằng tên sẽ mơ hồ. Khi lấy được `moodle_user_id` từ Moodle participants hoặc API, cần dùng `moodle_user_id` làm khóa chính cho mapping.
- Hiện có 2 Moodle learning users chưa match được qua participants bằng tên, cần kiểm tra thủ công trước khi coi mapping là hoàn chỉnh.

## Ví Dụ SQL Mẫu
Ví dụ câu hỏi:

> Ai đã từng truy cập Moodle và lần cuối truy cập là khi nào?

SQL ý tưởng:

```sql
SELECT
    registration_id,
    full_name,
    email,
    team_name,
    MIN(event_time) AS first_access_at,
    MAX(event_time) AS last_access_at,
    COUNT(*) AS learning_event_count
FROM silver_moodle_learning_events
WHERE is_learning_event = true
GROUP BY registration_id, full_name, email, team_name;
```

Ví dụ câu hỏi:

> Team nào có nhiều thành viên chưa từng truy cập?

SQL ý tưởng:

```sql
SELECT
    team_name,
    COUNT(*) AS member_count,
    SUM(CASE WHEN has_ever_accessed = false THEN 1 ELSE 0 END) AS never_accessed_member_count
FROM gold_user_learning_summary
GROUP BY team_name
ORDER BY never_accessed_member_count DESC;
```

## Bài Tập Thực Hành Cho Người Dùng
Hãy tự thử trả lời câu này trước khi qua bước code:

> Với bảng `gold_content_attention_summary`, một dòng nên đại diện cho activity, section, hay cả hai?

Gợi ý:
- Nếu một dòng là activity, ta biết chi tiết từng tài nguyên như `FAQ`, `READ ME FIRST`, `Ask Organizers`.
- Nếu một dòng là section, ta biết tổng quan từng phần học.
- Nếu muốn cả hai, có thể thêm cột `content_grain` với giá trị `activity` hoặc `section`.

## Bước Tiếp Theo Sau Tài Liệu Này
Bước kế tiếp nên là tạo pipeline nhỏ nhất:

```text
CSV log mẫu -> bronze_moodle_log_events -> kiểm tra parse ID và thời gian
```

Chưa cần làm dashboard ngay. Mục tiêu tiếp theo là chứng minh rằng hệ thống đọc được log, tách được ID, và chống trùng khi chạy lại cùng một file.

## Cập Nhật Triển Khai: Pipeline Bronze Tối Thiểu
Pipeline bronze tối thiểu đã được thiết kế để nhận file CSV log Moodle qua endpoint:

```text
POST /api/v1/moodle-logs/import-csv
```

Endpoint kiểm tra nhanh sau khi import:

```text
GET /api/v1/moodle-logs/bronze-summary
```

Các bảng được tạo trong database:
- `raw_moodle_log_files`
- `bronze_moodle_log_events`

Luồng xử lý:

```text
CSV log Moodle
  -> đọc header
  -> parse từng dòng
  -> parse Time thành event_time
  -> bóc Moodle ID từ Description
  -> tách Event context thành context_type/context_name
  -> phân loại event_category
  -> tạo event_hash để chống trùng
  -> insert vào bronze_moodle_log_events
```

## SQL Thực Hành Trong DBeaver
Sau khi import file log, người dùng nên tự chạy các câu SQL sau trong DBeaver.

### 1. Kiểm tra đã nạp bao nhiêu file log

```sql
SELECT
    id,
    source_file_name,
    row_count,
    inserted_count,
    duplicate_count,
    failed_count,
    load_status,
    time_min,
    time_max
FROM raw_moodle_log_files
ORDER BY id DESC;
```

Ý nghĩa:
- `row_count`: số dòng đọc từ CSV.
- `inserted_count`: số event mới được nạp.
- `duplicate_count`: số event bị bỏ qua vì đã tồn tại.
- `failed_count`: số dòng lỗi parse.

### 2. Kiểm tra tổng số event trong bronze

```sql
SELECT COUNT(*) AS total_bronze_events
FROM bronze_moodle_log_events;
```

Ý nghĩa: nếu import file mẫu lần đầu, số này nên tăng theo số dòng hợp lệ trong file.

### 3. Kiểm tra phân loại event

```sql
SELECT
    event_category,
    COUNT(*) AS event_count
FROM bronze_moodle_log_events
GROUP BY event_category
ORDER BY event_count DESC;
```

Ý nghĩa: câu này giúp thấy log đang gồm bao nhiêu event học tập, quản trị, báo cáo hoặc hệ thống.

### 4. Xem các nội dung học tập được xem nhiều nhất

```sql
SELECT
    context_type,
    context_name,
    COUNT(*) AS view_count,
    COUNT(DISTINCT moodle_user_id) AS unique_users
FROM bronze_moodle_log_events
WHERE is_learning_event = true
GROUP BY context_type, context_name
ORDER BY view_count DESC
LIMIT 20;
```

Ý nghĩa: đây là bản thô đầu tiên của chỉ số “nội dung nào được chú ý nhiều”.

### 5. Xem user nào hoạt động nhiều nhất

```sql
SELECT
    moodle_user_id,
    user_full_name_raw,
    COUNT(*) AS learning_event_count,
    MIN(event_time) AS first_access_at,
    MAX(event_time) AS last_access_at
FROM bronze_moodle_log_events
WHERE is_learning_event = true
GROUP BY moodle_user_id, user_full_name_raw
ORDER BY learning_event_count DESC
LIMIT 20;
```

Ý nghĩa: đây là bước đầu để tạo bảng `gold_user_learning_summary`.

### Bài Tập Nhỏ
Hãy tự sửa câu SQL số 5 để chỉ lấy những user có `learning_event_count >= 5`.

## Kết Quả Kiểm Chứng Với File Mẫu
Sau khi import `example/logs_SANDBOX2026_20260907-2141.csv` vào database thật:

```text
row_count = 3691
inserted_count = 3691
duplicate_count = 0
failed_count = 0
course_id = 12
time_min = 2026-08-05 18:45:32
time_max = 2026-09-07 21:40:58
```

Khi import lại đúng file đó lần thứ hai:

```text
inserted_count = 0
duplicate_count = 3691
total_events trong bronze vẫn = 3691
```

Phân loại event sau khi nạp:

```text
admin = 1880
learning = 1514
system = 182
unknown = 97
report = 18
```

Điều này xác nhận pipeline bronze v0 đã đạt yêu cầu tối thiểu:
- Đọc được CSV log Moodle.
- Parse được thời gian.
- Bóc được các Moodle ID chính từ `Description`.
- Phân loại sơ bộ event.
- Chạy lại cùng file không nhân đôi dữ liệu bronze.

## Cập Nhật Làm Sạch Dữ Liệu Test Trong Database Local
Ngày 2026-09-08, người dùng xác nhận hai Moodle user id sau là tài khoản test cũ, không thuộc hệ thống chính:

```text
moodle_user_id = 924
moodle_user_id = 919
```

Các log liên quan đã được backup trước khi xóa:

```text
backup_deleted_bronze_moodle_log_events_test_users_20260908
```

Kết quả cleanup:

```text
rows backed up = 49
rows deleted = 49
remaining rows for test users = 0
total bronze events after delete = 3642
learning users after delete = 46
matched learning users after delete = 46
```

Lưu ý: số liệu import gốc ở phần trên vẫn mô tả kết quả kiểm thử pipeline khi nạp file ban đầu. Số liệu hiện tại trong database local đã được làm sạch để loại test users khỏi phân tích silver/gold.

## Cập Nhật Triển Khai: Participants Import Chính Thức V0
Đã triển khai pipeline chính thức để nạp Moodle participants export vào database.

Endpoint import:

```text
POST /api/v1/moodle-participants/import-csv
```

Endpoint kiểm tra nhanh:

```text
GET /api/v1/moodle-participants/summary
```

Các bảng được tạo:
- `raw_moodle_participant_files`
- `raw_moodle_participants`
- `moodle_participant_email_exclusions`

Grain:
- `raw_moodle_participant_files`: một dòng = một file participants được import.
- `raw_moodle_participants`: một dòng = một participant trong file Moodle export.

Luồng xử lý:

```text
CSV participants Moodle
  -> đọc header
  -> chuẩn hóa First name + Last name thành moodle_full_name
  -> tạo moodle_full_name_key để join với log
  -> chuẩn hóa Email address thành email
  -> giữ Groups thành moodle_group_name
  -> tạo participant_hash để chống trùng khi import lại cùng file
  -> insert vào raw_moodle_participants
```

Kết quả kiểm chứng với file:

```text
example/courseid_12_participants.csv
```

Import lần đầu:

```text
row_count = 119
inserted_count = 119
duplicate_count = 0
failed_count = 0
course_id = 12
```

Import lại cùng file:

```text
inserted_count = 0
duplicate_count = 119
```

Sau khi xóa các email sai đã được người dùng xác nhận:

```text
raw_moodle_participants = 113
duplicate full name groups = 0
```

Các email sai được lưu vào `moodle_participant_email_exclusions` để import lại file gốc không đưa dữ liệu sai quay trở lại.

Import lại file gốc sau khi có exclusion:

```text
row_count = 119
inserted_count = 0
duplicate_count = 113
excluded_count = 6
failed_count = 0
```

Kiểm tra mapping chính thức sau cleanup:

```text
learning users = 46
matched users by name = 45
matched emails = 45
participants match registrations = 101
```

Lý do `learning users` lớn hơn `matched emails`: có một trường hợp hai Moodle user id cùng dùng một tên Moodle:

```text
Tiêm Mai An -> moodle_user_id 921, 931 -> vothientruong2005@gmail.com
```

Ngày 2026-09-08, người dùng xác nhận các log liên quan tới `Tiêm Mai An` cần được loại khỏi dữ liệu phân tích. Các log có `moodle_user_id` hoặc `moodle_affected_user_id` thuộc `921`, `931` đã được backup trước khi xóa:

```text
backup_deleted_bronze_moodle_log_events_tiem_mai_an_20260908
```

Kết quả cleanup:

```text
rows backed up = 111
rows deleted = 111
remaining rows = 0
total bronze events after delete = 3531
learning events after delete = 1461
learning users after delete = 44
matched emails after delete = 44
```

## Cập Nhật Triển Khai: Identity Map Chính Thức V0
Đã tạo view chính thức:

```text
int_moodle_user_identity_map
```

Grain:

```text
một dòng = một participant Moodle đã được nối với registration nếu có
```

Mục tiêu:

```text
raw_moodle_participants.email
  -> registrations.email
  -> registration_id, student_id, role, registration_team_name
```

View này là lớp intermediate trước silver. Silver sẽ join log học tập vào view này bằng:

```text
bronze_moodle_log_events.user_full_name_raw
  -> int_moodle_user_identity_map.moodle_full_name_key
```

Endpoint kiểm tra:

```text
GET /api/v1/moodle-participants/identity-map-summary
```

Kết quả kiểm chứng:

```text
total_identities = 113
matched_registrations = 101
unmatched_registrations = 12
learning_users = 45
matched_learning_users = 45
```

Phân loại trạng thái identity:

```text
matched_same_team = 80
matched_without_moodle_group = 19
unmatched_registration = 12
matched_team_conflict = 2
```

Ghi chú kỹ thuật: trong lúc triển khai, app từng lỗi startup vì view nháp `int_moodle_user_identity_map_v0` phụ thuộc vào `registrations.team_name`, còn hàm `ensure_registration_text_columns()` cố alter lại cột này mỗi lần khởi động. Đã sửa hàm ensure để chỉ alter khi cột chưa phải kiểu `TEXT`.

## Cập Nhật Chất Lượng Dữ Liệu: Backfill Moodle User ID Cho H5P/xAPI
Trong lúc người dùng kiểm tra `silver_moodle_learning_events_v0` trong DBeaver, phát hiện một nhóm `xAPI statement received` có `moodle_user_id` bị `NULL` dù `description_raw` vẫn chứa user id.

Nguyên nhân:

```text
Parser cũ chỉ bắt mẫu: user with id '982'
Một số log H5P dùng mẫu: user with the id '982'
```

Đã cập nhật parser để hỗ trợ cả hai mẫu:

```text
user with id '...'
user with the id '...'
```

Đã backup trước khi backfill:

```text
backup_bronze_moodle_log_events_before_xapi_id_backfill_20260908
```

Kết quả backfill:

```text
target rows = 201
backed up rows = 201
updated rows = 201
remaining learning events with null moodle_user_id = 0
learning users with id after backfill = 45
matched learning users after backfill = 45
```

Ý nghĩa: silver chính thức có thể dùng `moodle_user_id` làm khóa người học cho toàn bộ learning events hiện tại, không cần fallback bằng email cho các event H5P/xAPI trong dữ liệu mẫu này.
## Cập Nhật Chất Lượng Dữ Liệu: Chuẩn Hóa Tên Đội Cho Dashboard Đăng Ký
Ngày 2026-09-08, dashboard đăng ký hiển thị `23` đội trong khi kiểm tra dữ liệu cho thấy có một đội bị tách đôi vì khác chữ hoa/thường:

```text
STABILY - Thiết bị đeo ổn định chuyển động tay cho người mắc Parkinson
Stabily - Thiết bị đeo ổn định chuyển động tay cho người mắc Parkinson
```

Quy tắc mới cho metric đăng ký:

```sql
team_name_key = lower(trim(team_name))
```

Sau khi chuẩn hóa:

```text
total_users = 101
total_teams = 22
total_individuals = 18
```

Kiểm tra thêm:

```text
Weave Carbon có trong registrations và raw_moodle_participants.
Weave Carbon chưa có learning log trong dữ liệu đang import.
Airweave không xuất hiện trong registrations, raw_moodle_participants, identity map hoặc learning logs đã kiểm tra.
```

Ý nghĩa cho data platform: ở bước silver/gold nên có khóa đội chuẩn hóa hoặc dimension team riêng. Tên hiển thị vẫn giữ để người quản lý đọc, nhưng mọi phép đếm/join nên dùng khóa chuẩn hóa để tránh duplicate ảo.
## Cập Nhật Triển Khai: Silver Moodle Learning Events Chính Thức
Đã tạo view chính thức:

```text
silver_moodle_learning_events
```

Grain:

```text
Một dòng = một learning event Moodle đã được map danh tính người học.
```

Nguồn dữ liệu:

```text
bronze_moodle_log_events
  -> lọc is_learning_event = true
  -> lấy moodle_user_id từ description đã parse
  -> join int_moodle_user_identity_map bằng user_full_name_raw
  -> bổ sung email, registration_id, role, team_name
```

Kết quả kiểm chứng ngày 2026-09-08:

```text
learning_event_rows = 1461
learning_users = 45
matched_learning_emails = 45
learning_teams = 14
unmapped_event_rows = 0
duplicated_bronze_events = 0
```

Endpoint kiểm tra nhanh:

```text
GET /api/v1/moodle-logs/silver-summary
```

### SQL Thực Hành Trong DBeaver
Bạn có thể copy câu này để kiểm tra lại view Silver:

```sql
SELECT
    COUNT(*) AS learning_event_rows,
    COUNT(DISTINCT moodle_user_id) AS learning_users,
    COUNT(DISTINCT email) AS matched_learning_emails,
    COUNT(DISTINCT team_name_key) AS learning_teams,
    COUNT(*) FILTER (WHERE email IS NULL) AS unmapped_event_rows,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS latest_event_time
FROM silver_moodle_learning_events;
```

Kiểm tra grain để chắc chắn join không làm nhân đôi log:

```sql
SELECT
    COUNT(*) AS silver_rows,
    COUNT(DISTINCT bronze_event_id) AS distinct_bronze_events,
    COUNT(*) - COUNT(DISTINCT bronze_event_id) AS duplicated_bronze_events
FROM silver_moodle_learning_events;
```

Xem thử vài dòng đã được map:

```sql
SELECT
    event_time,
    full_name,
    email,
    team_name,
    activity_type,
    activity_name,
    event_name
FROM silver_moodle_learning_events
ORDER BY event_time DESC
LIMIT 20;
```

Bài tập nhỏ: hãy sửa câu SQL cuối để chỉ xem một team cụ thể, ví dụ `Fishomic`, bằng điều kiện `WHERE team_name = 'Fishomic'`.
## Cập Nhật Triển Khai: Log Export Mới, Submission Signals Và Activity Dimension
Ngày 2026-09-09, đã kiểm tra file log mới:

```text
example/logs_SANDBOX2026_20260909-1639.csv
```

Quan sát nguồn:

```text
file cũ = 3691 dòng
file mới = 4191 dòng
dòng trùng với file cũ = 3691
dòng mới thực sự = 500
```

Quyết định kỹ thuật: đổi khóa chống trùng log sang hash logic v2, không phụ thuộc vào tên file export. Điều này mô phỏng đúng bài toán thực tế khi Moodle export log theo cửa sổ thời gian chồng lấn.

Kết quả import file mới:

```text
row_count = 4191
inserted_count = 494
duplicate_count = 3521
excluded_count = 176
failed_count = 0
time_max = 2026-09-09 16:39:07
```

### Quy Tắc Tín Hiệu Tiến Độ V0
Trong `silver_moodle_learning_events`, thêm các cột:

```text
is_access_event
is_submission_event
is_submission_final_event
progress_signal_type
```

Quy tắc:

```text
access = người học xem khóa học, module, section, H5P hoặc trang submission.
submission_work = người học tạo/cập nhật/upload nội dung bài nộp nhưng chưa chắc đã submit cuối.
submission_final = người học đã bấm nộp bài chính thức.
```

Event được xem là hoàn thành submission v0:

```text
A submission has been submitted.
```

Không xem các event sau là hoàn thành cuối:

```text
Submission created.
Submission updated.
A file has been uploaded.
An online text has been uploaded.
```

Vì các event này chỉ cho thấy người học đang thao tác bản nháp hoặc upload/lưu nội dung.

Kết quả Silver sau import:

```text
learning_event_rows = 1948
learning_users = 53
matched_learning_emails = 53
learning_teams = 16
unmapped_event_rows = 0
duplicated_bronze_events = 0
```

Phân bố tín hiệu:

```text
access = 1905 event rows, 53 users
submission_work = 35 event rows, 1 user
submission_final = 8 event rows, 1 user
```

Submit final hiện tại:

```text
Nguyễn Bá Lộc - AI quét drone
MILESTONE 1 SUBMISSION = 2 events
MILESTONE 2 SUBISSMION = 2 events
MILESTONE 3 SUBMISSION = 1 event
MILESTONE 4 SUBMISSION = 3 events
```

### Dimension `dim_moodle_course_activities`
Đã tạo view:

```text
dim_moodle_course_activities
```

Grain:

```text
Một dòng = một Moodle course module id.
```

Cột chính:

```text
moodle_course_module_id
moodle_course_id
activity_type
activity_name
activity_type_key
activity_name_key
is_submission_activity
is_learning_material
total_event_rows
learning_event_rows
unique_learning_users
submission_final_event_rows
unique_submitters
first_seen_at
last_seen_at
```

Kết quả kiểm chứng:

```text
total_activities = 59
submission_activities = 17
learning_materials = 29
submission_final_event_rows = 8
global_unique_submitters = 1
```

### SQL Thực Hành Trong DBeaver
Kiểm tra Silver:

```sql
SELECT
    progress_signal_type,
    COUNT(*) AS event_rows,
    COUNT(DISTINCT email) AS unique_users
FROM silver_moodle_learning_events
GROUP BY progress_signal_type
ORDER BY event_rows DESC;
```

Xem các bài đã submit chính thức:

```sql
SELECT
    full_name,
    email,
    team_name,
    activity_name,
    moodle_course_module_id,
    COUNT(*) AS submit_events,
    MAX(event_time) AS latest_submit_at
FROM silver_moodle_learning_events
WHERE is_submission_final_event = TRUE
GROUP BY
    full_name,
    email,
    team_name,
    activity_name,
    moodle_course_module_id
ORDER BY latest_submit_at DESC;
```

Kiểm tra dimension activity:

```sql
SELECT
    moodle_course_module_id,
    activity_type,
    activity_name,
    is_submission_activity,
    is_learning_material,
    learning_event_rows,
    unique_learning_users,
    submission_final_event_rows,
    unique_submitters
FROM dim_moodle_course_activities
ORDER BY activity_type, activity_name;
```

Bài tập nhỏ: hãy sửa câu SQL cuối để chỉ lấy `Assignment` và sắp xếp theo `moodle_course_module_id`.
## Cập Nhật Triển Khai: Gold User Learning Summary
Đã tạo view:

```text
gold_user_learning_summary
```

Grain:

```text
Một dòng = một participant Moodle trong một course.
```

Lý do chọn grain này: dashboard quản lý cần thấy cả người chưa bắt đầu học. Vì vậy Gold phải lấy `int_moodle_user_identity_map` làm base rồi `LEFT JOIN` sang Silver. Nếu lấy Silver làm base thì chỉ còn những người đã có log.

Nguồn dữ liệu:

```text
int_moodle_user_identity_map
  -> left join silver_moodle_learning_events theo email
  -> tổng hợp access, activity đã xem, submission work, submission final
```

Cột chính:

```text
snapshot_date
moodle_course_id
participant_id
registration_id
moodle_user_id
full_name
email
team_name
identity_status
has_ever_accessed
first_access_at
last_access_at
days_since_last_access
learning_event_count
access_event_count
viewed_activity_count
active_days_count
submission_event_count
submission_work_event_count
submission_final_event_count
submitted_activity_count
submitted_activity_names
latest_submission_at
has_submitted
current_learning_status
```

Định nghĩa trạng thái v0:

```text
not_started = chưa có learning event nào
submitted = có ít nhất một event A submission has been submitted.
active = đã từng học và last_access_at nằm trong 7 ngày gần nhất
inactive = đã từng học nhưng quá 7 ngày chưa quay lại
```

Kết quả kiểm chứng ngày 2026-09-09:

```text
total_users = 113
accessed_users = 53
not_started_users = 60
submitted_users = 1
active_teams = 16
total_teams_in_gold = 22
```

Phân bố trạng thái:

```text
not_started = 60
active = 50
inactive = 2
submitted = 1
```

### SQL Thực Hành Trong DBeaver
Kiểm tra tổng quan Gold:

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_users,
    COUNT(*) FILTER (WHERE has_ever_accessed = FALSE) AS not_started_users,
    COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_users,
    COUNT(DISTINCT team_name_key) FILTER (WHERE has_ever_accessed = TRUE) AS active_teams,
    COUNT(DISTINCT team_name_key) AS total_teams_in_gold
FROM gold_user_learning_summary;
```

Xem phân bố trạng thái:

```sql
SELECT
    current_learning_status,
    COUNT(*) AS user_count
FROM gold_user_learning_summary
GROUP BY current_learning_status
ORDER BY user_count DESC, current_learning_status;
```

Xem người đã submit:

```sql
SELECT
    full_name,
    email,
    team_name,
    submitted_activity_count,
    submitted_activity_names,
    latest_submission_at
FROM gold_user_learning_summary
WHERE has_submitted = TRUE
ORDER BY latest_submission_at DESC;
```

Xem những người chưa bắt đầu:

```sql
SELECT
    full_name,
    email,
    team_name,
    current_learning_status
FROM gold_user_learning_summary
WHERE has_ever_accessed = FALSE
ORDER BY team_name, full_name;
```

Bài tập nhỏ: hãy sửa câu SQL `not_started` để đếm số người chưa bắt đầu theo từng team.
## Gold: Registered User Learning Summary

View: `gold_registered_user_learning_summary`

Mục tiêu: tạo bảng tổng hợp tiến độ học tập chỉ cho người đăng ký hợp lệ của chương trình Sandbox. View này khác với `gold_user_learning_summary`: view cũ lấy Moodle participants làm base để audit toàn bộ Moodle, còn view mới lấy `registrations` làm base để dashboard chương trình không bị phình số do admin, mentor, user test hoặc participant ngoài danh sách đăng ký.

Grain:

```text
một dòng = một registration_id hợp lệ
```

Nguồn dữ liệu:

```text
registrations
int_moodle_user_identity_map
silver_moodle_learning_events
```

Các chỉ số đã kiểm chứng ngày 2026-09-09:

```text
total_registered_users = 101
mapped_to_moodle_users = 101
accessed_users = 47
not_started_users = 54
submitted_users = 1
total_registered_teams = 22
active_registered_teams = 16
```

SQL thực hành trong DBeaver:

```sql
SELECT
    COUNT(*) AS total_registered_users,
    COUNT(*) FILTER (WHERE has_moodle_participant = TRUE) AS mapped_to_moodle_users,
    COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_users,
    COUNT(*) FILTER (WHERE has_ever_accessed = FALSE) AS not_started_users,
    COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_users,
    COUNT(DISTINCT team_name_key) FILTER (
        WHERE team_name_key IS NOT NULL
    ) AS total_registered_teams,
    COUNT(DISTINCT team_name_key) FILTER (
        WHERE has_ever_accessed = TRUE
          AND team_name_key IS NOT NULL
    ) AS active_registered_teams
FROM gold_registered_user_learning_summary;
```

Bài tập nhỏ cho người dùng: sửa câu SQL trên để đếm `not_started_users` theo từng `team_name`, sau đó so sánh team nào đã có người học và team nào chưa có ai bắt đầu.
## Gold: Team Learning Summary

View: `gold_team_learning_summary`

Mục tiêu: tổng hợp tiến độ học tập từ cấp người dùng đăng ký hợp lệ lên cấp đội. View này là nền cho dashboard filter theo team.

Kết quả kiểm chứng ngày 2026-09-09:

```text
total_teams = 22
active_teams = 16
not_started_teams = 6
submitted_teams = 1
registered_team_users = 83
accessed_team_users = 36
```

Grain:

```text
một dòng = một team_name_key hợp lệ
```

Câu hỏi business mà view này trả lời:

```text
Đội nào đã có người học?
Đội nào chưa ai bắt đầu?
Đội nào đã có người nộp submission?
Đội nào có dấu hiệu cần được nhắc nhở?
Mỗi đội đã chạm tới bao nhiêu activity khác nhau?
```

Các cột chính:

```text
team_name
registered_users
accessed_users
not_started_users
active_users
inactive_users
submitted_users
viewed_activity_count
submitted_activity_count
learning_event_count
current_team_learning_status
last_access_at
```

SQL thực hành trong DBeaver:

```sql
SELECT
    team_name,
    registered_users,
    accessed_users,
    not_started_users,
    submitted_users,
    viewed_activity_count,
    submitted_activity_count,
    current_team_learning_status,
    last_access_at
FROM gold_team_learning_summary
ORDER BY
    has_any_submission DESC,
    has_any_access DESC,
    accessed_users DESC,
    team_name;
```

Bài tập nhỏ cho người dùng: thêm một cột tính `access_rate` bằng `accessed_users * 100.0 / registered_users`, rồi sắp xếp để tìm các đội có tỷ lệ học thấp nhất.
## Gold: Individual Learning Summary

View: `gold_individual_learning_summary`

Mục tiêu: tạo lát cắt Gold riêng cho thí sinh tham gia cá nhân. View này dùng cho dashboard filter `individual`, còn trường hợp theo đội dùng `gold_team_learning_summary`.

Kết quả kiểm chứng ngày 2026-09-09:

```text
total_individuals = 18
mapped_to_moodle_users = 18
individuals_with_moodle_group = 0
accessed_individuals = 11
not_started_individuals = 7
submitted_individuals = 0
```

Grain:

```text
một dòng = một registration_id cá nhân
```

Câu hỏi business mà view này trả lời:

```text
Có bao nhiêu thí sinh cá nhân đã bắt đầu học?
Bao nhiêu thí sinh cá nhân vẫn chưa có hoạt động nào?
Có cá nhân nào đã nộp submission chưa?
Có cá nhân nào đã được thêm vào Moodle group không?
```

Cột quan trọng:

```text
full_name
email
moodle_group_name
individual_group_status
has_ever_accessed
viewed_activity_count
submitted_activity_count
learning_event_count
current_learning_status
last_access_at
```

SQL thực hành trong DBeaver:

```sql
SELECT
    full_name,
    email,
    individual_group_status,
    has_ever_accessed,
    viewed_activity_count,
    submitted_activity_count,
    current_learning_status,
    last_access_at
FROM gold_individual_learning_summary
ORDER BY
    has_ever_accessed DESC,
    viewed_activity_count DESC,
    full_name;
```

Bài tập nhỏ cho người dùng: viết thêm một câu SQL đếm số cá nhân theo `current_learning_status`, sau đó đối chiếu với endpoint `/api/v1/moodle-logs/gold-individual-summary`.
## Semantic API: Learning Dashboard Overview

Endpoint:

```text
GET /api/v1/moodle-logs/learning-dashboard-overview
```

Mục tiêu: cung cấp một nguồn dữ liệu tổng hợp cho tab overview của dashboard học tập. Endpoint này không thay thế các Gold view, mà đóng vai trò gom dữ liệu đã được định nghĩa sẵn để frontend không phải tự viết lại logic business.

Nguồn dữ liệu:

```text
gold_registered_user_learning_summary
gold_team_learning_summary
gold_individual_learning_summary
dim_moodle_course_activities
silver_moodle_learning_events
```

Các nhóm dữ liệu trả về:

```text
registered_summary
team_summary
individual_summary
activity_type_summary
top_viewed_activities
low_attention_activities
submission_activities
recent_submissions
submitted_teams
```

Kết quả kiểm chứng ngày 2026-09-09:

```text
total_registered_users = 101
accessed_users = 47
not_started_users = 54
submitted_users = 1
total_teams = 22
active_teams = 16
not_started_teams = 6
submitted_teams = 1
total_individuals = 18
accessed_individuals = 11
not_started_individuals = 7
```

SQL thực hành trong DBeaver để kiểm tra activity ít chú ý:

```sql
SELECT
    d.moodle_course_module_id,
    COALESCE(d.activity_type, 'unknown') AS activity_type,
    d.activity_name,
    COUNT(u.email) FILTER (WHERE e.is_access_event = TRUE) AS access_event_count,
    COUNT(DISTINCT u.email) FILTER (WHERE e.is_access_event = TRUE) AS unique_viewers
FROM dim_moodle_course_activities d
LEFT JOIN silver_moodle_learning_events e
    ON d.moodle_course_module_id = e.moodle_course_module_id
LEFT JOIN gold_registered_user_learning_summary u
    ON LOWER(TRIM(e.email)) = u.email
WHERE d.is_learning_material = TRUE
GROUP BY
    d.moodle_course_module_id,
    COALESCE(d.activity_type, 'unknown'),
    d.activity_name
ORDER BY unique_viewers ASC, access_event_count ASC, activity_name;
```

## Semantic API: Chi Tiết Hoạt Động Theo Đội

Endpoint:

```text
GET /api/v1/moodle-logs/team-activities-detail?team_name_key=...
```

Mục tiêu: khi người quản lý chọn một đội trên bảng điều khiển học tập, endpoint trả về đầy đủ thành viên của đội và các hoạt động Moodle thực tế đã được ghi nhận cho từng người.

Nguồn dữ liệu:

```text
gold_team_learning_summary
gold_registered_user_learning_summary
silver_moodle_learning_events
```

Grain của dữ liệu trả về:

```text
team: một dòng tổng quan đội
members: một dòng cho mỗi thành viên đăng ký trong đội
members.activities: một dòng cho mỗi cặp thành viên và Moodle course module đã có log
```

Lý do thiết kế:

```text
Gold team summary trả lời câu hỏi đội nào cần xem.
Gold registered user summary giữ đủ cả thành viên chưa bắt đầu học.
Silver learning events cho biết từng thành viên đã thực sự xem hoặc nộp hoạt động nào.
```

Quy tắc hiển thị v0:

```text
Những activity hoặc H5P không hiển thị nghĩa là chưa có log cho hoạt động đó trong dữ liệu hiện tại.
```

SQL thực hành trong DBeaver:

```sql
SELECT
    u.team_name,
    u.full_name,
    u.email,
    u.current_learning_status,
    e.moodle_course_module_id,
    e.activity_type,
    e.activity_name,
    COUNT(*) AS event_count,
    COUNT(*) FILTER (WHERE e.is_access_event = TRUE) AS access_event_count,
    COUNT(*) FILTER (WHERE e.is_submission_final_event = TRUE) AS submission_final_event_count,
    MIN(e.event_time) AS first_access_at,
    MAX(e.event_time) AS last_access_at
FROM gold_registered_user_learning_summary u
LEFT JOIN silver_moodle_learning_events e
    ON LOWER(TRIM(e.email)) = u.email
WHERE u.team_name_key = 'dien team_name_key vao day'
GROUP BY
    u.team_name,
    u.full_name,
    u.email,
    u.current_learning_status,
    e.moodle_course_module_id,
    e.activity_type,
    e.activity_name
ORDER BY
    u.full_name,
    last_access_at DESC NULLS LAST;
```

Bài tập nhỏ: chọn một `team_name_key` từ bảng `gold_team_learning_summary`, thay vào điều kiện `WHERE`, rồi kiểm tra thành viên nào có `moodle_course_module_id` là `NULL`. Những dòng đó là thành viên chưa có hoạt động trong Silver.
