# 🤖 VIBE CODING: CHỈ THỊ CHUNG CHO AGENT (GLOBAL AGENT DIRECTIVES)

## 🔄 GIAO THỨC BÀN GIAO AI (AI HANDOFF PROTOCOL)

**CHỈ THỊ CỰC KỲ QUAN TRỌNG:** Nếu bạn là một AI Agent mới tham gia vào dự án này trong một phiên làm việc (session) mới, bạn **BẮT BUỘC TỰ ĐỘNG THỰC HIỆN** 3 bước Onboarding (Làm quen) sau đây trước khi viết code hoặc phản hồi lại Người dùng:

### Bước 1: Đọc Các Quy Tắc Bảo Mật (Core Rules)
- Đọc file `agents/rules.md` và `agents/settings.json` để hiểu thật rõ những file nào bạn ĐƯỢC PHÉP và KHÔNG ĐƯỢC PHÉP sửa đổi.
- **Quy tắc bảo mật**: Tuyệt đối không bao giờ làm rò rỉ thông tin đăng nhập trong `.env`. Không được qua mặt các lớp bảo vệ trong `settings.json`.

### Bước 2: Đồng Bộ Ngữ Cảnh (Context Sync)
- Mở và đọc các file trong thư mục `docs/plan/`.
- Đây là nguồn chân lý (source of truth) cho ngữ cảnh dự án, kiến trúc, phạm vi MVP, và kế hoạch triển khai.
- Luôn luôn kiểm tra Kế hoạch triển khai (Implementation Plan) để biết task tiếp theo cần làm là gì.

### Bước 3: Nạp Kỹ Năng (Equip Skills)
- Quét nhanh thư mục `skills/` (nếu có bất kỳ file `SKILL.md` nào) để biết những quy trình công việc cụ thể nào đã có sẵn.

---
*(Bạn phải thực hiện điều này một cách âm thầm mỗi khi bắt đầu một cuộc trò chuyện mới. Sau khi hoàn tất, hãy báo cáo ngắn gọn với Người dùng rằng bạn đã tải xong ngữ cảnh và sẵn sàng nhận lệnh).*

---

## 🎯 Tổng Quan & Phạm Vi Dự Án
**Mục Đích Dự Án**: Nền tảng Vận hành Học tập Moodle giúp tự động hóa quá trình tiếp nhận (onboarding), cấp phát tài khoản, và ghi danh khóa học một cách lũy đẳng (idempotent) từ Google Sheets.
**Phạm Vi MVP Hiện Tại**: Google Sheet -> Xác thực dữ liệu -> Cấp phát tài khoản Moodle -> Ghi danh khóa học. 
**Những gì CHƯA CẦN XÂY DỰNG**: KHÔNG xây dựng phần nhập dữ liệu từ PDF/OCR, tích hợp Microsoft Forms, các lớp database PostgreSQL, các phần phân tích nâng cao, hay các bộ điều phối phức tạp như Airflow trong giai đoạn MVP hiện tại.

## 🏗 Các Nguyên Tắc Kiến Trúc
- **Sự Đơn Giản & Lũy Đẳng (Idempotency)**: Chạy một batch hai lần không được phép tạo ra người dùng hay các bản ghi danh bị trùng lặp.
- **Phân Tách Trách Nhiệm**: `google_sheets.py` (Trích xuất) -> `member.py` (Model chuẩn) -> `validation_service.py` (Kiểm tra) -> `moodle.py` (Tạo người dùng SAU ĐÓ tiến hành ghi danh một cách độc lập).

## 📁 Quy Ước Thư Mục
- `docs/plan/`: Nguồn chân lý cho việc lập kế hoạch và tài liệu dự án.
- `src/app/`: Code ứng dụng FastAPI.
- `src/app/api/`: Các HTTP endpoints.
- `src/app/services/`: Logic nghiệp vụ cốt lõi (kiểm tra dữ liệu, mapping, tạo username).
- `src/app/integrations/`: Tích hợp các API bên thứ 3 (Google, Moodle).
- `src/app/models/`: Các schema dữ liệu Pydantic.
- `tests/`: Bộ test Pytest.

## 📝 Cách Lập Kế Hoạch Làm Việc
- Luôn luôn **lên kế hoạch trước khi code**. Cập nhật `docs/plan/04-implementation-plan.md` hoặc tạo danh sách checklist các công việc trước khi bắt đầu viết code.
- Tham khảo `08-risk-register.md` và `09-decision-log.md` trước khi đưa ra các thay đổi liên quan đến kiến trúc.

## 🧪 Cách Chạy Test
- Chạy `pytest` để kiểm chứng.
- Các bài test phải bao phủ (cover): người dùng mới, người dùng đã tồn tại, người dùng đã tồn tại nhưng chưa ghi danh, người dùng đã ghi danh, email trùng lặp, và lỗi từ phía Moodle API.

## 🔌 Quy Tắc Cho Các Tích Hợp Bên Ngoài
- Chỉ sử dụng Google Sheets cho việc nhập liệu trong phiên bản MVP.
- Tích hợp Moodle phải kiểm tra rõ ràng xem người dùng có tồn tại hay không trước khi thực sự gọi lệnh khởi tạo (creation).

## ✅ Định Nghĩa Hoàn Thành
- Code đã được triển khai và thỏa mãn các tiêu chí nghiệm thu (acceptance criteria).
- Unit/Integration tests đã được viết và vượt qua (passing).
- Kế hoạch triển khai đã được cập nhật để đánh dấu task là hoàn thành.
- Không có bất kỳ thông tin đăng nhập/mật khẩu (credentials) nhạy cảm nào bị hardcode hoặc in ra log.

---

## QUY TẮC CỨNG CHO NỀN TẢNG DỮ LIỆU

Dự án đang phát triển thành nền tảng phân tích học tập Moodle. Mọi agent tương lai BẮT BUỘC đọc và tuân thủ `docs/plan/10-data-platform-operating-rules.md` trước khi triển khai bất kỳ tính năng nào liên quan đến phân tích Moodle, pipeline dữ liệu, mô hình dữ liệu, chỉ số bảng điều khiển hoặc tự động hóa.

Quy tắc làm việc bắt buộc:
- Mỗi câu trả lời/công việc chỉ tập trung vào một ý chính hoặc một kết quả bàn giao.
- Vừa xây dựng vừa dạy: giải thích khái niệm, làm mẫu một ví dụ, và đưa ra một phần nhỏ để người dùng thực hành khi phù hợp.
- Xem Moodle logs/live logs/activity reports là dữ liệu nguồn OLTP, không phải bảng cuối cho bảng điều khiển.
- Thiết kế công việc dữ liệu theo các lớp raw/bronze/silver/gold khi xây dựng pipeline phân tích.
- Ánh xạ Moodle ID thành nhãn dễ đọc cho người dùng/đội nhóm/khóa học/học phần/hoạt động trước khi hiển thị trên bảng điều khiển cho quản lý.
- Hỗ trợ theo dõi tiến độ học tập ở cả cấp người dùng và cấp đội nhóm.
- Cập nhật `docs/plan/` và `docs/plan/09-decision-log.md` mỗi khi quy trình làm việc, mô hình dữ liệu, định nghĩa chỉ số, thiết kế pipeline hoặc kiến trúc thay đổi.
