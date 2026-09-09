---
name: thinkspace-dev-workflow
description: >-
  Bộ quy trình bắt buộc (Runbook) dành cho Agent khi làm việc với dự án ThinkSpace Management. 
  Sử dụng skill này mỗi khi thực hiện thay đổi code liên quan đến Backend (FastAPI, SQLAlchemy), 
  Frontend (Chart.js, HTML/JS) hoặc thiết lập Docker để tránh các lỗi cẩu thả, bộ nhớ đệm (cache), 
  và đảm bảo hệ thống vận hành trơn tru.
---

# 🚀 Quy Trình Phát Triển ThinkSpace (ThinkSpace Dev Workflow)

Skill này đúc kết toàn bộ kinh nghiệm xương máu từ quá trình xây dựng platform ThinkSpace Management. Bất kỳ khi nào bạn (Agent) được yêu cầu viết code mới, sửa lỗi, hoặc thêm tính năng, bạn **BẮT BUỘC** phải tuân thủ nghiêm ngặt 5 bước sau đây:

## Bước 1: Khảo Sát Kỹ Lưỡng (Planning & Analysis)
- **Không bao giờ đoán mò dữ liệu đầu vào:** Khi làm việc với file Excel từ bên thứ 3 (như MS Forms, Google Sheets), phải luôn kiểm tra xem các cột có thực sự chứa dữ liệu hay không (VD: Cột "Last modified time" có thể bị trống nếu user không edit lại form). Luôn có logic dự phòng (`fallback`).
- **Phân tách Frontend và Backend:** Rà soát xem thay đổi thuộc về giao diện hay logic server. Nếu liên quan đến API, phải kiểm tra kỹ file `schema.py` (Database) và `dashboard.py` (Endpoints).

## Bước 2: Viết Code An Toàn (Safe Coding)
- **CSS & Chart.js:** 
  - Nếu sử dụng biểu đồ Chart.js, **TUYỆT ĐỐI** cẩn thận với thuộc tính `maintainAspectRatio: false`. Nếu dùng nó, BẮT BUỘC phải bọc `<canvas>` trong một thẻ `div` có thuộc tính `min-height` hoặc `height` cố định (ví dụ: `style="position: relative; height: 300px; width: 100%;"`). Nếu không, biểu đồ sẽ dãn nở vô hạn và làm lag sập trình duyệt của người dùng.
- **Xử lý Thời gian (Timezones & Formats):**
  - Luôn sử dụng vòng lặp `try-except` để parse nhiều định dạng ngày tháng khác nhau (`%m/%d/%y`, `%Y-%m-%d`, v.v.).
  - Excel đôi khi lưu ngày dưới dạng số thập phân (float/serial). Bắt buộc phải import và xử lý bằng `from openpyxl.utils.datetime import from_excel` nếu thư viện đọc ra số `float`.

## Bước 3: Đánh Bại Bộ Nhớ Đệm (Cache Busting)
- **Frontend (Trình duyệt):** 
  - Trình duyệt Chrome/Edge lưu cache file `.js` và `.css` rất dai dẳng. Mỗi khi bạn sửa `app.js` hoặc `styles.css`, **BẮT BUỘC** phải vào `index.html` và tăng version ở thẻ script/link (Ví dụ: Đổi `<script src="app.js?v=2"></script>` thành `v=3`).
  - Hướng dẫn người dùng bấm `Ctrl + F5` sau mỗi đợt update.
- **Backend (Docker & Uvicorn):**
  - Uvicorn trong Dockerfile của dự án hiện tại không có cờ `--reload`. 
  - Nếu bạn sửa file `.py`, code mới sẽ KHÔNG có tác dụng trừ khi container khởi động lại. Do đó, phải yêu cầu người dùng gõ `docker-compose restart app` hoặc `docker-compose down && docker-compose up --build`.

## Bước 4: Xử Lý Dữ Liệu Cũ (Database Wiping)
- Nếu bạn thay đổi logic trích xuất hoặc lưu trữ dữ liệu (VD: sửa cách đọc cột Excel), hãy nhớ rằng Database hiện tại đang lưu dữ liệu bị lỗi do logic cũ. 
- Phải nhắc người dùng dọn dẹp Database bằng lệnh `docker-compose down -v` trước khi test lại bằng cách upload file mới.

## Bước 5: Kiểm Tra Lại Bằng Mắt (Double Check)
- Đừng bao giờ vội vàng báo cáo hoàn thành khi chưa lường trước các rủi ro.
- Tự hỏi: "Nếu biến này bị undefined thì UI có bị sập không?". 
- Luôn bọc các hàm khởi tạo giao diện phức tạp trong `try...catch` và in ra `console.error` để không làm "chết lây" các phần tử UI khác. Cung cấp fallback UI (hiển thị "Chưa có data" thay vì để màn hình trắng bóc).
