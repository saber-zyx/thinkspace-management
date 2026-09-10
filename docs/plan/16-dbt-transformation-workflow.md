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
