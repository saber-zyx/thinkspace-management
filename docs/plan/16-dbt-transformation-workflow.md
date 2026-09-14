# Quy Trình dbt Cho Transform Dữ Liệu Moodle

Ngày tạo: 2026-09-10

## Mục Tiêu

Đưa `dbt` vào dự án để quản lý phần transform dữ liệu theo cách gần với quy trình Data Engineer/Analytics Engineer thực tế hơn.

Trước bước này, các view `int/silver/gold` đang được tạo bằng Python startup hook trong `src/app/core/database.py`. Cách đó chạy được và phù hợp để dựng MVP nhanh, nhưng khi pipeline lớn hơn thì SQL transform nên được tách ra thành dbt models để dễ đọc, kiểm thử và version control.

## Tool Được Thêm

- `dbt-postgres`: adapter để dbt chạy trên PostgreSQL/Neon, được cài từ `requirements-data.txt`.
- PostgreSQL/Neon: warehouse cho demo.
- DBeaver: nơi người dùng thực hành đọc SQL, kiểm tra count và debug dữ liệu.

## Cấu Trúc Mới

```text
analytics/dbt_thinkspace/
  dbt_project.yml
  profiles.example.yml
  models/
    sources.yml
    staging/
      stg_registrations.sql
      stg_moodle_participants.sql
    intermediate/
      int_moodle_user_identity_map.sql
      schema.yml
    silver/
      silver_moodle_learning_events.sql
      schema.yml
    marts/
      learning/
        gold_registered_user_learning_summary.sql
        schema.yml
```

## Model Đầu Tiên

Model đầu tiên là:

```text
int_moodle_user_identity_map
```

Grain:

```text
một dòng = một Moodle participant đã được map sang registration nếu email khớp
```

Lý do chọn model này trước:

- Đây là điểm nối quan trọng giữa Moodle và dữ liệu đăng ký.
- Nó giải quyết trực tiếp lỗi dữ liệu duplicate/mapping mà dự án đã gặp.
- Nó dễ kiểm chứng bằng SQL trong DBeaver.

## Cách Chạy Local

Cài dependency:

```powershell
python -m pip install -r requirements-data.txt
```

Set biến môi trường cho database local:

```powershell
$env:DBT_POSTGRES_HOST="localhost"
$env:DBT_POSTGRES_PORT="5433"
$env:DBT_POSTGRES_DB="thinkspacedb"
$env:DBT_POSTGRES_USER="thinkspace"
$env:DBT_POSTGRES_PASSWORD="password123"
```

Chạy dbt:

```powershell
cd analytics\dbt_thinkspace
Copy-Item profiles.example.yml profiles.yml
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..\..
```

Các model dbt sẽ được tạo trong schema:

```text
analytics
```

Các bảng nguồn của app vẫn nằm trong schema:

```text
public
```

Tách như vậy giúp ta thử dbt mà chưa làm ảnh hưởng trực tiếp tới các view `public` đang được dashboard dùng.

Sau khi làm xong, có thể xóa biến môi trường:

```powershell
Remove-Item Env:\DBT_POSTGRES_HOST
Remove-Item Env:\DBT_POSTGRES_PORT
Remove-Item Env:\DBT_POSTGRES_DB
Remove-Item Env:\DBT_POSTGRES_USER
Remove-Item Env:\DBT_POSTGRES_PASSWORD
```

## SQL Bạn Cần Tự Kiểm Tra Trong DBeaver

Sau khi chạy `dbt run`, mở DBeaver và chạy:

```sql
SELECT
    identity_status,
    COUNT(*) AS row_count
FROM analytics.int_moodle_user_identity_map
GROUP BY identity_status
ORDER BY row_count DESC, identity_status;
```

Kỳ vọng hiện tại:

```text
matched_same_team
matched_without_moodle_group
unmatched_registration
matched_team_conflict
```

Nếu count khác nhiều so với view cũ, ta sẽ debug từ staging:

```sql
SELECT COUNT(*) FROM analytics.stg_moodle_participants;
SELECT COUNT(*) FROM analytics.stg_registrations;
```

## Bài Tập Nhỏ

Bạn hãy đọc file:

```text
analytics/dbt_thinkspace/models/intermediate/int_moodle_user_identity_map.sql
```

Sau đó tự viết lại bằng lời:

1. Bảng này lấy dữ liệu từ đâu?
2. Nó join bằng khóa nào?
3. Vì sao `identity_status` cần thiết cho dashboard?

Đây là cách luyện tư duy phỏng vấn: không chỉ nói “em dùng dbt”, mà nói được “em dùng dbt để chuẩn hóa và kiểm soát identity mapping giữa Moodle logs và registration system”.

## Model Silver Đầu Tiên

Model tiếp theo là:

```text
silver_moodle_learning_events
```

Grain:

```text
một dòng = một Moodle learning event đã được map với participant/registration nếu tìm được danh tính
```

Model này chuyển logic `public.silver_moodle_learning_events` từ Python startup hook sang dbt trong schema `analytics`.

Điểm cần học:

- `source('app_public', 'bronze_moodle_log_events')`: đọc từ bảng bronze do app nạp.
- `ref('int_moodle_user_identity_map')`: dùng output của model dbt trước đó.
- `progress_signal_type`: biến log thô thành tín hiệu học tập dễ phân tích như `access`, `submission_work`, `submission_final`.
- `dbt test`: kiểm tra grain và chất lượng dữ liệu, ví dụ `bronze_event_id` không null/unique.

SQL kiểm chứng sau khi chạy:

```sql
SELECT COUNT(*) FROM public.silver_moodle_learning_events;
SELECT COUNT(*) FROM analytics.silver_moodle_learning_events;
```

Hai con số nên bằng nhau nếu model dbt đang phản ánh cùng logic với view app hiện tại.

Kết quả kiểm chứng local ngày 2026-09-11:

```text
public.silver_moodle_learning_events: 8,787 dòng
analytics.silver_moodle_learning_events: 8,787 dòng
dbt test: 27 pass
```

Phân phối `progress_signal_type`:

```text
access: 7,330
submission_final: 1,414
submission_work: 43
```

Lưu ý: dashboard hiện vẫn đọc view `public`. Model dbt đang chạy song song để học và kiểm chứng trước khi chuyển dashboard sang đọc `analytics` hoặc materialized mart.

## Gold Mart Đầu Tiên

Model gold đầu tiên là:

```text
gold_registered_user_learning_summary
```

Grain:

```text
một dòng = một thí sinh đăng ký chương trình
```

Model này tổng hợp từ:

- `stg_registrations`: danh sách đăng ký gốc đã chuẩn hóa.
- `int_moodle_user_identity_map`: ánh xạ Moodle participant với registration.
- `silver_moodle_learning_events`: các learning event đã chuẩn hóa.

Các chỉ số chính:

- `has_ever_accessed`: thí sinh đã từng có hoạt động hay chưa.
- `learning_event_count`: tổng event học tập.
- `access_event_count`: tổng event truy cập/xem.
- `viewed_activity_count`: số activity/module từng xem.
- `submission_final_event_count`: số event nộp bài hoàn tất.
- `current_learning_status`: `not_started`, `active`, `inactive`, hoặc `submitted`.

SQL kiểm chứng:

```sql
SELECT COUNT(*) FROM public.gold_registered_user_learning_summary;
SELECT COUNT(*) FROM analytics.gold_registered_user_learning_summary;
```

Và:

```sql
SELECT
    current_learning_status,
    COUNT(*) AS user_count
FROM analytics.gold_registered_user_learning_summary
GROUP BY current_learning_status
ORDER BY user_count DESC;
```

Kết quả kiểm chứng local ngày 2026-09-11:

```text
public.gold_registered_user_learning_summary: 112 dòng
analytics.gold_registered_user_learning_summary: 112 dòng
dbt test: 36 pass
```

Phân phối `current_learning_status`:

```text
active: 52
not_started: 59
submitted: 1
```

Điểm cần học:

- Gold mart không lưu toàn bộ log; nó rút gọn log thành trạng thái hiện tại của từng thí sinh.
- `registration_id` và `email` được test unique để bảo vệ grain một dòng cho một thí sinh.
- Dashboard hiện vẫn đọc schema `public`; schema `analytics` đang là bản dbt chạy song song để kiểm chứng trước khi đổi nguồn chính.

## Gold Project Mart

Model tiếp theo là:

```text
gold_project_learning_summary
```

Grain:

```text
một dòng = một dự án
```

Quy tắc tạo khóa dự án:

- Dự án đăng ký theo đội: dùng `team_name_key`.
- Dự án cá nhân: dùng `email`.

Điểm cần học:

- Đây là bước đổi grain từ thí sinh sang dự án.
- Một dự án đội có thể có nhiều thành viên, nhưng chỉ là một dòng trong mart dự án.
- `registered_users`, `accessed_users`, `submitted_users` là chỉ số thành viên bên trong dự án.
- `has_any_access` và `has_any_submission` là cờ boolean ở cấp dự án.

SQL kiểm chứng:

```sql
SELECT
    project_type,
    COUNT(*) AS projects,
    SUM(registered_users) AS registered_users,
    COUNT(*) FILTER (WHERE has_any_access = TRUE) AS active_projects,
    COUNT(*) FILTER (WHERE has_any_submission = TRUE) AS submitted_projects
FROM analytics.gold_project_learning_summary
GROUP BY project_type
ORDER BY project_type;
```

Kết quả kiểm chứng local ngày 2026-09-11:

```text
individual: 20 dự án, 20 thí sinh, 12 dự án đã hoạt động, 0 dự án đã nộp bài
team: 24 dự án, 92 thí sinh, 19 dự án đã hoạt động, 1 dự án đã nộp bài
dbt test: 44 pass
```

Phân phối `current_project_learning_status`:

```text
active: 30
not_started: 13
submitted: 1
```

## Gold Milestone Traction Mart

Model tiếp theo là:

```text
gold_milestone_traction_summary
```

Grain:

```text
một dòng = một milestone trên dashboard traction
```

Mart này trả lời câu hỏi:

- Với từng milestone, có bao nhiêu lượt xem guideline?
- Có bao nhiêu user duy nhất đã xem guideline?
- Có bao nhiêu log nộp bài hoàn tất?
- Có bao nhiêu dự án duy nhất đã nộp bài?

SQL kiểm chứng:

```sql
SELECT
    display_order,
    milestone_code,
    guideline_view_count,
    guideline_user_count,
    submission_done_count,
    submission_done_project_count
FROM analytics.gold_milestone_traction_summary
ORDER BY display_order;
```

Kết quả kiểm chứng local ngày 2026-09-11:

```text
Milestone 1: 190 guideline views, 4 users, 3 submitted, 1 dự án nộp
Milestone 2: 50 guideline views, 3 users, 2 submitted, 1 dự án nộp
Milestone 3: 50 guideline views, 2 users, 1 submitted, 1 dự án nộp
Milestone 4: 13 guideline views, 1 user, 3 submitted, 1 dự án nộp
Milestone 5: 27 guideline views, 2 users, 1 submitted, 1 dự án nộp
Final Submission: 80 guideline views, 2 users, 0 submitted, 0 dự án nộp
dbt test: 53 pass
```

Điểm cần học:

- `submission_done_count` là số log nộp bài, nên một dự án nộp nhiều lần có thể tăng số này.
- `submission_done_project_count` là số dự án duy nhất đã nộp, nên phù hợp hơn cho manager khi hỏi “bao nhiêu dự án đã nộp”.
- `submitted_projects` là chi tiết drill-down để dashboard mở modal xem dự án nào đã nộp.

## dbt Analytics Workflow v1

Tính đến ngày 2026-09-11, dbt project đã có đủ các lớp chính:

```text
Sources
  registrations
  raw_moodle_participants
  bronze_moodle_log_events
  raw_ueh_lms_course_enrollments

Staging
  stg_registrations
  stg_moodle_participants
  stg_ueh_lms_course_enrollments

Intermediate
  int_moodle_user_identity_map

Silver
  silver_moodle_learning_events

Gold / Marts
  dim_moodle_course_activities
  gold_user_learning_summary
  gold_registered_user_learning_summary
  gold_project_learning_summary
  gold_team_learning_summary
  gold_individual_learning_summary
  gold_daily_learning_interactions
  gold_key_activity_spotlights
  gold_pre_program_gate_summary
  gold_foundation_course_summary
  gold_ueh_lms_entrepreneurship_enrollment_summary
  gold_milestone_traction_summary
  gold_activity_type_summary
  gold_submission_activities_summary
```

Lệnh chạy workflow local:

```powershell
$env:DBT_POSTGRES_HOST='localhost'
$env:DBT_POSTGRES_PORT='5433'
$env:DBT_POSTGRES_DB='thinkspacedb'
$env:DBT_POSTGRES_USER='thinkspace'
$env:DBT_POSTGRES_PASSWORD='password123'

dbt run --profiles-dir .
dbt test --profiles-dir .
dbt docs generate --profiles-dir .
```

Kết quả kiểm chứng local:

```text
dbt run: 19/19 models pass
dbt test: 113/113 tests pass
dbt docs generate: tạo catalog thành công
```

SQL kiểm kê model trong DBeaver:

```sql
SELECT schemaname, viewname
FROM pg_views
WHERE schemaname = 'analytics'
ORDER BY viewname;
```

SQL kiểm tra các metric lõi:

```sql
SELECT 'registered_users' AS metric, COUNT(*)::numeric AS value
FROM analytics.gold_registered_user_learning_summary
UNION ALL
SELECT 'projects', COUNT(*)
FROM analytics.gold_project_learning_summary
UNION ALL
SELECT 'team_projects', COUNT(*)
FROM analytics.gold_project_learning_summary
WHERE project_type = 'team'
UNION ALL
SELECT 'individual_projects', COUNT(*)
FROM analytics.gold_project_learning_summary
WHERE project_type = 'individual'
UNION ALL
SELECT 'milestones', COUNT(*)
FROM analytics.gold_milestone_traction_summary
UNION ALL
SELECT 'key_spotlights', COUNT(*)
FROM analytics.gold_key_activity_spotlights;
```

Kết quả local hiện tại:

```text
registered_users: 112
projects: 44
team_projects: 24
individual_projects: 20
milestones: 6
key_spotlights: 4
```

Điểm cần học:

- dbt không ingest dữ liệu. App/script vẫn nạp raw/bronze.
- dbt chịu trách nhiệm transform: staging -> intermediate -> silver -> gold.
- Gold mart là nơi metric dashboard nên được định nghĩa rõ ràng.
- `dbt test` là lớp kiểm soát chất lượng dữ liệu, tương tự unit test cho data model.
- `dbt docs generate` giúp tạo lineage/catalog để giải thích project khi phỏng vấn.

Ranh giới hiện tại:

- Dashboard vẫn đọc schema `public` để tránh đổi runtime quá nhiều trong một bước.
- Schema `analytics` là bản dbt-first đã kiểm chứng local.
- Bước tiếp theo nên là refactor API sang đọc các mart `analytics`, hoặc tạo cơ chế deploy dbt sang Neon/Render.
# Cap Nhat Runtime dbt-First

Ngay cap nhat: 2026-09-11

Tu buoc nay, Learning Dashboard local da bat dau uu tien doc cac mart trong schema `analytics` do dbt tao ra. API dung helper `use_analytics_schema_if_available` de set `search_path = analytics, public`. Neu schema `analytics` chua ton tai hoac dbt chua build xong, API van fallback ve view `public` cu de dashboard khong bi sap.

Quy trinh van hanh local sau khi co file log/enrollment moi:

```powershell
$env:DBT_POSTGRES_HOST='localhost'
$env:DBT_POSTGRES_PORT='5433'
$env:DBT_POSTGRES_DB='thinkspacedb'
$env:DBT_POSTGRES_USER='thinkspace'
$env:DBT_POSTGRES_PASSWORD='password123'

cd analytics\dbt_thinkspace
dbt run --profiles-dir . --threads 1
dbt test --profiles-dir . --threads 1
cd ..\..
docker compose restart app
```

Ly do dung `--threads 1`: khi PostgreSQL local tao lai nhieu view phu thuoc nhau cung luc, dbt co the gap deadlock. Chay tuan tu cham hon mot chut nhung on dinh hon cho moi truong local.

Trang thai hien tai:

```text
FastAPI: giu vai tro API, upload/import, integration Moodle, frontend static.
dbt: giu vai tro transform staging -> intermediate -> silver -> gold.
PostgreSQL/Neon: luu raw/bronze va chua analytics mart.
Dashboard: doc API, API uu tien mart dbt trong analytics.
```

# Cap Nhat dbt Mart v2 Cho Detail Dashboard

Ngay cap nhat: 2026-09-12

Learning Dashboard da duoc chuyen tiep sang dbt-first o cac phan detail va overview con sot. Cac model moi:

- `gold_top_viewed_activities`: xep hang activity co nhieu user/lượt xem.
- `gold_low_attention_activities`: tim activity co muc do chu y thap.
- `gold_recent_submissions`: danh sach log nop bai hoan tat gan day.
- `gold_submitted_projects`: danh sach du an da nop bai.
- `gold_learning_activity_detail`: chi tiet tung thi sinh trong tung activity Moodle.
- `gold_ueh_lms_entrepreneurship_enrollment_detail`: danh sach thi sinh Sandbox da match voi enrollment UEH LMS Entrepreneurship.

Quy trinh hien tai sau khi import log moi:

```powershell
cd analytics\dbt_thinkspace

$env:DBT_POSTGRES_HOST='localhost'
$env:DBT_POSTGRES_PORT='5433'
$env:DBT_POSTGRES_DB='thinkspacedb'
$env:DBT_POSTGRES_USER='thinkspace'
$env:DBT_POSTGRES_PASSWORD='password123'

dbt run --profiles-dir . --threads 1
dbt test --profiles-dir . --threads 1
```

SQL mau de ban tu test trong DBeaver:

```sql
SELECT COUNT(*) AS activity_detail_rows
FROM analytics.gold_learning_activity_detail;

SELECT activity_name, access_event_count, unique_viewers
FROM analytics.gold_top_viewed_activities
ORDER BY unique_viewers DESC, access_event_count DESC
LIMIT 10;
```

Trang thai kiem chung cua lan cap nhat nay:

```text
pytest tests/test_main.py -q: 28/28 pass
dbt parse --profiles-dir .: pass
dbt run --profiles-dir . --threads 1: 25/25 models pass
dbt test --profiles-dir . --threads 1: 139/139 tests pass
learning-dashboard-overview: data_schema = analytics
individual-activities-detail: doc duoc gold_learning_activity_detail
```

# Cap Nhat Cleanup Legacy View Trong FastAPI

Ngay cap nhat: 2026-09-12

Sau khi dbt da build on dinh, cac ham tao view analytics cu trong FastAPI startup da duoc xoa. Tu luc nay:

- FastAPI tao bang nguon, nhan upload/import, cung cap API va static frontend.
- dbt tao staging, intermediate, silver va gold mart trong schema `analytics`.
- Dashboard doc API; API uu tien schema `analytics`.

Quan trong: sau khi import file log moi, can chay lai dbt de cac mart analytics cap nhat:

```powershell
.\scripts\run-local-analytics-refresh.ps1
```

Script refresh local gom cac buoc: kiem tra Docker services, chay `dbt run`, chay `dbt test`, va goi API dashboard de xac nhan `data_schema = analytics`.

Mac dinh script them `--quiet` cho `dbt run` va `dbt test` de log gon hon khi van hanh hang ngay. Khi can hoc/debug tung model dbt, chay:

```powershell
.\scripts\run-local-analytics-refresh.ps1 -VerboseDbt
```

Trang thai kiem chung cleanup:

```text
pytest tests/test_main.py -q: 28/28 pass
dbt run --profiles-dir . --threads 1: 25/25 models pass
dbt test --profiles-dir . --threads 1: 139/139 tests pass
docker compose restart app: thanh cong
learning-dashboard-overview: data_schema = analytics
```

# Chuan Hoa Refresh Analytics Live

Ngay cap nhat: 2026-09-12

Sau khi local da on dinh, live Render/Neon duoc chuan hoa bang script rieng:

```powershell
$env:TARGET_DATABASE_URL="connection string Neon"
$env:RENDER_APP_BASE_URL="https://thinkspace-management.onrender.com"
.\scripts\run-live-analytics-refresh.ps1
```

Y nghia:

- Local refresh dung PostgreSQL local lam target dbt.
- Live refresh dung Neon lam target dbt.
- Ca hai deu build cung schema `analytics`, chay `dbt test`, roi kiem tra API dashboard doc `data_schema = analytics`.
- Live refresh khong reset du lieu, khong seed data, va khong import log. No chi lam moi cac mart analytics tren du lieu da co san trong Neon.

Khi can debug:

```powershell
.\scripts\run-live-analytics-refresh.ps1 -VerboseDbt
```

Khi chi muon build/test dbt tren Neon va bo qua API Render:

```powershell
.\scripts\run-live-analytics-refresh.ps1 -SkipApiCheck
```
