# Nền tảng Phân tích & Vận hành Học tập Moodle (Moodle Learning Operations & Analytics Platform)

> **Trạng thái dự án:** Lập kế hoạch / Thiết kế MVP  
> **Phạm vi ban đầu:** Google Sheet → Validate dữ liệu → Cấp phát tài khoản Moodle → Ghi danh khóa học  
> **Phạm vi dài hạn:** Nền tảng Vận hành Học tập + Nền tảng Dữ liệu Moodle + Bảng điều khiển (Dashboard) Phân tích Học tập  
> **Ngôn ngữ chính:** Python  
> **Backend đề xuất:** FastAPI  
> **Database ban đầu:** PostgreSQL (được đưa vào sau khi tích hợp cốt lõi hoạt động)  
> **Mục tiêu sử dụng:** Tự động hóa việc tiếp nhận và ghi danh học viên vào các khóa học Moodle, đồng thời tạo nền tảng mở rộng cho việc phân tích dữ liệu học tập Moodle trong tương lai.

---

## 1. Tổng Quan Dự Án

Dự án này nhằm mục đích xây dựng một nền tảng nội bộ tự động hóa quy trình thu thập thông tin người tham gia/thành viên, tạo hoặc xác định người dùng Moodle, ghi danh họ vào đúng khóa học Moodle và sau này là trích xuất dữ liệu hoạt động học tập từ Moodle để theo dõi và phân tích vận hành.

Quy trình hiện tại đang rất thủ công:
1. Người tham gia gửi thông tin qua Microsoft Forms.
2. Thông tin được lưu trong form hoặc một template danh sách thành viên liên kết (Google Sheet).
3. Nhân viên kiểm tra thủ công họ tên, email, mã số sinh viên, số điện thoại, v.v.
4. Nhân viên chuẩn bị một file upload cho Moodle.
5. Tạo tài khoản Moodle thông qua bulk upload (tải lên hàng loạt).
6. Người dùng đã có tài khoản gây ra lỗi: Moodle không tự động tạo lại, dẫn đến việc họ không được ghi danh vào khóa học mới nếu quy trình chỉ dựa vào tính năng bulk upload.
7. Nhân viên phải tìm kiếm và ghi danh thủ công những người dùng cũ này.
8. Chưa có cơ sở dữ liệu vận hành tập trung hoặc nhật ký kiểm toán (audit trail) tự động.
9. Dữ liệu hoạt động học tập Moodle chưa được chuyển hóa một cách có hệ thống thành thông tin phân tích quản trị.

Nền tảng mục tiêu sẽ tự động hóa và chuẩn hóa toàn bộ quy trình này.

---

## 2. Vấn Đề Cốt Lõi

Các vấn đề vận hành chính bao gồm:
- Chuyển dữ liệu thủ công giữa Forms, Google Sheets, file upload và Moodle.
- Trùng lặp tài khoản Moodle hoặc lỗi tạo tài khoản khi người dùng đã tồn tại.
- Người dùng cũ không được tự động ghi danh vào khóa học mới.
- Việc tạo username thủ công dễ gây trùng lặp.
- Chưa có validation chặt chẽ trước khi đồng bộ lên Moodle.
- Không có lịch sử xử lý tập trung.
- Quy trình hiện tại không thể scale khi số lượng đội nhóm, khóa học, và người tham gia tăng lên.

Vì vậy, hệ thống phải xử lý **việc tạo người dùng** và **ghi danh khóa học** như hai thao tác hoàn toàn tách biệt.

Logic nghiệp vụ chuẩn xác:
```text
Tìm người dùng Moodle
        |
        +---- Đã tồn tại ------> Dùng lại Moodle user ID
        |
        +---- Chưa tồn tại --> Tạo người dùng mới
                                      |
                                      v
                              Lấy Moodle user ID
                                      |
                                      v
                            Kiểm tra ghi danh khóa học
                                      |
                   +------------------+------------------+
                   |                                     |
             Đã ghi danh                           Chưa ghi danh
                   |                                     |
                Bỏ qua (Skip)                       Ghi danh (Enroll)
```
Đây là một trong những yêu cầu quan trọng nhất của hệ thống.

---

## 3. Tầm Nhìn Sản Phẩm

Dự án không chỉ là một công cụ "upload CSV lên Moodle". Tầm nhìn dài hạn là:
> **Một nền tảng Vận hành & Phân tích Học tập kết nối dữ liệu đăng ký, quản lý người dùng Moodle, ghi danh khóa học, quản trị dữ liệu vận hành, và phân tích hoạt động học tập.**

Hệ thống trong tương lai có thể gồm 4 lớp:
1. Lớp Vận Hành Học Tập (Learning Operations)
2. Lớp Nền Tảng Dữ Liệu (Data Platform)
3. Lớp Phân Tích (Analytics)
4. Lớp Trí Tuệ Tương Lai (Intelligence - AI)

MVP hiện tại chỉ thực hiện flow (1) cốt lõi nhất.

---

## 4. Phạm Vi MVP

### 4.1 Mục Tiêu MVP
Phiên bản hoạt động đầu tiên phải thực hiện thành công luồng sau:
```text
URL Google Sheet + ID Khóa học Moodle
       |
       v
Đọc danh sách thành viên
       |
       v
Chuẩn hóa & Validate dữ liệu
       |
       v
Kiểm tra user Moodle
       |
       +---- user cũ ----+
       |                 |
       +---- user mới ---> Tạo tài khoản
                         |
                         v
                 Kiểm tra ghi danh
                         |
                         v
                 Ghi danh nếu cần
                         |
                         v
                 Trả về kết quả
```

### Tiêu chí thành công của MVP
Chỉ cần cung cấp 1 Google Sheet, 1 Moodle course, có cả user mới và cũ, hệ thống chạy trơn tru từ đầu tới cuối mà nhân viên không cần phải tạo/ghi danh thủ công.

---

## 5. Giả Định Đầu Vào Ban Đầu

Trong giai đoạn đầu:
> **Mặc định nguồn cấp danh sách thành viên luôn là Google Sheet.**
Việc xử lý PDF, Excel, CSV, Microsoft Form API, và OCR được dời lại các giai đoạn sau.

Input mong đợi:
```json
{
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "course_id": 123
}
```

---

## 6. Cấu Trúc Google Sheet Mong Đợi

Template danh sách thành viên hiện tại thường chứa:
- Tên, Họ và tên đệm
- Số điện thoại, Email
- Ngày sinh, Giới tính
- Trường đại học, Vai trò trong đội
- Mã số sinh viên (MSSV)
- Lớp, Ngành, Ghi chú

Đối với MVP, chỉ yêu cầu bắt buộc các trường cần thiết để xác định danh tính và cấp phát Moodle:
- `first_name` (Bắt buộc)
- `last_name` (Bắt buộc)
- `email` (Bắt buộc)
- `student_id` (Khuyến khích)

---

## 7. Model Member Chuẩn (Canonical Model)

Mọi nguồn dữ liệu tương lai (Excel, PDF, Forms...) cuối cùng đều phải được chuyển đổi thành model nội bộ này.

```python
from pydantic import BaseModel, EmailStr

class Member(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    student_id: str | None = None
    ...
```
Logic nghiệp vụ không được phụ thuộc vào định dạng file gốc ban đầu.

---

## 8. Chiến Lược Định Danh Người Dùng Moodle

Hệ thống không được chỉ dựa vào Moodle username để nhận diện người dùng. Thứ tự ưu tiên:
1. Moodle user ID (ID nội bộ Moodle)
2. Student ID / MSSV (Mã số sinh viên)
3. Email
4. Moodle username

---

## 9. Tạo Username

Quy tắc hiện tại: `Võ Thiên Trường → truongvt`.
Cần có một service riêng biệt (không hard-code rải rác) để:
1. Bỏ dấu tiếng Việt, chuyển thành chữ thường.
2. Xóa khoảng trắng và ký tự đặc biệt.
3. Ghép Tên + ký tự đầu của Họ và Tên Đệm.
4. Xử lý trùng lặp (vd: truongvt, truongvt2).

---

## 10. Logic Nghiệp Vụ Moodle

**Việc tạo user và ghi danh user PHẢI là hai thao tác độc lập.**
Điều này giải quyết bài toán user cũ bị bỏ qua (skip) hoàn toàn trong tính năng bulk upload.

---

## 11. Yêu Cầu Tích Hợp Moodle

Trước khi triển khai tích hợp, cần có từ Quản trị viên Moodle:
- Base URL, Web Services được bật, API token với đủ quyền hạn.
Nếu không có quyền gọi trực tiếp API, giải pháp tạm thời là: Hệ thống sinh ra một file CSV chuẩn của Moodle để quản trị viên tải lên thủ công. (Tuy nhiên, gọi API trực tiếp vẫn là mục tiêu ưu tiên số 1).

---

## 12. Xử Lý Mật Khẩu

Hệ thống **không được phép tự tạo và lưu trữ plaintext passwords dài hạn**. Tùy thuộc vào cấu hình của Moodle (tự tạo password, dùng SSO, hay password tạm thời bắt buộc đổi), hệ thống sẽ xử lý theo. Mật khẩu không bao giờ được commit lên Git.

---

## 13. Yêu Cầu Kiểm Tra Dữ Liệu (Validation)

Mỗi record phải qua vòng kiểm tra trước khi đồng bộ:
- Tên bắt buộc có?
- Email đúng định dạng?
- Có trùng lặp email/MSSV ngay trong batch này không?
- Username sinh ra được không?
Bản ghi nào lỗi sẽ bị từ chối, nhưng không làm dừng cả batch (Partial Failure).

---

## 14. Đề Xuất Quy Trình Staging & Phê Duyệt

Dù ban đầu chạy tự động qua command line/API, ở môi trường Production sau này nên có luồng:
`Nhập liệu → Phân tích → Kiểm tra → STAGING → Xem xét → Phê duyệt → Đồng bộ lên Moodle`.
Điều này ngăn chặn dữ liệu sai bị đẩy thẳng lên hệ thống thật.

---

## 15. Công Nghệ Đề Xuất

**MVP:** Python 3.11+, FastAPI, Pydantic, httpx, Google Sheets API, Moodle Web Services, pytest, ruff, Docker.
**Sau MVP:** PostgreSQL, SQLAlchemy, Alembic.
**Giai đoạn Phân tích (Analytics):** SQL, dbt, PostgreSQL/BigQuery, Power BI/Metabase.
**Tuyệt đối không dùng Airflow/Kafka trong MVP.**

---

## 16. Cấu Trúc Repository Khuyến Nghị
Được chia thành các layer rõ ràng: `api/`, `core/`, `models/`, `integrations/`, `services/`, `utils/`. Giúp dễ dàng phát triển và scale về sau.

---

## 17. Trách Nhiệm Các Module Chính
- `integrations/google_sheets.py`: Chỉ dùng để đọc raw data từ Sheet, không chứa logic Moodle.
- `models/member.py`: Định nghĩa schema chuẩn của thành viên.
- `services/member_service.py`: Ánh xạ dữ liệu thô vào schema chuẩn.
- `services/validation_service.py`: Kiểm tra tính hợp lệ.
- `integrations/moodle.py`: Tương tác thuần túy với Moodle API.
- `services/enrollment_service.py`: Điều phối toàn bộ flow xử lý (Kiểm tra -> Tạo -> Ghi danh).

---

*(Bản README này đã được cấu trúc và dịch sang tiếng Việt để phù hợp với quá trình Onboarding cho cả kỹ sư phần mềm lẫn AI Coding Agents. Tham khảo chi tiết trong thư mục `docs/plan/`)*
