# Ngữ Cảnh Dự Án

## Vấn Đề Kinh Doanh
Quy trình hiện tại để thêm người tham gia vào Moodle đang diễn ra hoàn toàn thủ công. Nhân viên phải chuyển thông tin từ Microsoft Forms sang Google Sheets, kiểm tra dữ liệu bằng tay, chuẩn bị file tải lên, và tạo tài khoản thông qua tính năng bulk upload. Người dùng đã có tài khoản yêu cầu một quy trình thủ công riêng biệt để tìm và ghi danh (enroll), do Moodle không tự động tạo lại các tài khoản đã tồn tại. Điều này dẫn đến tình trạng trùng lặp tài khoản, bỏ sót ghi danh, và thiếu một nhật ký (audit log) tập trung.

## Quy Trình Thủ Công Hiện Tại
1. Người tham gia gửi thông tin qua Microsoft Forms.
2. Thông tin được lưu vào một template danh sách thành viên trên Google Sheet được liên kết.
3. Nhân viên kiểm tra thủ công họ tên, email, mã số sinh viên, số điện thoại, vai trò.
4. Nhân viên chuẩn bị một file upload cho Moodle.
5. Tài khoản được tạo qua bulk upload.
6. Nhân viên phải tìm và ghi danh thủ công cho những người dùng đã có tài khoản, vì tính năng bulk upload không xử lý tốt người dùng cũ.

## Quy Trình Tự Động Hóa Mong Muốn
Một nền tảng thống nhất tự động đọc dữ liệu từ Google Sheet, kiểm tra tính hợp lệ của dữ liệu, tìm kiếm tài khoản Moodle đã tồn tại (tái sử dụng tài khoản) hoặc tạo tài khoản mới, và sau đó ghi danh họ vào đúng khóa học. Quá trình này phải có tính lũy đẳng (idempotent - chạy nhiều lần không tạo ra dữ liệu rác).

## Phạm Vi MVP
MVP sẽ tập trung vào luồng tích hợp cốt lõi:
- Đầu vào: Link Google Sheet & ID Khóa Học Moodle
- Đọc danh sách thành viên từ Google Sheet
- Chuẩn hóa và kiểm tra (validate) dữ liệu
- Kiểm tra xem người dùng Moodle đã tồn tại chưa (dựa trên email, mã số sinh viên, v.v.)
- Tạo tài khoản Moodle mới nếu cần
- Kiểm tra trạng thái ghi danh khóa học
- Ghi danh người dùng nếu cần
- Trả về kết quả có cấu trúc (structured results)

## Ngoài Phạm Vi (Hiện Tại)
- Nhập dữ liệu từ file PDF, Excel, CSV
- Tích hợp trực tiếp với API của Microsoft Forms
- Nhận dạng ký tự quang học (OCR)
- Lưu trữ bằng cơ sở dữ liệu PostgreSQL (sẽ được thêm vào sau khi MVP hoạt động ổn định)
- Phân tích Nâng cao / Dashboard
- Các công cụ quản lý luồng công việc phức tạp (Airflow, Celery)

## Tầm Nhìn Nền Tảng Dài Hạn
Nền tảng Vận hành Học tập & Phân tích gồm 4 lớp:
1. **Lớp Vận Hành Học Tập (Learning Operations)**: Tiếp nhận dữ liệu, cấp phát tài khoản, ghi danh.
2. **Lớp Nền Tảng Dữ Liệu (Data Platform)**: Database vận hành, thu thập dữ liệu Moodle, ETL.
3. **Lớp Phân Tích (Analytics)**: Các bảng điều khiển (Dashboard), phân tích khóa học/nhóm.
4. **Lớp Trí Tuệ (Intelligence)**: Cảnh báo tự động, gợi ý.
