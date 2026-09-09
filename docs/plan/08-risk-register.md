# Sổ Đăng Ký Rủi Ro (Risk Register)

| Rủi ro | Tác động | Giải pháp giảm thiểu |
|------|--------|------------|
| **Không có quyền truy cập Moodle API (Moodle API permission unavailable)** | Không thể tự động hóa việc cấp phát tài khoản hoặc ghi danh. | Phương án dự phòng (Fallback): tạo ra file CSV chuẩn của Moodle để quản trị viên có thể upload thủ công trong lúc chờ IT cấp quyền. |
| **Cấu trúc Google Sheet không nhất quán (Google Sheet schema inconsistent)** | Lỗi mapping dữ liệu hoặc crash chương trình. | Xây dựng một lớp validation mạnh; sử dụng fuzzy matching cho headers nếu cần, nhưng phải tuân thủ nghiêm ngặt việc ép kiểu các trường bắt buộc trước khi xử lý tiếp. |
| **Trùng lặp tài khoản Moodle (Duplicate Moodle accounts)** | Gây bất đồng bộ dữ liệu và nhầm lẫn cho người dùng. | Chiến lược phân giải định danh (identity resolution) nghiêm ngặt (Email -> MSSV -> Username) trước khi tạo user. |
| **Xung đột Username (Username collision)** | Thao tác tạo người dùng sẽ bị thất bại. | Triển khai một dịch vụ tạo username đủ "dai" (resilient) bằng cách query vào Moodle và gắn thêm các hậu tố dạng số. |
| **Ghép sai thông tin định danh (Incorrect identity matching)** | Ghi danh nhầm người. | Validate nhiều yếu tố định danh cùng lúc (ví dụ: Email + Student ID). Báo cáo các trường hợp xung đột (conflicts) để con người xem xét lại. |
| **Rò rỉ dữ liệu Production (Production data leakage)** | Lộ thông tin cá nhân (PII exposure). | Đảm bảo file `.env` đã được đưa vào ignore. Không in ra (log) các dữ liệu nhạy cảm (như mật khẩu hoặc toàn bộ email trong debug logs). |
| **Giới hạn tốc độ gọi API (API rate limits)** | Batch đang chạy giữa chừng thì bị crash. | Implement logic thử lại (retry logic) kết hợp với backoff cho cả Google và Moodle APIs. |
| **Lỗi một phần batch (Partial batch failure)** | Một dòng bị lỗi làm ngưng toàn bộ quá trình đồng bộ (sync). | Sử dụng khối `try-except` bên trong vòng lặp của batch. Thu thập lỗi và trả về một bản tóm tắt kiểu `PARTIAL_FAILURE`. |
| **Lộ thông tin đăng nhập (Credentials exposure)** | Vi phạm an ninh (Security breach). | Tuyệt đối KHÔNG commit file `.env` hoặc các file Service Account JSONs. Chỉ sử dụng thuần túy các biến môi trường. |
