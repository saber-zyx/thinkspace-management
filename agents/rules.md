# 🛡️ SECURITY & CORE FILES PROTECTION RULES

## ⚠️ TÌNH TRẠNG: TUYỆT ĐỐI TUÂN THỦ (CRITICAL)

Là một AI Agent hoạt động trong dự án này, bạn **KHÔNG ĐƯỢC PHÉP** sửa đổi (modify), xóa (delete) hoặc thay thế nội dung các tệp/thư mục dưới đây trừ khi có LỆNH XÁC NHẬN RÕ RÀNG (Explicit override) từ người dùng:

### 1. Bí mật & Cấu hình môi trường (NO ACCESS)
- `.env`, `.env.*`
- **Mục đích:** Ngăn chặn rò rỉ dữ liệu nhạy cảm, API keys, và Database credentials. Tuyệt đối không in nội dung file này ra chat.

### 2. Nguyên tắc nội bộ (READ-ONLY)
- `AGENTS.md`
- Thư mục `agents/` và `skills/`
- **Mục đích:** AI chỉ được phép đọc để lấy ngữ cảnh. Không được tự ý thay đổi luật chơi của dự án hoặc thay đổi logic hành vi của chính mình.

### 3. Định hướng & Tài liệu (UPDATE WITH CAUTION)
- Thư mục `docs/` (`requirements.md`, `architecture.md`, `tasks/`, `decisions/`)
- **Mục đích:** AI **ĐƯỢC PHÉP** và có trách nhiệm cập nhật tài liệu khi dự án phát triển để giữ context cho các AI khác.
- **Quy tắc cập nhật:**
  - `docs/tasks/` và `docs/decisions/`: AI được tự do cập nhật khi có tiến độ hoặc quyết định mới.
  - `docs/requirements.md` & `docs/architecture.md`: Trái tim của dự án. AI được phép cập nhật, nhưng PHẢI hỏi ý kiến (Ask permission) trước khi ghi đè nếu thay đổi luồng nghiệp vụ hoặc tech stack lõi.

### 4. Định tuyến hạ tầng & DevOps (REQUIRES APPROVAL)
- `Dockerfile`, `compose.yaml`, `.dockerignore`
- **Mục đích:** Bảo vệ môi trường chạy, tránh việc container bị cấu hình sai dẫn đến hỏng hệ thống.

### 5. Quản lý phiên bản (NO ACCESS)
- `.git/`, `.gitignore`
- **Mục đích:** Bảo vệ toàn vẹn lịch sử mã nguồn.

---
*Nếu nhận được task yêu cầu sửa các file cấm nhưng không có chỉ thị rõ ràng, AI PHẢI dừng lại và hỏi ý kiến người dùng.*
