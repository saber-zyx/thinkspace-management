# Đánh Giá Trạng Thái Hiện Tại

## Cấu Trúc Repository
- `.agents/` - Thư mục trống
- `agents/` - Chứa `rules.md` và `settings.json` (Luật cho AI).
- `docs/plan/` - Được tạo mới để lưu các tài liệu lập kế hoạch cho dự án.
- `skills/` - Từng chứa hàng ngàn kỹ năng AI chung chung (`claude_skills`, `skills`, `superpower_skills`). Đã được dọn dẹp và xóa do không phục vụ cho MVP hiện tại (Google Sheet, Moodle, FastAPI).
- `src/` - Trống, chờ triển khai code.
- `tests/` - Trống, chờ viết tests.

## Công Nghệ
- **Python**: Ngôn ngữ cốt lõi.
- **FastAPI / Pydantic / httpx**: Được đề xuất cho backend (chưa cài đặt).
- **Docker**: Các file `Dockerfile` và `compose.yaml` (rất cơ bản) đã được tạo.
- **PostgreSQL**: Có trong `.env.example`, nhưng đã thống nhất trì hoãn đến khi luồng làm việc MVP cốt lõi hoàn thiện.

## Các File Đã Có
- `README.md` (Ngữ cảnh sản phẩm/dự án, tầm nhìn, phạm vi MVP)
- `AGENTS.md` (Hướng dẫn vận hành dành cho các AI coding agent)
- `agents/rules.md` và `agents/settings.json` (Quyền truy cập nghiêm ngặt cho agents)
- `requirements.txt` (Chứa các thư viện cần thiết cho MVP)
- `.env.example` (Chứa cấu hình PostgreSQL, Google và Moodle)
- `.gitignore`, `.dockerignore` (Cấu hình bỏ qua file tiêu chuẩn, đã được thiết lập đúng)

## Các Vấn Đề Được Phát Hiện & Nợ Kỹ Thuật (Technical Debt)
- **Thư mục skills bị phình to**: Hơn 1000 kỹ năng không liên quan. Hành động: Đã xóa toàn bộ.
- **Cấu hình rỗng**: Dockerfile và compose.yaml trước đó hoàn toàn trống. Hành động: Đã tạo file cơ bản, giữ đơn giản cho MVP.
- **Thiếu Cấu Hình Ứng Dụng**: `.env.example` thiếu cấu hình Google và Moodle. Hành động: Đã thêm.
- **Dependencies**: `requirements.txt` thiếu thư viện thực tế. Hành động: Đã cập nhật với stack ban đầu (fastapi, uvicorn, pydantic, v.v.).

## Các Bước Dọn Dẹp Đã Thực Hiện
- Tạo cấu trúc `docs/plan/` nền tảng.
- Xóa bỏ các kỹ năng AI không liên quan để giữ context sạch sẽ và tập trung vào MVP tích hợp Moodle.
- Chuẩn bị `.env.example` với các biến môi trường cần thiết.
- Chuẩn bị `requirements.txt`.

## Các Phần Cố Tình Giữ Nguyên
- Chưa triển khai các thiết lập Docker/Compose phức tạp (giữ đơn giản cho MVP).
- Chưa thiết kế cấu trúc database (PostgreSQL thuộc phạm vi tương lai).
