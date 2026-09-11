# Kế Hoạch Triển Khai

## Chi Tiết Công Việc (Task Breakdown)

### TASK-001: Khởi tạo Project & Ứng dụng FastAPI
- **Mục tiêu**: Khởi tạo ứng dụng FastAPI cơ bản.
- **File ảnh hưởng**: `src/app/main.py`, `src/app/__init__.py`, `requirements.txt`
- **Phụ thuộc**: Không có.
- **Testing**: Xác minh ứng dụng có thể khởi động thành công.
- **Trạng thái**: TODO (Chưa bắt đầu)

### TASK-002: Thêm Endpoint Health (Kiểm tra sức khỏe hệ thống)
- **Mục tiêu**: Endpoint cơ bản để đảm bảo API đang chạy tốt.
- **File ảnh hưởng**: `src/app/api/health.py`
- **Phụ thuộc**: TASK-001
- **Testing**: `test_health.py`
- **Trạng thái**: TODO

### TASK-003: Cấu Hình Môi Trường
- **Mục tiêu**: Cài đặt `pydantic-settings` để load cấu hình từ `.env`.
- **File ảnh hưởng**: `src/app/core/config.py`, `.env.example`
- **Phụ thuộc**: TASK-001
- **Testing**: Test khả năng load config.
- **Trạng thái**: TODO

### TASK-004: Định Nghĩa Model Member
- **Mục tiêu**: Triển khai model Pydantic chuẩn (`Member`).
- **File ảnh hưởng**: `src/app/models/member.py`
- **Phụ thuộc**: Không có
- **Testing**: Viết Unit tests cho việc validate schema.
- **Trạng thái**: TODO

### TASK-005: Triển Khai Trình Phân Tích ID Google Sheet & Xác Thực
- **Mục tiêu**: Parse URL và thực hiện xác thực với Google Sheets API.
- **File ảnh hưởng**: `src/app/integrations/google_sheets.py`
- **Phụ thuộc**: TASK-003
- **Testing**: Viết Integration tests (có sử dụng mock).
- **Trạng thái**: TODO

### TASK-006: Triển Khai Trình Đọc Google Sheets & Mapping
- **Mục tiêu**: Đọc các hàng và ánh xạ các tiêu đề thô (raw headers) sang model `Member`.
- **File ảnh hưởng**: `src/app/services/member_service.py`
- **Phụ thuộc**: TASK-004, TASK-005
- **Testing**: Viết Unit tests với data mock của Sheet.
- **Trạng thái**: TODO

### TASK-007: Xác Thực Dữ Liệu (Validate Records)
- **Mục tiêu**: Kiểm tra tính hợp lệ của email, phát hiện trùng lặp.
- **File ảnh hưởng**: `src/app/services/validation_service.py`
- **Phụ thuộc**: TASK-004
- **Testing**: Test các email không hợp lệ, dữ liệu bị trùng lặp.
- **Trạng thái**: TODO

### TASK-008: Tạo Username Moodle
- **Mục tiêu**: Sinh username tự động (ví dụ: `truongvt`) và tránh trùng lặp.
- **File ảnh hưởng**: `src/app/services/username_service.py`
- **Phụ thuộc**: Không có
- **Testing**: Viết Unit tests với các tên có dấu tiếng Việt.
- **Trạng thái**: TODO

### TASK-009: Kết Nối Moodle API (Tìm kiếm/Tạo User)
- **Mục tiêu**: Tìm user bằng email/MSSV, hoặc tạo user mới.
- **File ảnh hưởng**: `src/app/integrations/moodle.py`
- **Phụ thuộc**: TASK-003, TASK-008
- **Testing**: Mock các response trả về từ Moodle.
- **Trạng thái**: TODO

### TASK-010: Ghi Danh Khóa Học (Course Enrollment)
- **Mục tiêu**: Kiểm tra trạng thái ghi danh và tiến hành ghi danh nếu cần thiết.
- **File ảnh hưởng**: `src/app/integrations/moodle.py`, `src/app/services/enrollment_service.py`
- **Phụ thuộc**: TASK-009
- **Testing**: Mock kịch bản đã ghi danh vs chưa ghi danh.
- **Trạng thái**: TODO

### TASK-011: Xây Dựng Luồng Workflow Batch
- **Mục tiêu**: Xây dựng endpoint chính kết nối toàn bộ luồng xử lý trên.
- **File ảnh hưởng**: `src/app/api/enrollment_batches.py`
- **Phụ thuộc**: Tất cả các tasks trên
- **Testing**: End-to-end integration test (có mock).
- **Trạng thái**: TODO

### TASK-012: Triển Khai Bronze Pipeline Cho Moodle Logs
- **Mục tiêu**: Tạo pipeline tối thiểu để nạp file CSV log Moodle vào database, lưu metadata file ở `raw_moodle_log_files` và từng dòng event ở `bronze_moodle_log_events`.
- **File ảnh hưởng**: `src/app/models/schema.py`, `src/app/services/moodle_log_service.py`, `src/app/api/moodle_logs.py`, `src/app/main.py`, `src/app/core/database.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`
- **Phụ thuộc**: ADR-007, ADR-008, file mẫu `example/logs_SANDBOX2026_20260907-2141.csv`.
- **Testing**: `python -m pytest`, `python -m compileall src/app`, import thử file CSV mẫu qua `/api/v1/moodle-logs/import-csv`.
- **Trạng thái**: DONE

### TASK-013: Thiết Kế Silver Pipeline Cho Moodle Learning Events
- **Mục tiêu**: Cùng người dùng đọc dữ liệu trong `bronze_moodle_log_events`, xác định grain, cột phân tích, quy tắc lọc learning event, và chiến lược ánh xạ Moodle user sang dữ liệu đăng ký trước khi viết code silver.
- **File ảnh hưởng dự kiến**: `docs/plan/11-moodle-analytics-data-model.md`, `src/app/models/schema.py`, `src/app/services/moodle_log_service.py`, `tests/test_main.py`.
- **Phụ thuộc**: TASK-012, bảng `registrations`, bảng `bronze_moodle_log_events`, dữ liệu log mẫu trong `example/logs_SANDBOX2026_20260907-2141.csv`.
- **Bài thực hành cho người dùng**: Chạy SQL trong DBeaver để kiểm tra event learning, event admin/report, và tỷ lệ ánh xạ user từ Moodle log về bảng đăng ký.
- **Trạng thái**: IN_PROGRESS

### TASK-014: Thiết Kế Và Nạp Moodle Participants V0
- **Mục tiêu**: Tạo nguồn ánh xạ danh tính từ file Moodle participants export để nối Moodle logs với email, groups và bảng `registrations`.
- **File ảnh hưởng**: `src/app/models/schema.py`, `src/app/services/moodle_participant_service.py`, `src/app/api/moodle_participants.py`, `src/app/main.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Phụ thuộc**: File mẫu `example/courseid_12_participants.csv`, TASK-013.
- **Testing**: `python -m pytest`, `python -m compileall src/app`, import thử file CSV mẫu qua `/api/v1/moodle-participants/import-csv`.
- **Kết quả kiểm chứng**: Import lần đầu đọc 119 dòng, import lại cùng file tạo 0 dòng mới và 119 duplicate. Sau cleanup email sai đã xác nhận, bảng `raw_moodle_participants` còn 113 dòng.
- **Trạng thái**: DONE

### TASK-015: Tạo Identity Map Chính Thức Cho Moodle Users
- **Mục tiêu**: Tạo view `int_moodle_user_identity_map` để nối participants Moodle với `registrations` bằng email, cung cấp identity đã chuẩn hóa cho bước silver.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/api/moodle_participants.py`, `src/app/main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Phụ thuộc**: TASK-014, kết quả kiểm chứng DBeaver của người dùng.
- **Testing**: `python -m pytest`, `python -m compileall src/app`, restart app, gọi `/api/v1/moodle-participants/identity-map-summary`.
- **Kết quả kiểm chứng**: `total_identities = 113`, `matched_registrations = 101`, `unmatched_registrations = 12`, `learning_users = 44`, `matched_learning_users = 44`.
- **Trạng thái**: DONE
## TASK-016: Chuẩn hóa cách đếm số lượng đội trên dashboard đăng ký
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tránh dashboard đếm trùng một đội chỉ vì tên đội khác chữ hoa/thường hoặc khác khoảng trắng.
- **File ảnh hưởng**: `src/app/utils/text_utils.py`, `src/app/services/msforms_service.py`, `src/app/services/moodle_participant_service.py`, `src/app/api/dashboard.py`, `tests/test_main.py`.
- **Kết quả kiểm chứng**: Dashboard `GET /api/v1/dashboard/stats` trả `total_teams = 22` sau khi chuẩn hóa biến thể `STABILY`/`Stabily`.
- **Ghi chú học tập**: Metric cấp đội cần có `team_name_key = lower(trim(team_name))` hoặc một dimension team canonical, không nên dựa hoàn toàn vào chuỗi nhập thô.
## TASK-017: Tạo view Silver chính thức cho Moodle learning events
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo lớp dữ liệu sạch `silver_moodle_learning_events` từ `bronze_moodle_log_events` và `int_moodle_user_identity_map`.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Kết quả kiểm chứng**: `learning_event_rows = 1461`, `learning_users = 45`, `matched_learning_emails = 45`, `learning_teams = 14`, `unmapped_event_rows = 0`.
- **Ghi chú học tập**: Silver có grain `một dòng = một learning event đã map danh tính`. Kiểm tra grain cho thấy `silver_rows = 1461`, `distinct_bronze_events = 1461`, `duplicated_bronze_events = 0`.
## TASK-018: Cập nhật pipeline log cho export chồng lấn và tín hiệu submit
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Import file log mới `logs_SANDBOX2026_20260909-1639.csv` mà không nhân đôi các dòng đã có, đồng thời nhận diện event submit để phục vụ chỉ số hoàn thành.
- **File ảnh hưởng**: `src/app/models/schema.py`, `src/app/services/moodle_log_service.py`, `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`.
- **Kết quả kiểm chứng**: File mới có `4191` dòng, import thêm `494` dòng mới, bỏ qua `3521` dòng trùng, loại trừ `176` dòng thuộc user exclusion, lỗi parse `0`.
- **Ghi chú học tập**: Export log định kỳ thường bị chồng lấn thời gian, nên khóa chống trùng phải dựa trên event logic thay vì tên file.

## TASK-019: Tạo dimension activity Moodle từ log
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo view `dim_moodle_course_activities` để map `moodle_course_module_id` với `activity_type`, `activity_name` và các nhãn phân tích cơ bản.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Kết quả kiểm chứng**: `total_activities = 59`, `submission_activities = 17`, `learning_materials = 29`, `submission_final_event_rows = 8`, `global_unique_submitters = 1`.
- **Ghi chú học tập**: Dimension là bảng tra cứu mô tả đối tượng phân tích. Fact/Silver ghi lại hành vi; Dim mô tả activity/module đó là gì.
## TASK-020: Tạo Gold user learning summary
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo view `gold_user_learning_summary` để tổng hợp tiến độ học tập ở cấp từng người học.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Kết quả kiểm chứng**: `total_users = 113`, `accessed_users = 53`, `not_started_users = 60`, `submitted_users = 1`, `active_teams = 16`, `total_teams_in_gold = 22`.
- **Ghi chú học tập**: Gold dùng `int_moodle_user_identity_map` làm base để vẫn giữ được user chưa có log học. Nếu dùng Silver làm base thì sẽ mất nhóm `not_started`.
## TASK-021: Tạo Gold registered user learning summary
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo view `gold_registered_user_learning_summary` để dashboard chương trình chỉ tính những người có trong bảng `registrations`, thay vì tính toàn bộ Moodle participants.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Kết quả kiểm chứng**: View mới trả `total_registered_users = 101`, `mapped_to_moodle_users = 101`, `accessed_users = 47`, `not_started_users = 54`, `submitted_users = 1`, `total_registered_teams = 22`, `active_registered_teams = 16`.
- **Ghi chú học tập**: Đây là ví dụ về việc chọn đúng grain/base table trước khi dựng metric. Với dashboard chương trình, base đúng là `registrations`; với audit Moodle rộng hơn, base có thể là `raw_moodle_participants` hoặc `int_moodle_user_identity_map`.
## TASK-022: Tạo Gold team learning summary
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo view `gold_team_learning_summary` để tổng hợp tiến độ học tập ở cấp đội, phục vụ dashboard filter theo team.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`, `docs/optimization/02-individual-to-team-group-sync.md`.
- **Câu hỏi business dashboard bắt đầu trả lời**: Đội nào đã có thành viên học, đội nào chưa bắt đầu, đội nào đã có người nộp submission, đội nào cần được nhắc nhở.
- **Ghi chú học tập**: Đây là bước aggregate từ grain người dùng lên grain đội. Khi aggregate cần phân biệt `viewed_activity_count` của cả đội với tổng activity đã xem theo từng thành viên.
## TASK-023: Tạo Gold individual learning summary
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo view `gold_individual_learning_summary` để tổng hợp tiến độ học tập của nhóm thí sinh đăng ký cá nhân, phục vụ dashboard filter dành cho cá nhân.
- **File ảnh hưởng**: `src/app/core/database.py`, `src/app/main.py`, `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Câu hỏi business dashboard bắt đầu trả lời**: Có bao nhiêu thí sinh cá nhân đã học, bao nhiêu người chưa bắt đầu, ai đã nộp submission, và có cá nhân nào đã được đưa vào Moodle group hay chưa.
- **Ghi chú học tập**: View này là lát cắt semantic từ `gold_registered_user_learning_summary`, không tạo lại logic mapping. Đây là cách tránh trùng logic khi thiết kế tầng Gold.
## TASK-024: Tạo overview API cho Learning Dashboard
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Tạo endpoint `GET /api/v1/moodle-logs/learning-dashboard-overview` để gom các chỉ số tổng quan từ Gold registered user, Gold team, Gold individual, dim activity và Silver events.
- **File ảnh hưởng**: `src/app/api/moodle_logs.py`, `tests/test_main.py`, `docs/plan/12-learning-dashboard-business-questions.md`, `docs/plan/11-moodle-analytics-data-model.md`.
- **Kết quả kiểm chứng**: Endpoint trả `total_registered_users = 101`, `accessed_users = 47`, `not_started_users = 54`, `submitted_users = 1`, `total_teams = 22`, `active_teams = 16`, `not_started_teams = 6`, `submitted_teams = 1`, `total_individuals = 18`, `accessed_individuals = 11`.
- **Ghi chú học tập**: Đây là semantic API cho dashboard. Frontend không nên tự viết lại logic business; frontend chỉ trình bày dữ liệu đã được định nghĩa rõ ở backend/data layer.
## TASK-025: Dựng Learning Dashboard UI v0
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Thêm màn `Learning Dashboard` vào sidebar và dựng UI v0 cho ba filter `Overview`, `Team`, `Individual`.
- **File ảnh hưởng**: `src/app/static/index.html`, `src/app/static/styles.css`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`.
- **Nguồn dữ liệu**: `GET /api/v1/moodle-logs/learning-dashboard-overview`, `GET /api/v1/moodle-logs/gold-team-summary`, `GET /api/v1/moodle-logs/gold-individual-summary`.
- **Kết quả kiểm chứng**: `python -m pytest` trả `25 passed`; `node --check src/app/static/learning-dashboard.js` không báo lỗi; `/` và `/learning-dashboard.js?v=1` trả HTTP `200`.
- **Ghi chú học tập**: Đây là bước tách frontend theo domain. Dashboard đăng ký vẫn dùng `app.js`; dashboard học tập dùng `learning-dashboard.js` để tránh trộn logic.

## TASK-026: Thêm drill-down hoạt động theo từng đội
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Khi người quản lý bấm vào một đội trong bảng học tập, hệ thống mở modal hiển thị từng thành viên của đội và các hoạt động Moodle mà từng người đã thực hiện.
- **File ảnh hưởng**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/styles.css`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`, `docs/plan/11-moodle-analytics-data-model.md`, `docs/plan/12-learning-dashboard-business-questions.md`.
- **Nguồn dữ liệu**: `gold_team_learning_summary`, `gold_registered_user_learning_summary`, `silver_moodle_learning_events`.
- **API mới**: `GET /api/v1/moodle-logs/team-activities-detail?team_name_key=...`.
- **Câu hỏi business dashboard bắt đầu trả lời**: Trong một đội cụ thể, thành viên nào đã học, thành viên nào chưa bắt đầu, mỗi người đã xem hoặc nộp những hoạt động nào, và những hoạt động không hiển thị nghĩa là chưa có log cho hoạt động đó trong dữ liệu hiện tại.
- **Kết quả kiểm chứng**: `python -m pytest` trả `25 passed`; `node --check src/app/static/learning-dashboard.js` không báo lỗi; `/` và `/learning-dashboard.js?v=7` trả HTTP `200`; gọi chi tiết đội `ai quét drone` trả `2` thành viên và thành viên đầu có `16` hoạt động.
- **Ghi chú học tập**: Đây là ví dụ về luồng drill-down từ Gold aggregate xuống Silver fact. Gold giúp chọn đúng đội và thành viên; Silver cung cấp từng event/activity thực tế.

## TASK-027: Cải thiện UI activity detail và thêm drill-down cá nhân
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Làm gọn phần metric activity trong modal bằng chip nhỏ, đổi nhãn trạng thái nộp bài về `Đã nộp bài`, và cho phép bấm chi tiết từng cá nhân để xem activity log giống tab đội.
- **File ảnh hưởng**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/styles.css`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`, `docs/plan/12-learning-dashboard-business-questions.md`, `docs/plan/13-learning-dashboard-insight-backlog.md`.
- **Nguồn dữ liệu**: `gold_individual_learning_summary`, `silver_moodle_learning_events`.
- **API cập nhật**: `GET /api/v1/moodle-logs/individual-activities-detail?email=...` trả thêm số lượt view, số sự kiện, số thao tác nộp bài và số lần nộp bài cuối.
- **Kết quả kiểm chứng**: `python -m pytest` trả `25 passed`; `node --check src/app/static/learning-dashboard.js` không báo lỗi; `/learning-dashboard.js?v=7` trả HTTP `200`; gọi chi tiết cá nhân trả `20` hoạt động cho `anhtruong.31241023562@st.ueh.edu.vn`; gọi chi tiết đội `AI quét drone` vẫn trả count submission cụ thể cho từng activity.
- **Ghi chú học tập**: Không nên dùng badge chung chung trên activity detail. Nên hiển thị chỉ số đo được từ log, ví dụ `19 lượt view`, `34 sự kiện`, `15 thao tác nộp bài`, `3 đã nộp bài`.

## TASK-028: Chuẩn bị kế hoạch deploy demo Render + Neon
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Có checklist deploy demo công khai để manager xem trước dashboard mà chưa cần triển khai production.
- **File ảnh hưởng**: `docs/plan/14-demo-deploy-render-neon.md`, `docs/plan/09-decision-log.md`.
- **Quyết định kỹ thuật**: Bản demo ưu tiên Render Python Web Service + Neon PostgreSQL, chạy bằng `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`.
- **Ghi chú học tập**: Khi deploy backend, điểm quan trọng không chỉ là code chạy local, mà còn là app phải bind đúng host/port do nền tảng cấp và đọc cấu hình qua environment variables.

## TASK-029: Thiết kế kiến trúc lấy Moodle logs liên tục
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Chốt hướng ingestion log dài hạn trước khi code collector, tránh phụ thuộc việc download thủ công hoặc scrape UI Live logs.
- **File ảnh hưởng**: `docs/plan/15-moodle-log-ingestion-architecture.md`, `docs/plan/09-decision-log.md`.
- **Quyết định kỹ thuật**: Không scrape HTML Live logs làm nguồn chính. Ưu tiên Moodle External Database Log Store hoặc quyền đọc database log Moodle, sau đó dùng watermark để lấy incremental.
- **Ghi chú học tập**: Đây là bước chuyển từ batch thủ công sang pipeline dữ liệu. Khái niệm cần nắm là watermark: lưu mốc log cuối đã xử lý để lần sau chỉ lấy phần mới.

## TASK-030: Tạo script seed dữ liệu demo sang Neon
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Cho phép đưa dữ liệu dashboard đang đúng ở PostgreSQL local sang Neon mà không upload lại qua UI và không gọi Moodle API.
- **File ảnh hưởng**: `scripts/seed-neon-demo.ps1`, `docs/plan/14-demo-deploy-render-neon.md`, `docs/plan/09-decision-log.md`.
- **Lỗi đã xử lý**: File dump đầu tiên chứa bảng backup tạm nên restore lỗi relation không tồn tại. File dump tiếp theo dùng `INSERT` không có tên cột nên restore lỗi lệch kiểu dữ liệu giữa local và Neon. Script mới dump schema bảng chính và data bằng `--column-inserts`.
- **Ghi chú học tập**: Khi migrate dữ liệu giữa hai database cùng engine nhưng schema có thể lệch, nên ưu tiên restore schema khớp trước rồi dùng insert có tên cột hoặc dump custom format.

## TASK-031: Khởi tạo dbt project cho transform Moodle analytics
- **Trạng thái**: Hoàn thành
- **Mục tiêu**: Bắt đầu đưa tool Data Engineer vào pipeline bằng dbt, trước mắt chuyển logic identity mapping sang model SQL có source, staging, intermediate và test.
- **File ảnh hưởng**: `requirements-data.txt`, `.gitignore`, `analytics/dbt_thinkspace/`, `docs/plan/16-dbt-transformation-workflow.md`, `docs/plan/09-decision-log.md`.
- **Model đầu tiên**: `int_moodle_user_identity_map`, grain `một dòng = một Moodle participant đã được map sang registration nếu email khớp`.
- **Kết quả kiểm chứng**: `dbt debug`, `dbt run`, `dbt test` đều chạy thành công trên PostgreSQL local; dbt tạo `3` view trong schema `analytics` và `18` data tests pass. `analytics.int_moodle_user_identity_map` có `113` dòng.
- **Ghi chú học tập**: dbt không thay thế database. dbt quản lý SQL transform trong database, giúp mô hình dữ liệu có version, test và lineage rõ ràng hơn. Dependency dbt được tách sang `requirements-data.txt` để web app deploy không phải cài tool pipeline.

## TASK-032: Nap file Moodle log moi nhat vao dashboard local
- **Trang thai**: Hoan thanh phan local, cho seed Neon de cap nhat web service.
- **Muc tieu**: Dua file log moi nhat trong `example/` vao PostgreSQL local de dashboard localhost phan anh du lieu hoc tap moi truoc khi quay lai thiet ke live logs.
- **File log da nap**: `example/logs_SANDBOX2026_20260910-0640.csv`.
- **Ket qua import**: File co `4342` dong; he thong them `151` event moi, bo qua `4015` event trung, loai `176` event nam trong danh sach exclude, va khong co dong loi parse.
- **So lieu local sau import**: `bronze_moodle_log_events = 4176`, `bronze learning events = 2068`, `silver_moodle_learning_events = 2068`, `learning users = 55`, `learning emails = 55`, `learning teams = 17`, `latest_event_time = 2026-09-10 06:40:15+00`.
- **So lieu dashboard registered local**: `total_registered_users = 101`, `accessed_users = 49`, `not_started_users = 52`, `submitted_users = 1`, `total_teams = 22`, `active_teams = 17`, `not_started_teams = 5`, `total_individuals = 18`, `accessed_individuals = 12`.
- **Ghi chu van hanh**: Render hien van doc du lieu Neon cu cho den khi chay lai `scripts/seed-neon-demo.ps1 -ResetTarget` voi `TARGET_DATABASE_URL`. Connection string Neon khong duoc ghi vao chat, docs hoac Git.

## TASK-033: Them overview insight cho guideline, survey va interaction theo ngay
- **Trang thai**: Hoan thanh local.
- **Muc tieu**: Bo sung cac insight quan trong cho manager trong Learning Dashboard Overview: nhịp tương tác theo ngày, spotlight cho `UEH LMS REGISTRATION GUIDELINE`, `Pre-Program Survey`, và `Foundations of Digital Entrepreneurship Course`.
- **File anh huong**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/learning-dashboard.js`, `src/app/static/styles.css`, `tests/test_main.py`.
- **Metric moi**: `daily_interactions` gom tong interaction, luot xem, thao tac nop bai, lan da nop bai, so nguoi hoc va so doi hoat dong theo tung ngay.
- **Spotlight moi**: `key_activity_spotlights` theo doi module `714` guideline LMS, module `707` trang survey, va module `712` Foundations subsection.
- **Pheu survey moi**: `pre_program_gate_summary` theo doi so nguoi da xem survey page va co di tiep sang noi dung khac hay khong. Cac chi so guideline FMC3 duoc tach rieng tu TASK-035.
- **Ghi chu hoc tap**: Day la vi du ve dashboard metric theo business question. Truoc khi ve bieu do, can chot cau hoi manager muon tra loi va gan moi chi so voi grain ro rang: ngay, user da dang ky, team, hay Moodle activity.

## TASK-034: Chuan hoa spotlight Pre-Program Survey va Foundations
- **Trang thai**: Hoan thanh local.
- **Muc tieu**: Lam ro su khac nhau giua log he thong/admin va tuong tac hoc tap that cua thi sinh trong cac activity trong yeu.
- **File anh huong**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`, `docs/plan/09-decision-log.md`.
- **Quyet dinh UI**: `Pre-Program Survey` chi hien mot page dang hien thi cho nguoi hoc la module `707`; activity an module `709` khong dua vao spotlight/phieu quan ly.
- **Quyet dinh metric**: `Foundations of Digital Entrepreneurship Course` module `712` hien note neu chi co log he thong/admin, nhung khong cong vao so nguoi hoc hoac luot xem cua thi sinh.
- **Ghi chu hoc tap**: Trong log Moodle, cung mot `course module id` co the co log admin/system va log learner. Dashboard phai chot grain va actor ro rang truoc khi tinh KPI.

## TASK-035: Tach Pre-Program Survey va FMC3 thanh hai funnel rieng
- **Trang thai**: Hoan thanh local.
- **Muc tieu**: Khong tron tin hieu survey dau vao voi tin hieu doc guideline/tai lieu cua khoa `Foundations of Digital Entrepreneurship Course`.
- **File anh huong**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`, `docs/plan/09-decision-log.md`.
- **Thay doi metric**: `pre_program_gate_summary` chi theo doi viec xem trang Pre-Program Survey va viec co di tiep sang noi dung khac hay khong.
- **Metric moi**: `foundation_course_summary` theo doi `UEH LMS Registration Guideline (FMC3)` module `714`, activity `Certificate Submission` module `716`, so doi hoat dong, va nhom bo guideline FMC3 nhung van vao submission.
- **Ghi chu hoc tap**: Khi mot dashboard co nhieu business process gan nhau, can tach funnel theo dung ngu canh nghiep vu. Cung la chu "guideline" nhung guideline LMS cua FMC3 khong duoc tron vao Pre-Program Survey.

## TASK-036: Siết scope FMC3 về module 714 và 716
- **Trang thai**: Hoan thanh local.
- **Muc tieu**: Giam so lieu phinh to do gom qua rong cac log H5P/milestone khong phai muc tieu FMC3 manager dang can theo doi.
- **File anh huong**: `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/learning-dashboard.js`, `tests/test_main.py`, `docs/plan/09-decision-log.md`.
- **Quyet dinh metric**: Card `Foundations of Digital Entrepreneurship Course` va `foundation_course_summary` chi tinh scope `714` guideline va `716` Certificate Submission. Cac H5P milestone khong con duoc cong vao card nay.
- **Ket qua local sau khi siết scope**: Scope `714/716` co `39` access events, `30` Course module viewed, `3` submission actions va `5` email co log.
- **Ghi chu hoc tap**: Khi mot chi so bi lon bat thuong, can drill down theo `module_id`, `event_name`, `progress_signal_type` truoc khi sua UI. Loi o day la dinh nghia scope, khong phai loi Chart.js.

## TASK-037: Them o theo doi dang ky khoa entrepreneurship tren UEH LMS
- **Trang thai**: Hoan thanh local.
- **Muc tieu**: Bo sung o thu 4 trong khu vuc hoat dong trong yeu de theo doi user da dang ky khoa entrepreneurship tren he thong UEH LMS ben thu ba.
- **File anh huong**: `src/app/models/schema.py`, `src/app/api/moodle_logs.py`, `src/app/static/index.html`, `src/app/static/learning-dashboard.js`, `src/app/static/styles.css`, `scripts/seed-neon-demo.ps1`, `tests/test_main.py`, `docs/plan/09-decision-log.md`.
- **Bang raw moi**: `raw_ueh_lms_course_enrollments` luu email enrollment tu UEH LMS voi `external_course_key = 'fmc3_entrepreneurship'`.
- **Metric moi**: `ueh_lms_entrepreneurship_enrollment_summary` tinh `enrolled_registered_users`, `total_registered_users`, `source_enrolled_emails`, va `enrollment_rate` bang cach join email UEH LMS voi `registrations`.
- **Chi tiet moi**: Endpoint `/api/v1/moodle-logs/ueh-lms-entrepreneurship-enrollments-detail` tra danh sach user da match email de hien trong modal.
- **Ghi chu hoc tap**: Day la mau raw landing table cho nguon third-party. Pipeline thuc te sau nay se upsert tu database UEH LMS vao raw, sau do dashboard chi doc summary da join theo email.

## TASK-038: Import log tieng Viet cua khoa entrepreneurship
- **Trang thai**: Hoan thanh local, cho seed Neon de cap nhat live.
- **Muc tieu**: Doc file log `example/logs_Digital Entrepreneurship_20260910-1053.csv` co header/event name tieng Viet, chuyen ve schema Moodle log chuan va tu dong tao enrollment UEH LMS tu event ghi danh khoa hoc.
- **File anh huong**: `src/app/services/moodle_log_service.py`, `src/app/core/database.py`, `tests/test_main.py`, `docs/plan/09-decision-log.md`.
- **Mapping moi**: Header tieng Viet duoc map sang header chuan; event `Người dùng đã ghi danh khóa học` duoc map thanh `User enrolled in course`; event `Mô-đun khóa học đã xem`, SCORM va Quiz duoc map thanh cac learning event canonical.
- **Ket qua local**: Import `18,133` dong, them `18,133` bronze events, khong loi parse, course id `42246`. Bang `raw_ueh_lms_course_enrollments` co `19` email, trong do `13` email match voi `107` registrations, ty le `12.1%`.
- **Doi chieu live hien tai**: Render/Neon van co `4,176` bronze events va `0` enrollment UEH LMS cho den khi seed lai Neon tu local.
- **Ghi chu hoc tap**: Day la vi du ve raw ingestion co schema drift/ngon ngu khac nhau. Bronze nen giu gia tri canonical de silver/gold khong phai xu ly nhieu ngon ngu trong tung dashboard query.

## TASK-039: Tao khung incremental live ingestion cho Moodle logs
- **Trang thai**: Hoan thanh khung v0, cho dau noi nguon log Moodle that.
- **Muc tieu**: Tao state va run audit cho pipeline lay Moodle logs lien tuc, de moi lan chay chi lay log moi hon watermark thay vi nap lai toan bo.
- **File anh huong**: `src/app/models/schema.py`, `src/app/core/config.py`, `src/app/services/moodle_log_ingestion_service.py`, `src/app/api/moodle_logs.py`, `scripts/seed-neon-demo.ps1`, `tests/test_main.py`, `docs/plan/09-decision-log.md`, `docs/plan/15-moodle-log-ingestion-architecture.md`.
- **Bang moi**: `moodle_log_ingestion_state` luu `last_moodle_log_id`, `last_event_time`, `last_success_at`, `status`; `moodle_log_ingestion_runs` luu tung lan chay, so dong lay ve, so dong insert/trung/loi va watermark truoc/sau.
- **API moi**: `GET /api/v1/moodle-logs/live-ingestion/status` de xem trang thai pipeline; `POST /api/v1/moodle-logs/live-ingestion/run-once` de chay mot batch incremental.
- **Nguon v0**: Ho tro adapter doc PostgreSQL Moodle standard log store thong qua bien moi truong `MOODLE_LOG_SOURCE_DATABASE_URL`. Khi chua cau hinh nguon, endpoint tra `not_configured` thay vi gia lap thanh cong.
- **Ghi chu hoc tap**: Watermark la cot dung de nho "da xu ly den dau". Trong pipeline log, watermark tot nhat la `moodle_log_id` tang dan; neu khong co id on dinh moi dung den timestamp.

## TASK-045: Chuẩn Bị Chạy Live Log Ingestion Định Kỳ Ở Localhost
- **Trạng thái**: Hoàn thành bước khung vận hành local, chờ cấu hình nguồn Moodle read-only thật.
- **Mục tiêu**: Cho phép chạy pipeline lấy log mới theo chu kỳ 30-60 phút ở localhost mà không cần upload CSV thủ công.
- **File ảnh hưởng**: `.env.example`, `scripts/run-live-log-ingestion-loop.ps1`, `docs/plan/09-decision-log.md`, `docs/plan/15-moodle-log-ingestion-architecture.md`, `tests/test_main.py`.
- **Cách chạy local**: Sau khi cấu hình `MOODLE_LOG_SOURCE_DATABASE_URL` trong `.env` và restart app, chạy `.\scripts\run-live-log-ingestion-loop.ps1 -IntervalMinutes 30`.
- **Ghi chú học tập**: Script này đóng vai trò scheduler đơn giản. Trong data engineering thực tế, bước này có thể được thay bằng cron, GitHub Actions, Airflow, Dagster hoặc Prefect, nhưng logic cốt lõi vẫn là gọi một batch incremental có watermark và audit.
