# Kế Hoạch Kiến Trúc

## Kiến Trúc Cốt Lõi Cho MVP
MVP sẽ đi theo kiến trúc pipeline phân lớp, đồng bộ. Ứng dụng là một service FastAPI đóng vai trò điều phối luồng xử lý.

```text
Google Sheet
    ↓
Tích hợp Google Sheets (Extract - Trích xuất)
    ↓
Model Member chuẩn (Transform - Chuyển đổi)
    ↓
Kiểm tra tính hợp lệ (Validate - Xác thực)
    ↓
Định danh người dùng (Find/Match - Tìm/Khớp)
    ↓
Tích hợp Moodle (Tạo user nếu cần)
    ↓
Kiểm tra trạng thái ghi danh (Check)
    ↓
Ghi danh nếu cần (Action)
    ↓
Kết quả trả về (Output - Có cấu trúc)
```

## Trách Nhiệm Của Từng Lớp
- **Lớp API (API Layer)**: Cung cấp các endpoint (ví dụ: FastAPI routes) để kích hoạt quá trình xử lý hàng loạt (batch processing).
- **Lớp Dịch Vụ (Service Layer)**: Điều phối logic nghiệp vụ, parse dữ liệu, validate, khớp định danh, và quản lý luồng công việc.
- **Lớp Tích Hợp (Integration Layer)**: Xử lý tương tác với API bên ngoài. 
  - `google_sheets.py`: Đọc dữ liệu.
  - `moodle.py`: Đóng gói (abstract) các lệnh gọi REST/Web Services của Moodle.
- **Models**: Các schema của Pydantic (ví dụ: model chuẩn `Member`) đại diện cho trạng thái bên trong ứng dụng.
- **Validation**: Kiểm tra các trường bắt buộc, trùng lặp email/ID, định dạng đúng trước khi xử lý.
- **Cấu hình (Configuration)**: Sử dụng `pydantic-settings` để quản lý an toàn các biến môi trường.
- **Logging**: Ghi lại nhật ký kiểm toán và lỗi mà không làm dừng toàn bộ tiến trình.
- **Tests**: Kiểm tra tính đúng đắn trên nhiều case khác nhau (người dùng mới, cũ, lỗi API).

## Các Nguyên Tắc Kiến Trúc
- **Sự đơn giản**: Không sử dụng hạ tầng không cần thiết (không Airflow, Redis, hoặc PostgreSQL cho phiên bản hoạt động đầu tiên).
- **Tính module hóa**: Logic nghiệp vụ phải tách biệt với các tích hợp bên ngoài.
- **Dễ test**: Dễ dàng mock (giả lập) các phản hồi từ Google Sheets và Moodle API.
- **Tính lũy đẳng (Idempotency)**: Chạy cùng một tập dữ liệu nhiều lần vẫn trả về cùng một kết quả cuối mà không nhân bản tài khoản hay tạo trùng lặp ghi danh.
- **Phân tách trách nhiệm (Separation of Concerns)**: Việc tạo người dùng phải hoàn toàn độc lập với việc ghi danh khóa học.
