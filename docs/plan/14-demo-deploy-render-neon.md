# Kế Hoạch Deploy Demo Render + Neon

Ngày tạo: 2026-09-09

Mục tiêu của bước này là đưa bản demo ThinkSpace Management lên một URL công khai để manager có thể xem trước dashboard. Đây là bản demo, chưa phải production thật.

## Quyết Định V0

Chọn Render cho web service và Neon cho PostgreSQL.

Lý do:

- App hiện tại là FastAPI + static frontend, Render chạy Python web service khá trực tiếp.
- App đã đọc database qua biến môi trường `DATABASE_URL`, nên có thể trỏ sang Neon mà không cần sửa logic core.
- Render có URL dạng `onrender.com`, phù hợp cho demo nhanh.
- Neon cung cấp PostgreSQL managed, tiện hơn việc giữ database trong container local.

Không chọn GitHub Pages cho bản này vì app cần backend FastAPI và database. GitHub Pages chỉ phù hợp khi frontend hoàn toàn static.

## Kiến Trúc Demo

```text
Người xem dashboard
  -> Render Web Service
  -> FastAPI + static files
  -> Neon PostgreSQL
```

Ở bản demo ngày mai, dữ liệu có thể import từ file mẫu/local trước. Không đưa Moodle token production lên cloud nếu chưa cần ingestion tự động.

## Cấu Hình Render Đề Xuất

Tạo Web Service dạng Python từ GitHub repository.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn src.app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables tối thiểu:

```text
APP_ENV=demo
APP_DEBUG=false
DATABASE_URL=<connection string PostgreSQL của Neon>
```

Nếu chỉ show dashboard học tập và không upload/onboard user thật trong bản demo, tạm thời chưa cần cấu hình:

```text
MOODLE_BASE_URL
MOODLE_TOKEN
GOOGLE_SERVICE_ACCOUNT_FILE
```

## Cấu Hình Neon Đề Xuất

Tạo một database PostgreSQL riêng cho demo, ví dụ:

```text
thinkspace_demo
```

Sau đó lấy connection string dạng PostgreSQL và đưa vào biến `DATABASE_URL` trên Render.

Lưu ý bảo mật:

- Không commit connection string vào Git.
- Không lưu Moodle token hoặc Google service account trong docs.
- Nếu cần secret file Google sau này, dùng cơ chế Secret Files hoặc Environment Variables của nền tảng deploy.

## Checklist Người Dùng Thực Hành

1. Push code mới nhất lên GitHub.
2. Tạo project/database trên Neon.
3. Copy connection string của Neon.
4. Tạo Web Service trên Render từ GitHub repo.
5. Nhập build command và start command ở trên.
6. Thêm `DATABASE_URL`, `APP_ENV`, `APP_DEBUG`.
7. Deploy và mở URL `onrender.com`.
8. Kiểm tra endpoint:

```text
/health
/api/v1/moodle-logs/learning-dashboard-overview
```

## Seed Dữ Liệu Demo Từ Local Sang Neon

Không upload lại file đăng ký lên cloud demo nếu không cần gọi Moodle. Với demo dashboard, cách đúng là seed dữ liệu từ PostgreSQL local sang Neon.

Script hỗ trợ:

```text
scripts/seed-neon-demo.ps1
```

Cách chạy trong PowerShell:

```powershell
$env:TARGET_DATABASE_URL="connection string Neon"
.\scripts\seed-neon-demo.ps1 -ResetTarget
Remove-Item Env:\TARGET_DATABASE_URL
```

Nếu Neon hiển thị hai connection string, ưu tiên dùng `Direct connection` cho bước seed dữ liệu. Connection pooler vẫn phù hợp cho app đọc dashboard, nhưng thao tác restore schema/data nên dùng direct connection khi có thể.

Script sẽ:

- Dump schema của các bảng chính từ PostgreSQL local.
- Dump data bằng `--column-inserts` để tránh lệch thứ tự cột giữa local và Neon.
- Reset schema `public` trên Neon nếu truyền `-ResetTarget`.
- Restore schema và data lên Neon.
- Gọi code app để tạo lại các view phân tích `int/silver/gold`.
- Kiểm tra số dòng của `registrations`, `raw_moodle_participants`, `bronze_moodle_log_events`.

Không commit connection string Neon vào Git. Chỉ set tạm bằng biến môi trường trong terminal.

Sau khi seed xong, mở lại app Render và bấm `Ctrl + F5` để kiểm tra dashboard.

## Rủi Ro Demo

- Nếu database Neon trống, dashboard sẽ chưa có số liệu cho đến khi import dữ liệu.
- Nếu deploy bằng Dockerfile hiện tại, Dockerfile đang bind port `8000`. Render thường nên dùng `$PORT`, nên bản demo khuyến nghị chạy Python native trước.
- Nếu upload dữ liệu trên cloud demo, cần đảm bảo không dùng dữ liệu nhạy cảm hoặc credentials thật khi chưa thống nhất quyền truy cập.
- Nếu dùng file dump data-only không có tên cột, restore có thể lỗi khi thứ tự cột giữa local và Neon lệch nhau. Vì vậy script seed demo dùng `--column-inserts`.

## Bài Tập Nhỏ Cho Bạn

Khi deploy xong, bạn mở Render logs và kiểm tra dòng chạy Uvicorn có bind đúng `0.0.0.0` và đúng port Render cấp hay không. Đây là kỹ năng rất thực tế khi deploy backend.
