# Lộ Trình MVP

## Các Giai Đoạn

### Giai đoạn 0 — Nền tảng Repository (NOW - HIỆN TẠI)
- Kiểm tra các file hiện có, dọn dẹp các thư mục kỹ năng (skills) và cấu hình không cần thiết.
- Khởi tạo cấu trúc `docs/plan/`.
- Xác định kiến trúc và phạm vi MVP.
- Thiết lập khung FastAPI cơ bản, cấu hình Docker và `requirements.txt`.

### Giai đoạn 1 — Lấy dữ liệu Google Sheet (NEXT - TIẾP THEO)
- Triển khai tích hợp Google Sheets.
- Đọc các dòng dữ liệu và ánh xạ tiêu đề (headers) sang cấu trúc bên trong.
- Xử lý xác thực (authentication) và kết nối với Google APIs.

### Giai đoạn 2 — Chuẩn hóa & Kiểm tra dữ liệu (LATER - SAU NÀY)
- Phân tích dữ liệu thô sang các model Pydantic `Member` chuẩn.
- Kiểm tra tính hợp lệ của dữ liệu (emails, mã số sinh viên, các trường bắt buộc).
- Phát hiện trùng lặp dữ liệu trong một đợt xử lý (batch).

### Giai đoạn 3 — Kết nối Moodle API (LATER)
- Kết nối tới Moodle Web Services/REST API.
- Triển khai chức năng tìm kiếm người dùng và xác định định danh.

### Giai đoạn 4 — Cấp phát người dùng (LATER)
- Triển khai logic tạo username (xử lý trùng lặp tên).
- Tạo tài khoản Moodle mới một cách an toàn.

### Giai đoạn 5 — Ghi danh khóa học (LATER)
- Kiểm tra trạng thái ghi danh hiện tại.
- Ghi danh người dùng vào các khóa học Moodle đích.

### Giai đoạn 6 — Luồng công việc xử lý hàng loạt End-to-end (LATER)
- Kết nối tất cả các thành phần lại với nhau.
- Xử lý danh sách thành viên một cách lũy đẳng (idempotent).
- Trả về tóm tắt kết quả có cấu trúc.

### Giai đoạn 8 — Giao diện Web API & Upload MS Forms (ĐANG TRIỂN KHAI)
- Xây dựng giao diện Web (FastAPI HTML/CSS) bằng Glassmorphism.
- Hỗ trợ Upload file Excel (kết quả từ Microsoft Forms).
- Xử lý logic chia nhánh: Đăng ký Nhóm (kéo từ Google Sheet link) và Đăng ký Cá nhân (lấy data trực tiếp từ file Excel MS Forms).
- Trả về báo cáo (Report) chạy Batch.
- Setup Docker tự động chạy Web API một cách dễ dàng.

### Giai đoạn 9 — Registration Phase Dashboard (LATER)
- Xây dựng hệ thống Dashboard hiển thị thông tin đăng ký cuộc thi của thí sinh.
- Biểu đồ số lượng đăng ký theo ngày (Daily trend).
- Bảng xếp hạng số lượng thí sinh theo trường Đại học (University ranking).
- Thống kê tỷ lệ thí sinh theo chủ đề/lĩnh vực dự án lựa chọn.

### Giai đoạn 10 — Online Phase Analytics Dashboard (LATER)
- Theo dõi tương tác của người dùng trên hệ thống Moodle.
- Đo lường mức độ tương tác (Engagement): Đọc bài, làm quiz, nộp task.
- Theo dõi tiến độ hoàn thành các interactive content (vd: H5P, SCORM).
- Cung cấp insights cho ban tổ chức để đánh giá chất lượng và sự tham gia của các đội/thí sinh.

### Giai đoạn 11 — Lưu trữ dữ liệu với PostgreSQL (LATER)
- Cài đặt Database để lưu trữ vĩnh viễn các lịch sử đồng bộ, log hoạt động và phục vụ tính năng query cho các Dashboard ở Giai đoạn 9, 10.
