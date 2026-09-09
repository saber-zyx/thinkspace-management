# Kế Hoạch Tích Hợp (Integration Plan)

## 1. Tích Hợp Google Sheets
**Mục Đích**: Đọc dữ liệu thành viên từ các URLs được cung cấp.
**Cách Tiếp Cận**:
- Sử dụng Google Sheets API thông qua thư viện `google-api-python-client` hoặc các REST calls nhẹ tương đương.
- Xác thực (Authentication) bằng Service Account JSON (cấu hình trong file `.env`).
- **Lưu ý Quan Trọng Về Quyền Truy Cập (Permissions)**: Các file Google Sheet là do các đội thi/người tham gia tự tạo và sở hữu, sau đó chia sẻ quyền xem (Viewer) cho Ban tổ chức (BTC). Do đó, ứng dụng sẽ chỉ gọi API đọc (Read-only). Hệ thống phải xử lý khéo léo lỗi `403 Permission Denied` trong trường hợp team quên cấp quyền cho email của Service Account hoặc quên mở quyền "Anyone with the link can view".
- Đầu vào mục tiêu: URL + Tên Sheet (hoặc Index).
- Đầu ra: Danh sách thô các dictionaries.

## 2. Tích Hợp Moodle
**Mục Đích**: Cấp phát (provision) người dùng và xử lý việc ghi danh (enrollments).
**Cách Tiếp Cận**: 
- Dùng Moodle REST API / Web Services.
- Tạo một lớp trừu tượng (abstraction layer) riêng biệt `integrations/moodle.py` để đảm nhận toàn bộ các sắc thái đặc thù của Moodle API.

### Các Thông Tin Moodle Bắt Buộc Cần Có (Blockers)
Trước khi tiến hành code, những thông tin sau đây BẮT BUỘC PHẢI được xác nhận từ Quản trị viên Moodle (TUYỆT ĐỐI KHÔNG được tự giả định):
- Moodle base URL (URL gốc)
- Phiên bản Moodle
- REST API đã được bật chưa?
- Web Services đã được bật chưa?
- API token (với đầy đủ các quyền - permissions hợp lý)
- Role ID chuẩn dùng cho việc ghi danh học viên (student enrollment)
- Chính sách Mật khẩu (Moodle có tự tạo không? Có dùng SSO không? Có bắt buộc đổi mật khẩu ở lần đăng nhập đầu không?)
- Trường dữ liệu nào trong Moodle đang lưu MSSV (Student ID)? (ví dụ: `idnumber`, custom profile field?)
- Có hệ thống test/staging (sandbox) nào để dùng cho lúc code phát triển (development) không?
