# Kế Hoạch Test (Testing Plan)

## Các Cấp Độ Test
Kiểm thử (testing) sẽ được chia thành unit tests, integration tests, và end-to-end tests để đảm bảo mức độ tin cậy tối đa cho toàn bộ luồng xử lý hàng loạt (batch workflow).

## Các Yêu Cầu Bao Phủ (Coverage Requirements)
Bộ test suite PHẢI bao phủ rõ ràng các kịch bản (scenarios) sau:

### Các Kịch Bản Về Định Danh Người Dùng (User Identity)
- **Người dùng mới (New user)**: Tạo username thành công, tạo tài khoản thành công, và thực hiện ghi danh.
- **Người dùng đã tồn tại (Existing user)**: Tìm thấy tài khoản cũ, không tạo lại, và tiến hành ghi danh.
- **Tồn tại + chưa ghi danh (Existing + not enrolled)**: Nhận diện được người dùng cũ và thực hiện ghi danh.
- **Tồn tại + đã ghi danh (Existing + already enrolled)**: Nhận diện được người dùng, phát hiện đã có ghi danh, và nhẹ nhàng bỏ qua bước ghi danh (skip).

### Các Kịch Bản Về Dữ Liệu & Xác Thực (Data & Validation)
- **Email không hợp lệ (Invalid email)**: Từ chối bản ghi (record) đó ngay trong pha validation.
- **Trùng lặp Email (Duplicate email)**: Phát hiện trùng lặp ngay trong cùng một batch xử lý và loại bỏ bản sao trùng đó.
- **Trùng lặp MSSV (Duplicate MSSV)**: Xử lý an toàn các xung đột mã số sinh viên.
- **Xung đột Username (Username collision)**: Sinh ra username thay thế (ví dụ: `truongvt` -> `truongvt2`).

### Xử Lý Lỗi & Khả Năng Phục Hồi (Error Handling & Resilience)
- **Lỗi Moodle API**: Xử lý mượt mà (gracefully) các tình huống timeout hoặc lỗi 5xx từ phía Moodle.
- **Lỗi một phần batch (Partial batch failure)**: Nếu một bản ghi nào đó bị lỗi (ví dụ do dữ liệu hỏng), các bản ghi còn lại trong batch đó VẪN PHẢI tiếp tục được xử lý.

## Công Cụ Test
- **Framework**: `pytest`
- **Mocking**: `unittest.mock` / `responses` / `httpx-mock` để giả lập các APIs ngoại vi (Google Sheets, Moodle).
