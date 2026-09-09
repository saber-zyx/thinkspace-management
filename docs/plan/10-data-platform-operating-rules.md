# Quy Tắc Vận Hành Nền Tảng Dữ Liệu

## Trạng Thái
QUY TẮC CỨNG. Các quy tắc này áp dụng cho mọi công việc tương lai khi ThinkSpace được mở rộng từ công cụ tiếp nhận người dùng thành nền tảng phân tích học tập Moodle và dự án kỹ thuật dữ liệu.

## Định Hướng Sản Phẩm
ThinkSpace sẽ phát triển từ công cụ đăng ký/tiếp nhận người dùng thành nền tảng phân tích học tập trên Moodle.

Nền tảng phải giúp quản lý chương trình trả lời các câu hỏi vận hành thực tế:
- Đã tiếp nhận được bao nhiêu thí sinh/người dùng?
- Người dùng nào đã truy cập Moodle, người dùng nào vẫn hiện `Never`?
- Người dùng nào đang hoạt động, không hoạt động, hoặc có nguy cơ bỏ học?
- Mỗi người dùng đã học tới đâu trong nội dung khóa học?
- Mỗi đội nhóm đang tiến bộ như thế nào?
- Phân đoạn, hoạt động, tài nguyên hoặc bài học nào có nhiều hoặc ít sự chú ý?
- Các ID thô từ Moodle cần được ánh xạ thành nhãn nào để người quản lý đọc được: người dùng, đội nhóm, khóa học, học phần, phân đoạn, sự kiện?

## Quy Tắc Làm Việc Cùng Người Dùng
Mỗi câu trả lời và mỗi bước triển khai phải tuân thủ:
- Mỗi lần chỉ tập trung vào một ý chính hoặc một kết quả bàn giao.
- Không trả lời bằng quá nhiều hướng lớn khi người dùng đang cần một bước cụ thể.
- Vừa xây dựng vừa dạy: giải thích khái niệm, làm mẫu một ví dụ, rồi đưa ra một phần nhỏ để người dùng thực hành khi phù hợp.
- Giải thích thân thiện với người mới học về mô hình dữ liệu, SQL, nạp dữ liệu, biến đổi dữ liệu, điều phối quy trình và thiết kế bảng điều khiển.
- Gắn mỗi tính năng với một kỹ năng hồ sơ năng lực của Nhà phân tích dữ liệu hoặc Kỹ sư dữ liệu.
- Khi có thay đổi liên quan đến database, luôn đưa SQL mẫu để người dùng tự chạy trong DBeaver và hiểu kết quả.
- Trước khi code một bảng, pipeline hoặc tầng dữ liệu mới, phải dừng lại ở bước thiết kế để người dùng cùng tham gia: đọc dữ liệu mẫu, xác định grain, đề xuất cột, đoán khóa chống trùng, và viết SQL kiểm chứng.
- Không chỉ giao cho người dùng các bước cuối đơn giản. Người dùng phải được tham gia cả các bước tư duy chính: vì sao chọn bảng này, vì sao đặt cột này, vì sao lọc event này, và vì sao metric này đáng tin.
- Sau mỗi deliverable data engineering, phải giải thích trạng thái hiện tại: phần nào là code chính đã chạy trong hệ thống, phần nào là v0 có thể thay đổi, phần nào chỉ là test hoặc tài liệu.
- Cập nhật tài liệu dự án khi quy trình làm việc, kiến trúc, mô hình dữ liệu hoặc hướng triển khai thay đổi.

## Quy Tắc Thiết Kế Kỹ Thuật Dữ Liệu
Dữ liệu vận hành của Moodle là dữ liệu nguồn OLTP. Không dùng trực tiếp dữ liệu này làm bảng cuối cho bảng điều khiển.

Các phần phân tích Moodle tương lai nên đi theo pipeline nhiều lớp:
- Lớp raw/landing: lưu dữ liệu trích xuất gần với nguồn Moodle nhất có thể.
- Lớp bronze: ép kiểu dữ liệu và làm sạch nhẹ các thực thể/log Moodle.
- Lớp silver: khử trùng lặp, gắn nhãn, nối bảng và tạo bảng sẵn sàng phân tích.
- Lớp gold: tạo các bảng mart phục vụ bảng điều khiển cho quản lý chương trình.

Cần thiết kế mô hình các thực thể cốt lõi trước khi viết code:
- users
- teams
- courses
- enrollments
- course_sections
- course_modules
- activities/resources
- logs/events
- user_activity_sessions
- progress/completion_snapshots
- team_progress_snapshots

ID thô từ Moodle phải được ánh xạ sang nhãn dễ đọc trước khi xuất hiện trên bảng điều khiển cho quản lý.

## Quy Tắc Pipeline
Mỗi tính năng pipeline dữ liệu phải định nghĩa:
- Nguồn: Moodle API, báo cáo xuất file, file log, live logs hoặc truy cập database.
- Grain: một dòng dữ liệu đại diện cho điều gì.
- Khóa chính hoặc khóa tự nhiên.
- Con trỏ tăng dần: timestamp, log id, thời điểm chỉnh sửa hoặc checkpoint đáng tin cậy khác.
- Quy tắc lũy đẳng: chạy lại cùng một lần nạp dữ liệu không được tạo dòng trùng lặp.
- Kiểm tra chất lượng dữ liệu: khóa null, khóa trùng, timestamp sai, ID chưa ánh xạ.
- Tần suất làm mới: hằng ngày, mỗi 2 giờ, mỗi 60 giây hoặc thủ công.

Có thể thu thập log gần thời gian thực, nhưng bảng điều khiển mặc định nên dùng các bảng đã biến đổi ổn định, trừ khi người dùng yêu cầu rõ một chế độ xem vận hành trực tiếp.

## Quy Tắc Phân Tích Moodle
Phân tích học tập phải hỗ trợ cả cấp người dùng và cấp đội nhóm:
- Kích hoạt người dùng: lần truy cập đầu, lần truy cập cuối, chưa từng truy cập.
- Mức độ tham gia: lượt xem, hành động, số ngày hoạt động, hoạt động gần đây.
- Tiến độ học tập: phân đoạn đã xem, hoạt động đã hoàn thành, phần trăm hoàn thành nếu Moodle cung cấp.
- Tiến độ đội nhóm: tổng hợp chỉ số của các thành viên trong đội.
- Mức độ chú ý nội dung: hoạt động/tài nguyên/phân đoạn có lượt xem cao hoặc thấp.
- Khả năng kiểm chứng: có thể truy ngược một chỉ số trên bảng điều khiển về log nguồn.

## Quy Trình Triển Khai
Mỗi công việc nền tảng dữ liệu tương lai sẽ đi theo thứ tự này, trừ khi người dùng yêu cầu thu hẹp phạm vi:
1. Định nghĩa câu hỏi nghiệp vụ.
2. Định nghĩa grain và mô hình dữ liệu.
3. Xác định nguồn và cách trích xuất.
4. Tạo hoặc cập nhật vùng raw/staging.
5. Biến đổi thành bảng sẵn sàng phân tích.
6. Thêm kiểm tra chất lượng dữ liệu.
7. Xây dựng hoặc cập nhật API endpoint.
8. Xây dựng hoặc cập nhật bảng điều khiển.
9. Kiểm tra với dữ liệu mẫu và dữ liệu thật khi có.
10. Cập nhật tài liệu và nhật ký quyết định.

## Quy Trình Giảng Dạy
Khi hướng dẫn người dùng trong lúc triển khai:
- Bắt đầu bằng mô hình tư duy đơn giản nhất.
- Đưa ra đúng ví dụ SQL, mô hình dữ liệu hoặc pipeline đang được dùng.
- Giải thích vì sao chọn thiết kế đó.
- Đưa ra một bài tập nhỏ để người dùng lặp lại.
- Tránh đưa quá nhiều kiến trúc tương lai trong một lần.

## Quy Tắc Tài Liệu
Bắt buộc cập nhật tài liệu khi công việc thay đổi bất kỳ nội dung nào:
- mô hình dữ liệu
- thiết kế pipeline
- cách tích hợp Moodle
- định nghĩa chỉ số trên bảng điều khiển
- tần suất làm mới
- ánh xạ từ nguồn sang đích
- quyết định kiến trúc

Dùng `docs/plan/` làm nguồn chân lý và `docs/plan/09-decision-log.md` để lưu quyết định.

## Quy Tắc Bảo Mật Và Riêng Tư
Dữ liệu học tập Moodle có thể chứa hành vi học tập nhạy cảm. Các bước tương lai phải:
- Không bao giờ lộ thông tin đăng nhập hoặc mã truy cập.
- Không ghi bí mật vào log.
- Không hiển thị dữ liệu cá nhân không cần thiết trên bảng điều khiển tổng quan.
- Ưu tiên chỉ số tổng hợp cho màn hình tổng quan của quản lý.
- Chỉ tạo màn hình xem chi tiết theo từng người dùng khi có mục đích rõ ràng và phù hợp quyền truy cập.

## Định Nghĩa Hoàn Thành
Một công việc nền tảng dữ liệu chỉ được xem là hoàn thành khi:
- Câu hỏi nghiệp vụ đã được trả lời.
- Grain và mô hình dữ liệu đã được ghi vào tài liệu.
- Pipeline có tính lũy đẳng, hoặc giới hạn của nó đã được ghi rõ.
- Test hoặc các bước kiểm chứng đã chạy.
- Nhãn trên bảng điều khiển đọc được và không lộ ID thô khi đã có nhãn thay thế.
- Tài liệu đã được cập nhật.
