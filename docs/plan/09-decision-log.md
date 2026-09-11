# Nhật Ký Quyết Định

## ADR-001: Sử Dụng Một Model Member Chuẩn
- **Quyết định**: Tất cả đầu vào (Google Sheet, Forms, v.v.) sẽ được parse (phân tích) vào một model Pydantic thống nhất tên là `Member` trước khi xử lý.
- **Lý do**: Giúp tách biệt hoàn toàn logic nghiệp vụ của Moodle khỏi các định dạng nguồn cấp dữ liệu khác nhau.

## ADR-002: Tách Biệt Việc Tạo Người Dùng và Việc Ghi Danh
- **Quyết định**: Cụm tích hợp Moodle sẽ phải kiểm tra rõ ràng xem người dùng đã tồn tại chưa, tạo mới nếu thiếu, SAU ĐÓ mới kiểm tra trạng thái ghi danh và tiến hành ghi danh nếu chưa có.
- **Lý do**: Giải quyết triệt để lỗi chí mạng khi những người dùng Moodle đã tồn tại bị bỏ qua chỉ vì tính năng bulk-upload báo lỗi trùng lặp khi tạo tài khoản.

## ADR-003: Không Sử Dụng Các Bộ Điều Phối (Orchestrators) Phức Tạp Trong MVP
- **Quyết định**: Tuyệt đối không dùng Airflow, Celery, hay Kafka trong Giai đoạn 1 (Phase 1). Ưu tiên dùng luồng logic đồng bộ (synchronous) đơn giản của FastAPI hoặc các background tasks mặc định.
- **Lý do**: Giữ cho kiến trúc đơn giản và dễ dàng triển khai.

## ADR-004: Google Sheet Là Nguồn Dữ Liệu Duy Nhất Ban Đầu
- **Quyết định**: Tạm hoãn việc đọc PDF, OCR, Excel, hay tích hợp trực tiếp API nhập liệu.
- **Lý do**: Tập trung công sức phát triển vào luồng tích hợp Moodle cốt lõi và hệ thống validation trước tiên.

## ADR-005: Trì Hoãn PostgreSQL
- **Quyết định**: Không sử dụng database cho lần lặp (iteration) hoạt động đầu tiên. Trả về kết quả trực tiếp.
- **Lý do**: Cần phải chứng minh được luồng Google Sheet -> Moodle hoạt động tốt trước khi thêm phần quản lý trạng thái (state management).

## ADR-006: Xóa Bỏ Các Agent Skills Không Dùng Đến
- **Quyết định**: Xóa toàn bộ dump khổng lồ trong thư mục `skills/`.
- **Lý do**: Hơn 1000 kỹ năng AI chung chung chỉ gây nhiễu và hoàn toàn không phục vụ cho mục đích cụ thể của dự án này. Các kỹ năng tùy chỉnh sẽ chỉ được bổ sung khi có một luồng công việc cần lặp lại nhiều lần (ví dụ: `moodle-api-integration`).

## ADR-007: Phát Triển ThinkSpace Thành Nền Tảng Phân Tích Học Tập Moodle
- **Quyết định**: Các bước phát triển tiếp theo sẽ mở rộng ThinkSpace từ công cụ tiếp nhận người dùng thành nền tảng phân tích học tập Moodle. Moodle logs, live logs, activity reports, lần truy cập cuối, tiến độ hoàn thành, người dùng, đội nhóm, khóa học, phân đoạn, học phần và sự kiện sẽ được mô hình hóa qua pipeline nhiều lớp trước khi đưa lên bảng điều khiển.
- **Lý do**: Quản lý chương trình không chỉ cần biết đã tiếp nhận bao nhiêu người dùng, mà còn cần biết người dùng có đang hoạt động không, đã từng truy cập Moodle chưa, đang xem nội dung nào, mỗi người dùng/đội nhóm đã học tới đâu, và hoạt động nào có nhiều hoặc ít sự chú ý.
- **Quy tắc vận hành**: Mọi công việc phân tích Moodle trong tương lai phải tuân thủ `docs/plan/10-data-platform-operating-rules.md`, tập trung vào một kết quả bàn giao mỗi lần, vừa xây dựng vừa hướng dẫn người dùng, và cập nhật tài liệu khi kiến trúc, quy trình làm việc, định nghĩa chỉ số hoặc mô hình dữ liệu thay đổi.

## ADR-008: Bắt Đầu Moodle Analytics Bằng Data Model Log V0
- **Quyết định**: Bước đầu của nền tảng dữ liệu sẽ dùng file log mẫu `example/logs_SANDBOX2026_20260907-2141.csv` để thiết kế mô hình `raw -> bronze -> silver -> gold`. Bảng lõi đầu tiên là `bronze_moodle_log_events`, với grain là một dòng log Moodle đại diện cho một event của một user tại một thời điểm.
- **Lý do**: Log Moodle đang trộn dữ liệu học tập, quản trị, báo cáo và hệ thống. Nếu đưa thẳng vào bảng điều khiển sẽ khó map ID, khó lọc admin, và dễ đếm sai chỉ số active/progress.
- **Tài liệu liên quan**: `docs/plan/11-moodle-analytics-data-model.md`.

## ADR-009: Người Dùng Phải Tham Gia Từ Bước Thiết Kế Dữ Liệu
- **Quyết định**: Từ các bước tiếp theo, trước khi code bảng, pipeline hoặc tầng dữ liệu mới, agent phải hướng dẫn người dùng tham gia vào phần thiết kế: đọc dữ liệu mẫu, xác định grain, chọn cột, chọn khóa chống trùng, dự đoán lỗi dữ liệu và viết SQL kiểm chứng.
- **Lý do**: Mục tiêu của dự án không chỉ là có sản phẩm chạy được, mà còn giúp người dùng đủ hiểu để trình bày dự án trong phỏng vấn Data Analyst/Data Engineer.
- **Quy tắc vận hành**: Không chỉ giao cho người dùng các bước cuối đơn giản. Mỗi deliverable phải có phần giải thích trạng thái hiện tại: cái gì là code chính, cái gì là v0 có thể đổi, và cái gì chỉ là test/tài liệu.

## ADR-010: Dùng Moodle Participants Export Làm Nguồn Ánh Xạ Danh Tính V0
- **Quyết định**: Trong silver pipeline v0, không map trực tiếp Moodle logs sang `registrations` bằng tên đăng ký. Thay vào đó, dùng file Moodle participants export làm nguồn ánh xạ trung gian: `bronze_moodle_log_events.user_full_name_raw` -> `participants.First name + Last name` -> `participants.Email address` -> `registrations.email`.
- **Lý do**: Moodle logs không có email, còn email là khóa ổn định nhất để nối với dữ liệu đăng ký. Kiểm tra dữ liệu mẫu cho thấy 46/48 Moodle learning users map được sang participants bằng tên Moodle, và 107/119 participants map được sang `registrations` bằng email. File participants cũng có cột `Groups`, giúp kiểm tra chéo đội nhóm từ Moodle với đội nhóm trong hệ thống đăng ký.
- **Giới hạn v0**: Nếu có hai user trùng full name trong Moodle, join bằng tên sẽ mơ hồ. Khi lấy được `moodle_user_id` trực tiếp từ participants/API, cần chuyển khóa mapping chính sang `moodle_user_id`.
- **Hướng công cụ**: dbt phù hợp để triển khai các model staging/silver/gold sau khi thiết kế grain và mapping được chốt. Chưa cần đưa dbt vào trước khi có bảng participants/staging đầu tiên trong database.

## ADR-011: Loại Test Users Khỏi Bronze Local Có Backup
- **Quyết định**: Hai Moodle user id `924` và `919` được người dùng xác nhận là tài khoản test cũ, không thuộc hệ thống chính. Các log liên quan được backup vào `backup_deleted_bronze_moodle_log_events_test_users_20260908` trước khi xóa khỏi `bronze_moodle_log_events` trong database local.
- **Lý do**: Nếu giữ test users trong bronze local, bước silver/gold sẽ bị nhiễu khi tính số user active, mapping identity và dashboard tiến độ học tập.
- **Giới hạn**: Đây là ngoại lệ có xác nhận nghiệp vụ. Quy tắc mặc định của pipeline dữ liệu vẫn là giữ raw/bronze gần nguồn nhất có thể, ưu tiên flag hoặc loại ở silver/gold thay vì xóa trực tiếp.

## ADR-012: Dùng Bảng Exclusion Để Chặn Email Participants Sai Quay Lại
- **Quyết định**: Các email participants sai hoặc thuộc tài khoản test/duplicate đã được người dùng xác nhận sẽ được lưu trong `moodle_participant_email_exclusions`. Khi import Moodle participants CSV, pipeline bỏ qua các email đang active trong bảng này.
- **Lý do**: Nếu chỉ xóa dòng sai khỏi `raw_moodle_participants`, import lại file gốc có thể đưa các dòng đó quay lại. Bảng exclusion giúp pipeline có quy tắc data quality lặp lại được và dễ audit.
- **Kết quả kiểm chứng**: Import lại file `courseid_12_participants.csv` sau khi thêm 6 exclusions cho kết quả `inserted_count = 0`, `duplicate_count = 113`, `excluded_count = 6`.

## ADR-013: Loại Log Tiêm Mai An Khỏi Bronze Local Có Backup
- **Quyết định**: Người dùng xác nhận các log liên quan tới `Tiêm Mai An` là dữ liệu cần loại khỏi phân tích. Các log có `moodle_user_id` hoặc `moodle_affected_user_id` thuộc `921`, `931` được backup vào `backup_deleted_bronze_moodle_log_events_tiem_mai_an_20260908` trước khi xóa khỏi `bronze_moodle_log_events`.
- **Lý do**: Hai Moodle user id này cùng map về một identity, làm lệch bước identity map và số learning users. Loại khỏi bronze local giúp dữ liệu học tập chính sạch hơn trước khi tạo silver.
- **Kết quả kiểm chứng**: Đã backup và xóa 111 dòng. Sau cleanup, `learning users = 44` và `matched emails = 44`.

## ADR-014: Tạo Identity Map Bằng Database View Trước Khi Dùng dbt
- **Quyết định**: Tạo view `int_moodle_user_identity_map` trong PostgreSQL để nối `raw_moodle_participants` với `registrations` bằng email. View này là lớp intermediate cho `silver_moodle_learning_events`.
- **Lý do**: Identity mapping là transformation dạng SQL, phù hợp để làm bằng view trong local v0 và có thể chuyển gần như trực tiếp sang dbt model sau này. Cách này cũng giúp người dùng thực hành cùng logic trong DBeaver trước khi code hóa.
- **Kết quả kiểm chứng**: Endpoint `/api/v1/moodle-participants/identity-map-summary` trả về `total_identities = 113`, `matched_registrations = 101`, `unmatched_registrations = 12`, `learning_users = 45`, `matched_learning_users = 45` sau khi backfill H5P/xAPI logs.
- **Ghi chú vận hành**: Các hàm ensure schema cần tránh alter cột khi không cần thiết, vì database view có thể phụ thuộc vào các cột đó.

## ADR-015: Backfill Moodle User ID Cho H5P/xAPI Logs
- **Quyết định**: Cập nhật parser Moodle log để bắt cả mẫu `user with id '...'` và `user with the id '...'`. Backfill các learning events H5P/xAPI cũ đang thiếu `moodle_user_id` trong `bronze_moodle_log_events`.
- **Lý do**: Người dùng phát hiện trong DBeaver rằng `description_raw` có user id nhưng `moodle_user_id` bị `NULL`. Nếu không sửa ở bronze, silver sẽ phải dùng fallback email không cần thiết và dashboard có nguy cơ đếm sai user.
- **Kết quả kiểm chứng**: Đã backup 201 dòng vào `backup_bronze_moodle_log_events_before_xapi_id_backfill_20260908`, backfill 201 dòng, còn 0 learning event thiếu `moodle_user_id`. Sau backfill, `learning_users = 45` và `matched_learning_users = 45`.
## ADR-016: Đếm Số Lượng Đội Bằng Tên Đã Chuẩn Hóa
- **Quyết định**: Chỉ số `Số Lượng Đội` trên dashboard đăng ký phải đếm theo khóa chuẩn hóa `lower(trim(team_name))`, không đếm trực tiếp theo chuỗi `team_name` thô.
- **Lý do**: Dữ liệu thực tế có biến thể cùng một đội nhưng khác chữ hoa/thường, ví dụ `STABILY - ...` và `Stabily - ...`. Nếu đếm chuỗi thô, dashboard báo `23` đội; sau chuẩn hóa, số đội đúng trong database hiện tại là `22`.
- **Kết quả kiểm chứng**: Đã chuẩn hóa 1 dòng `registrations` từ biến thể `Stabily` về canonical `STABILY`. Endpoint `GET /api/v1/dashboard/stats` trả `total_teams = 22`, `total_users = 101`, `total_individuals = 18`.
- **Ghi chú dữ liệu**: `Weave Carbon` tồn tại trong `registrations` và `raw_moodle_participants`, nhưng chưa có learning log trong dữ liệu hiện tại. Không tìm thấy team/email/group chứa `Airweave` trong các bảng đã kiểm tra.
## ADR-017: Tạo View Silver Cho Moodle Learning Events
- **Quyết định**: Tạo view PostgreSQL chính thức `silver_moodle_learning_events` để lọc learning events từ bronze và nối sang `int_moodle_user_identity_map`.
- **Lý do**: Dashboard học tập không nên đọc trực tiếp từ `bronze_moodle_log_events`, vì bronze vẫn là log thô. Silver cần cung cấp danh tính đã map, email, team, activity, ngày event và các cờ phân loại cơ bản như `is_view_event`, `is_completion_event`.
- **Grain**: Một dòng trong `silver_moodle_learning_events` đại diện cho một learning event Moodle đã được map danh tính.
- **Kết quả kiểm chứng**: `learning_event_rows = 1461`, `learning_users = 45`, `matched_learning_emails = 45`, `learning_teams = 14`, `unmapped_event_rows = 0`, `duplicated_bronze_events = 0`.
- **Ghi chú công cụ**: View này đang được tạo bằng SQLAlchemy startup hook. Khi đưa dbt vào dự án, view này là ứng viên chuyển thành model `silver_moodle_learning_events.sql`.
## ADR-018: Chống Trùng Log Khi Import Các File Export Chồng Lấn
- **Quyết định**: Đổi `event_hash` của Moodle logs sang hash logic dựa trên nội dung event đã chuẩn hóa và số thứ tự xuất hiện của các event giống nhau trong cùng một file, không dựa vào `source_file_name`.
- **Lý do**: File `logs_SANDBOX2026_20260909-1639.csv` có `4191` dòng, trong đó `3691` dòng trùng với file export cũ và chỉ có `500` dòng mới. Nếu dùng hash cũ gồm tên file, pipeline sẽ nhân đôi lịch sử mỗi lần import bản export mới.
- **Kết quả kiểm chứng**: Sau migration hash v2, import file mới thêm `494` dòng mới, bỏ qua `3521` dòng trùng, loại trừ `176` dòng thuộc user exclusion, và không có lỗi parse.

## ADR-019: Phân Biệt Access, Submission Work Và Submission Final
- **Quyết định**: Trong Silver, event học tập được gắn `progress_signal_type` gồm `access`, `submission_work`, `submission_final`, `other_learning`. Chỉ event `A submission has been submitted.` được xem là tín hiệu hoàn thành submission v0.
- **Lý do**: Các event như `Submission created.`, `Submission updated.`, `A file has been uploaded.`, `An online text has been uploaded.` cho thấy người học đang thao tác bài nộp, nhưng chưa chắc đã bấm submit cuối cùng. Dashboard hoàn thành cần tách rõ trạng thái này.
- **Kết quả kiểm chứng**: Sau khi import log mới, Silver có `1905` access events, `35` submission work events và `8` submission final events. Tất cả `8` submission final hiện thuộc một người học: `Nguyễn Bá Lộc`.

## ADR-020: Tạo Dimension Moodle Course Activities Từ Log
- **Quyết định**: Tạo view `dim_moodle_course_activities` từ `bronze_moodle_log_events`, grain là một dòng cho mỗi `moodle_course_module_id`.
- **Lý do**: `moodle_course_module_id` là khóa activity/module trong Moodle. Dashboard tiến độ cần một dimension để biết id đó là Assignment/Page/H5P/File/Forum nào, có phải activity nộp bài không, và có bao nhiêu người đã xem/nộp.
- **Kết quả kiểm chứng**: Dimension hiện có `59` activities, gồm `17` Assignment submission activities, `29` learning materials, `8` final submit events và `1` submitter duy nhất toàn hệ thống.
## ADR-021: Gold User Learning Summary Dùng Participants Làm Base
- **Quyết định**: Tạo view `gold_user_learning_summary` với grain `một dòng = một participant Moodle trong một course`, lấy `int_moodle_user_identity_map` làm base và left join sang `silver_moodle_learning_events`.
- **Lý do**: Dashboard tiến độ cần thấy cả người chưa học. Nếu dùng Silver làm base thì chỉ thấy người đã phát sinh event, không trả lời được câu hỏi `Never` hoặc `not_started`.
- **Định nghĩa trạng thái v0**: `not_started` nếu không có learning event; `submitted` nếu có ít nhất một `A submission has been submitted.`; `active` nếu có learning event và truy cập trong 7 ngày gần nhất; `inactive` nếu đã từng học nhưng quá 7 ngày chưa quay lại.
- **Kết quả kiểm chứng**: Gold hiện có `113` users, `53` accessed users, `60` not started users, `1` submitted user, `16` active teams và `22` teams tổng trong Gold.
## ADR-022: Dashboard Chương Trình Dùng Registrations Làm Base
- **Quyết định**: Tạo view `gold_registered_user_learning_summary` với grain `một dòng = một người đăng ký hợp lệ trong bảng registrations`. Dashboard quản lý chương trình sẽ ưu tiên view này thay vì `gold_user_learning_summary`.
- **Lý do**: Moodle participants có thể chứa admin, mentor, tài khoản hỗ trợ, user test hoặc người không thuộc danh sách đăng ký Sandbox. Nếu dùng toàn bộ participants làm base, chỉ số tổng user có thể là `113` hoặc `119`, trong khi danh sách đăng ký hợp lệ hiện tại là `101`.
- **Kết quả kiểm chứng**: `total_registered_users = 101`, `mapped_to_moodle_users = 101`, `accessed_users = 47`, `not_started_users = 54`, `submitted_users = 1`, `total_registered_teams = 22`, `active_registered_teams = 16`.
- **Ghi chú vận hành**: `gold_user_learning_summary` vẫn được giữ để audit toàn bộ Moodle participants. Khi build dashboard chính thức, card tiến độ chương trình nên đọc từ `gold_registered_user_learning_summary`.
## ADR-023: Team Dashboard Dùng Gold Team Summary Làm Semantic Layer
- **Quyết định**: Tạo view `gold_team_learning_summary` từ `gold_registered_user_learning_summary` và `silver_moodle_learning_events`. Dashboard tab/filter theo team sẽ đọc từ view này.
- **Lý do**: Manager cần xem tiến độ theo đội, không chỉ theo từng người. Nếu frontend tự aggregate từ user rows, logic trạng thái đội, số activity đã xem và submission dễ bị lặp lại ở nhiều nơi.
- **Định nghĩa trạng thái đội v0**: `not_started` nếu chưa có thành viên nào có learning event; `submitted` nếu có ít nhất một thành viên đã submit; `active` nếu có thành viên active trong 7 ngày gần nhất; `inactive` nếu đội từng học nhưng không còn active.
- **Ghi chú dashboard**: Overview sẽ nhìn toàn hệ thống và section/submission; team filter sẽ drill-down từng đội và thành viên; individual filter sẽ dành cho người tham gia cá nhân, sau này có thể liên quan tới workflow chuyển cá nhân thành nhóm.
## ADR-024: Individual Dashboard Có Gold View Riêng
- **Quyết định**: Tạo view `gold_individual_learning_summary` bằng cách lọc các dòng không có `team_name_key` từ `gold_registered_user_learning_summary`.
- **Lý do**: Dashboard cần một filter riêng cho thí sinh cá nhân. Nếu chỉ dùng chung view registered user, frontend sẽ phải tự nhớ điều kiện lọc và dễ lệch logic giữa các màn hình.
- **Cờ dữ liệu mới**: `individual_group_status` phân biệt `individual_solo` và `individual_with_moodle_group`. Cờ này giúp phát hiện sớm trường hợp cá nhân đã được thêm vào group Moodle để sau này xử lý workflow chuyển cá nhân thành nhóm.
- **Ghi chú vận hành**: Chưa tự động chuyển cá nhân thành team ở bước này. Vấn đề đó đã được ghi vào `docs/optimization/02-individual-to-team-group-sync.md`.
## ADR-025: Learning Dashboard Overview Đọc Từ Semantic API
- **Quyết định**: Tạo endpoint `GET /api/v1/moodle-logs/learning-dashboard-overview` làm nguồn dữ liệu v0 cho tab overview của dashboard học tập.
- **Lý do**: Overview cần gom nhiều lớp dữ liệu: registered users, teams, individuals, activities và submissions. Nếu để frontend tự ghép nhiều endpoint nhỏ, logic business sẽ bị rải rác và khó kiểm soát.
- **Phạm vi v0**: Endpoint trả tổng quan người học, đội, cá nhân, phân bố activity type, activity xem nhiều, activity ít chú ý, submission activities, recent submissions và submitted teams.
- **Ghi chú nghiệp vụ**: Tất cả số trong overview được neo theo `gold_registered_user_learning_summary`, tức là chỉ tính người đăng ký hợp lệ trong chương trình, không tính admin hoặc participants ngoài chương trình.
## ADR-026: Learning Dashboard Frontend Tách File JS Riêng
- **Quyết định**: Dựng UI học tập trong `learning-dashboard.js` thay vì nhồi thêm toàn bộ logic vào `app.js`.
- **Lý do**: Dashboard đăng ký và dashboard học tập có nguồn dữ liệu, biểu đồ, bảng và hành vi filter khác nhau. Tách file giúp giảm rủi ro sửa một dashboard làm hỏng dashboard còn lại.
- **Phạm vi v0**: UI có sidebar entry `Learning Dashboard`, tab `Overview`, `Team`, `Individual`, KPI cards, biểu đồ trạng thái, bảng activity, bảng submission, bảng đội và bảng cá nhân.
- **Ghi chú vận hành**: Vì frontend bị cache mạnh trên trình duyệt, `index.html` đã tăng version CSS/JS. Sau khi cập nhật UI cần dùng `Ctrl + F5` để tải lại tài nguyên mới.

## ADR-027: Drill-down Đội Đọc Gold Thành Viên Và Silver Hoạt Động
- **Quyết định**: Tab đội của bảng điều khiển học tập dùng `gold_team_learning_summary` để liệt kê đội, dùng `gold_registered_user_learning_summary` để lấy từng thành viên, và dùng `silver_moodle_learning_events` để hiển thị các hoạt động thực tế của từng thành viên khi mở chi tiết.
- **Lý do**: Người quản lý cần xem bên trong từng đội, không chỉ xem tổng số đội. Nếu chỉ đọc Gold team aggregate thì biết đội có bao nhiêu người học, nhưng không biết ai đã xem/nộp hoạt động nào. Nếu chỉ đọc Silver thì sẽ mất những thành viên chưa bắt đầu vì họ chưa có log. Kết hợp Gold và Silver giúp vừa giữ đủ thành viên, vừa drill-down được hành vi thật.
- **Quy tắc hiển thị v0**: Modal chỉ hiển thị những hoạt động đã có log. Những activity hoặc H5P không hiển thị nghĩa là chưa có log cho hoạt động đó trong dữ liệu hiện tại.
- **Ghi chú vận hành**: Activity type và tên activity từ Moodle có thể giữ tiếng Anh để bám sát nguồn log. Modal không dùng nhãn chung chung ở từng activity, mà hiển thị số lượt view, số sự kiện, số thao tác nộp bài và số lần đã nộp bài nếu có.

## ADR-028: Activity Detail Ưu Tiên Số Liệu Log Thay Vì Badge Chung
- **Quyết định**: Activity detail trong modal đội và cá nhân sẽ hiển thị các chip số liệu như `lượt view`, `sự kiện`, `thao tác nộp bài`, `đã nộp bài`, thay vì gắn badge trạng thái chung cho từng activity.
- **Lý do**: Một người dùng có thể vừa xem nhiều activity, vừa thao tác nhiều submission khác nhau. Badge chung dễ làm manager hiểu nhầm rằng người học đã hoàn thành toàn bộ nội dung. Tên activity từ Moodle đã cho biết người dùng đang ở submission nào, còn chip số liệu cho biết mức độ tương tác cụ thể.
- **Quy tắc ngôn ngữ UI**: UI quản lý ưu tiên tiếng Việt tự nhiên. Các tên activity/type lấy từ Moodle có thể giữ nguyên theo log nguồn nếu chúng là nhãn chính thức của khóa học.
- **Phạm vi hiện tại**: Tab cá nhân có nút `Chi tiết` và dùng endpoint `individual-activities-detail` để xem activity log của từng thí sinh cá nhân.

## ADR-029: Deploy Demo Dùng Render Và Neon
- **Quyết định**: Bản demo công khai trước mắt sẽ dùng Render Web Service cho FastAPI/static frontend và Neon PostgreSQL cho database.
- **Lý do**: App hiện tại đã đọc database qua `DATABASE_URL`, nên có thể chuyển từ PostgreSQL local sang PostgreSQL managed mà không đổi logic business. Render cũng hỗ trợ start command Python dùng biến `$PORT`, phù hợp với FastAPI.
- **Phạm vi**: Đây là demo để manager xem dashboard, chưa phải production. Chưa đưa Moodle token hoặc Google service account thật lên cloud nếu chưa cần chạy onboarding/ingestion tự động.
- **Tài liệu vận hành**: Xem `docs/plan/14-demo-deploy-render-neon.md`.

## ADR-030: Ingestion Moodle Logs Không Scrape Live Logs UI
- **Quyết định**: Pipeline log dài hạn sẽ không scrape giao diện Live logs HTML. Nguồn ưu tiên là Moodle External Database Log Store hoặc quyền đọc database log Moodle bằng tài khoản read-only.
- **Lý do**: Live logs là giao diện cho người quản trị xem, không phải contract dữ liệu ổn định. Pipeline data engineer cần nguồn có schema, watermark và khả năng audit.
- **Cơ chế incremental**: Dùng watermark theo `last_moodle_log_id` hoặc `last_event_time`, chỉ lấy log mới, rồi ghi vào raw/bronze và refresh silver/gold.
- **Tài liệu vận hành**: Xem `docs/plan/15-moodle-log-ingestion-architecture.md`.

## ADR-031: Seed Demo Neon Bằng Schema + Column Inserts
- **Quyết định**: Khi seed dữ liệu demo từ PostgreSQL local sang Neon, dùng script `scripts/seed-neon-demo.ps1` để restore schema của các bảng chính trước, sau đó restore data bằng `pg_dump --column-inserts`.
- **Lý do**: Restore bằng data-only không có tên cột dễ lỗi nếu thứ tự cột giữa local và Neon lệch. Ngoài ra database local có nhiều bảng backup/audit tạm, không nên đưa toàn bộ lên Neon demo.
- **Bảng được seed**: `sync_jobs`, `registrations`, `raw_moodle_log_files`, `raw_moodle_participant_files`, `raw_moodle_participants`, `bronze_moodle_log_events`, `moodle_log_user_exclusions`, `moodle_participant_email_exclusions`.
- **Cập nhật vận hành**: Sau khi restore data, script tạm set `DATABASE_URL` sang Neon và import `src.app.main` để tạo lại các view phân tích `int/silver/gold` ngay từ local.
- **Cập nhật lỗi script**: PowerShell cần ghép tham số `pg_dump` vào biến mảng trước khi gọi helper. Nếu gọi helper rồi cộng mảng ở ngoài, tham số `-f /tmp/...` không được truyền đúng và dump sẽ in ra console.
- **Ghi chú bảo mật**: Connection string Neon chỉ được truyền bằng biến môi trường `TARGET_DATABASE_URL`, không ghi vào docs, code hoặc Git.

## ADR-032: Bắt Đầu Chuyển Transform Sang dbt
- **Quyết định**: Thêm dbt project tại `analytics/dbt_thinkspace` và chuyển model đầu tiên `int_moodle_user_identity_map` sang dbt.
- **Lý do**: Python startup hook phù hợp cho MVP nhanh, nhưng pipeline Data Engineer cần SQL transform có cấu trúc, có test, có lineage và có thể chạy độc lập theo lịch. dbt là tool phù hợp cho lớp transform `staging -> intermediate -> marts`.
- **Phạm vi hiện tại**: Chưa xóa các hàm ensure view trong FastAPI. dbt project chạy song song để học và kiểm chứng trước, sau đó mới chuyển dần `silver/gold`.
- **Schema dbt**: Các model dbt được tạo trong schema `analytics`; các bảng nguồn của app vẫn ở schema `public`. Cách này tránh làm ảnh hưởng dashboard hiện tại trong lúc học và chuyển đổi dần.
- **Dependency mới**: `dbt-postgres==1.11.0` trong `requirements-data.txt`, tách khỏi `requirements.txt` của web app.
- **Tài liệu học tập**: Xem `docs/plan/16-dbt-transformation-workflow.md`.

## ADR-033: Cap Nhat Demo Web Bang Batch Seed Truoc Khi Co Live Ingestion
- **Quyet dinh**: Trong giai doan demo ngay 2026-09-10, dashboard localhost duoc cap nhat bang cach import file Moodle log CSV moi nhat vao PostgreSQL local, sau do seed lai Neon cho Render doc du lieu moi.
- **Ly do**: Live logs/incremental ingestion chua duoc xay dung xong, nen batch seed la cach nhanh va kiem soat duoc de dua so lieu moi len demo web cho manager xem truoc.
- **Ranh gioi hien tai**: Cach nay khong phai pipeline tu dong dai han. Buoc live ingestion sau se can watermark, lich chay, log audit va co che retry.
- **Ket qua kiem chung local**: Sau khi nap `logs_SANDBOX2026_20260910-0640.csv`, local co `4176` bronze events, `2068` silver learning events, `55` learning emails va `17` learning teams.
- **Ghi chu bao mat**: Connection string Neon chi duoc truyen qua bien moi truong `TARGET_DATABASE_URL`, khong ghi vao code, docs, Git hoac noi dung chat.

## ADR-034: Ep PostgreSQL Search Path Ve Public Khi Ket Noi Neon
- **Quyet dinh**: App FastAPI dung SQLAlchemy event `connect` de chay `SET search_path TO public` sau khi mo ket noi PostgreSQL.
- **Ly do**: Sau khi reset schema tren Neon, ket noi co the bao loi `no schema has been selected to create in` khi SQLAlchemy chay `CREATE TABLE`. Tuy nhien Neon pooler khong chap nhan startup parameter `options=search_path`, nen khong duoc dua `search_path` vao URL hoac `connect_args`. Cach dung event sau ket noi phu hop hon voi pooler.
- **Ket qua kiem chung**: Script seed Neon da chay thanh cong; Neon co `4176` bronze events, `113` Moodle participants va `101` registrations. API Render da doc du lieu moi tu Neon.

## ADR-035: Tach Tin Hieu Guideline, Survey Va Hoc Sau Cong
- **Quyet dinh**: Learning Dashboard Overview theo doi rieng `UEH LMS Registration Guideline (FMC3)`, trang `Pre-Program Survey`, subsection `Foundations of Digital Entrepreneurship Course`, va nhom nguoi da vao noi dung sau cong survey.
- **Ly do**: Manager can biet nguoi hoc co doc huong dan LMS va co di qua survey hay khong. Khong duoc xem `Course module viewed` la da hoan thanh survey; day chi la tin hieu da xem/mo activity. Tin hieu hoan thanh survey can duoc xac dinh rieng khi log Moodle co event submit/complete phu hop.
- **Quy tac dem v0**: Cac chi so spotlight chi dem user co trong `gold_registered_user_learning_summary`. Cac log khong map duoc email dang ky khong duoc tinh vao ty le thí sinh.
- **Ket qua local hien tai**: Guideline LMS co `3` nguoi dang ky da xem; trang survey co `26` nguoi xem; `35` nguoi da truy cap noi dung khac sau cong survey. Cac chi so FMC3 duoc tach rieng trong ADR-037.

## ADR-036: Khong Tron Log He Thong Vao Tuong Tac Hoc Tap
- **Quyet dinh**: Learning Dashboard chi tinh tuong tac hoc tap bang log cua learner da map duoc vao danh sach dang ky. Log admin/system nhu `Course module created` hoac `Course module updated` duoc hien nhu ghi chu van hanh neu can, khong cong vao KPI nguoi hoc.
- **Ly do**: Module `712` Foundations hien co log `Course module created/updated` do admin thuc hien, nhung chua co learner interaction. Neu cong log nay vao KPI, manager se hieu nham rang thi sinh da truy cap noi dung.
- **Quyet dinh Pre-Program Survey**: Spotlight chi hien page `Pre-Program Survey` module `707`. Activity an module `709` khong hien trong spotlight/phieu manager vi no khong phai diem cham truc tiep nguoi hoc thay tren giao dien.
- **Tac dong**: UI co the hien "co log he thong, chua co thi sinh truy cap" cho activity quan trong, giup phan biet tinh trang cau hinh Moodle voi hanh vi hoc tap that.

## ADR-037: Tach Funnel Survey Va Funnel FMC3
- **Quyet dinh**: `Pre-Program Survey` va `Foundations of Digital Entrepreneurship Course` duoc tinh bang hai summary rieng. `pre_program_gate_summary` khong con chua chi so "bo guideline nhung van vao tai lieu". Chi so do chuyen sang `foundation_course_summary` va chi ap dung cho `UEH LMS Registration Guideline (FMC3)`.
- **Ly do**: Page survey module `707` la cong survey dau vao, trong khi guideline module `714` la huong dan dang ky LMS cua rieng khoa FMC3. Neu dat chung, manager co the hieu nham nguoi hoc bo survey guideline, trong khi thuc te la bo guideline cua khoa FMC3.
- **Dinh nghia FMC3 v0**: Sau khi doi chieu voi muc tieu quan ly, FMC3 chi tinh module `714` la `UEH LMS Registration Guideline (FMC3)` va module `716` la `Certificate Submission`. Khong gom cac H5P milestone vao card FMC3 de tranh phinh to so lieu.
- **Tac dong**: Dashboard hien rieng khoi `Pre-Program Survey` va khoi `Foundations of Digital Entrepreneurship Course`, giup nguoi quan ly doc insight dung ngu canh.

## ADR-038: Siết Scope Foundations/FMC3 Chỉ Còn 714 Và 716
- **Quyet dinh**: Card `Foundations of Digital Entrepreneurship Course` khong aggregate cac H5P/milestone nua. Metric chinh chi tinh hai module manager can theo doi: guideline `714` va submission `716`.
- **Ly do**: Cac H5P sinh nhieu log `xAPI statement received`, lam `access_event_count` tang len hang tram va de bi hieu nham la luot xem khoa hoc. Scope moi bam sat business question: co doc guideline FMC3 khong va co vao/nop Certificate Submission khong.
- **Tac dong**: So lieu FMC3 giam ve muc de giai thich: `39` access events trong scope `714/716`, gom `30` Course module viewed va `3` submission actions tren du lieu local hien tai.

## ADR-039: Theo Doi Enrollment UEH LMS Bang Raw Landing Table
- **Quyet dinh**: Them bang `raw_ueh_lms_course_enrollments` lam diem nhan du lieu dang ky khoa entrepreneurship tu UEH LMS. Dashboard join bang nay voi `registrations` bang email de tinh ty le user Sandbox da dang ky khoa.
- **Ly do**: UEH LMS la nguon ben thu ba, khong nen tron truc tiep vao Moodle logs. Tach raw table giup sau nay co the thay nguon nap du lieu bang API, read-only database, CSV hoac job dbt ma khong doi UI dashboard.
- **Metric v0**: `enrolled_registered_users / total_registered_users`, kem danh sach chi tiet cac user match email. Neu raw table chua co data, card hien `0` thay vi tu suy dien tu logs.
- **Tac dong**: Khu vuc hoat dong trong yeu co them card thu 4 cho trang thai dang ky UEH LMS entrepreneurship, phuc vu nhu cau doi chieu cross-system cua manager.

## ADR-040: Chuan Hoa Log Moodle Tieng Viet Sang Canonical Event
- **Quyet dinh**: Parser Moodle log chap nhan ca header/event name tieng Anh va tieng Viet. Cac gia tri tieng Viet duoc map ve canonical event/component/context truoc khi ghi bronze.
- **Ly do**: File log UEH LMS entrepreneurship export bang giao dien tieng Viet, trong khi pipeline ban dau duoc xay tu Moodle Sandbox giao dien tieng Anh. Neu khong canonical hoa o ingestion, silver/gold se bi tach logic theo tung ngon ngu va dashboard de dem sai.
- **Enrollment UEH LMS**: Event `Người dùng đã ghi danh khóa học` trong course id `42246` duoc dung de upsert email vao `raw_ueh_lms_course_enrollments` voi `external_course_key = 'fmc3_entrepreneurship'`.
- **Ket qua local**: File entrepreneurship moi co `18,133` dong, import khong loi, sinh `19` email enrollment nguon UEH LMS va `13` email match voi registrations.

## ADR-041: Live Log Ingestion Phai Co Watermark Va Run Audit
- **Quyet dinh**: Truoc khi lap lich lay Moodle logs moi 30 phut hoac gan real-time, he thong phai co bang `moodle_log_ingestion_state` va `moodle_log_ingestion_runs`.
- **Ly do**: Pipeline log khong duoc dua vao cam tinh "lay lai file moi nhat". Can biet lan truoc da doc den `moodle_log_id` nao, lan nay lay bao nhieu dong moi, bao nhieu dong bi trung, va neu loi thi loi o batch nao.
- **Nguon v0**: Adapter dau tien doc tu Moodle standard log store hoac database log PostgreSQL read-only qua `MOODLE_LOG_SOURCE_DATABASE_URL`. Khong scrape HTML Live logs.
- **Tac dong**: Dashboard van doc silver/gold nhu hien tai. Live ingestion chi la cach nap bronze lien tuc; cac metric dashboard khong can doi khi nguon chuyen tu CSV thu cong sang job incremental.

## ADR-042: Doi Don Vi Quan Ly Tu Doi Sang Du An
- **Quyet dinh**: Tren dashboard quan ly, `du an` la don vi tong hop gom `du an dang ky theo doi` va `du an ca nhan`. Cong thuc v0: `total_projects = total_team_projects + total_individual_projects`.
- **Ly do**: Manager khong chi quan tam co bao nhieu doi nhieu thanh vien, ma can biet tong so du an dang tham gia chuong trinh. Mot thi sinh ca nhan tu do van duoc xem la mot du an rieng de theo doi tien do hoc tap va nop bai.
- **Tac dong len dashboard dang ky**: Card `So luong doi` doi thanh `So luong du an`; card ben canh hien co cau `Doi dang ky` va `Ca nhan tu do`.
- **Tac dong len dashboard hoc tap**: Card `Du an da hoat dong` va chart `Trang thai du an` tinh tren ca du an theo doi va du an ca nhan. `active_projects = active_team_projects + accessed_individual_projects`; `submitted_projects = submitted_team_projects + submitted_individual_projects`.
- **Cap nhat hoat dong trong yeu**: Card `Foundations of Digital Entrepreneurship Course` khong con dem viec xem subsection module `712`. Tin hieu chinh duoc doi sang `Certificate Submission` module `716`, uu tien ty le user da nop certificate submission.
- **Cap nhat UI KPI**: Dashboard hoc tap gop `Tong thi sinh` va `Chua bat dau` thanh card `Ty le thi sinh co hoat dong`, hien ty le `accessed_users / total_registered_users` de manager doc nhanh muc do kich hoat nen tang.

## ADR-043: Them Bang Traction Theo Milestone Tren Overview
- **Quyet dinh**: Thay card `Hoat dong theo loai noi dung` tren Learning Dashboard Overview bang bang `Traction theo milestone`.
- **Cau hoi nghiep vu**: Manager can xem nhanh voi moi milestone, thi sinh co doc guideline khong, co vao trang submission khong, va co nop bai hoan tat khong.
- **Grain v0**: Mot dong dai dien cho mot moc hoc tap quan trong. Pham vi gom `Milestone 1`, `Milestone 2`, `Milestone 3`, `Milestone 4`, `Milestone 5`, va `Final Submission`.
- **Module mapping v0**: Guideline modules lan luot la `650`, `653`, `656`, `659`, `662`, `665`; submission modules lan luot la `651`, `654`, `657`, `660`, `663`, `666`.
- **Metric v0**: Moi dong hien `Guideline Viewed` theo views va thi sinh, `Submission Viewed` theo views va thi sinh, va `Submission Done` theo luot nop va thi sinh nop. Chi dem log da map duoc vao thi sinh trong danh sach dang ky Sandbox.
- **Tac dong pipeline**: Khong doi raw/bronze/silver. API overview tong hop truc tiep tu `silver_moodle_learning_events` va `gold_registered_user_learning_summary`, nen khi log moi duoc nap vao bronze/silver thi bang traction tu cap nhat theo du lieu hien co.

## ADR-044: Rut Gon Traction Submission Theo Du An
- **Quyet dinh**: Bo nhom cot `Submission Viewed` khoi bang `Traction theo milestone`. Bang chi giu `Guideline Viewed` va `Submission Done`.
- **Metric v0**: `Submission Done` gom hai chi so: `submitted` la so log nop bai hoan tat, `du an` la so du an duy nhat da nop trong milestone do.
- **Quy tac dem du an**: Du an nhom dung `team_name_key`; du an ca nhan dung `email`. Cong thuc khoa dem la `COALESCE(team_name_key, email)`, nen mot du an co nhieu thanh vien nop hoac nop nhieu lan van chi tinh la mot du an trong cot `du an`.
- **Chi tiet dashboard**: Moi dong milestone co nut `Xem` de mo danh sach du an da nop, so lan submitted, so user nop va lan nop cuoi.
- **Ghi chu dien giai log events**: `learning_event_count` trong modal chi tiet la tong so log events hoc tap da qua silver, khong phai so bai hoc. User co nhieu H5P/xAPI statements co the co so log events rat cao.

## ADR-045: Chạy Live Log Ingestion Local Bằng Script Scheduler Nhẹ
- **Quyết định**: Giai đoạn localhost dùng `scripts/run-live-log-ingestion-loop.ps1` để gọi `POST /api/v1/moodle-logs/live-ingestion/run-once` theo chu kỳ thay vì nhúng scheduler chạy nền trực tiếp trong FastAPI.
- **Lý do**: Cách này dễ quan sát khi học data engineering: người vận hành thấy từng run, số dòng lấy về, số dòng insert, số dòng trùng và watermark trước/sau. Nó cũng tránh việc web app tự chạy job ẩn khi nguồn Moodle chưa được cấu hình chắc chắn.
- **Điều kiện chạy thật**: `.env` local cần có `MOODLE_LOG_SOURCE_DATABASE_URL` read-only tới Moodle log store/database thật. Nếu endpoint status báo `is_configured = false`, script dừng để tránh tạo nhiều run `not_configured`.
- **Hướng nâng cấp**: Khi local ổn định, có thể chuyển scheduler sang cron, GitHub Actions, Airflow, Dagster hoặc Prefect mà vẫn giữ nguyên endpoint, bảng state và bảng run audit.
