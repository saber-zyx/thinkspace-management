# Câu hỏi nghiệp vụ cho bảng điều khiển học tập

## Mục tiêu dashboard

Dashboard học tập không chỉ trả lời câu hỏi “đã onboard bao nhiêu thí sinh”, mà phải giúp manager biết người học và đội nhóm đang thật sự sử dụng Moodle như thế nào.

## Bộ lọc 1: Tổng quan

Câu hỏi cần trả lời:

- Tổng số thí sinh đăng ký hợp lệ là bao nhiêu?
- Bao nhiêu thí sinh đã từng có hoạt động học?
- Bao nhiêu thí sinh chưa bắt đầu?
- Bao nhiêu thí sinh đã nộp submission?
- Hoạt động hoặc section nào được xem nhiều nhất?
- Hoạt động hoặc section nào ít được chú ý nhất?
- Bài nộp nào đã có người nộp?
- Đội nào đã nộp bài?

Nguồn dữ liệu chính:

```text
gold_registered_user_learning_summary
gold_team_learning_summary
gold_individual_learning_summary
dim_moodle_course_activities
silver_moodle_learning_events
```

Endpoint v0:

```text
GET /api/v1/moodle-logs/learning-dashboard-overview
```

## Bộ lọc 2: Đội

Câu hỏi cần trả lời:

- Mỗi đội có bao nhiêu thành viên đăng ký?
- Bao nhiêu thành viên trong đội đã học?
- Bao nhiêu thành viên chưa bắt đầu?
- Đội đã có ai nộp submission chưa?
- Thành viên nào trong đội đang active, inactive hoặc not started?
- Đội đã xem bao nhiêu hoạt động khác nhau?
- Khi chọn một đội, từng thành viên đã xem hoặc nộp hoạt động nào?
- Thành viên nào chưa có hoạt động nào được ghi nhận trong log?

Nguồn dữ liệu chính:

```text
gold_team_learning_summary
gold_registered_user_learning_summary
silver_moodle_learning_events
```

Endpoint chi tiết:

```text
GET /api/v1/moodle-logs/team-activities-detail?team_name_key=...
```

Ghi chú hiển thị:

```text
Những activity hoặc H5P không hiển thị nghĩa là chưa có log cho hoạt động đó trong dữ liệu hiện tại.
```

## Bộ lọc 3: Cá nhân

Câu hỏi cần trả lời:

- Có bao nhiêu thí sinh cá nhân?
- Ai đã học, ai chưa bắt đầu?
- Có cá nhân nào đã nộp bài chưa?
- Có cá nhân nào đã được đưa vào nhóm Moodle chưa?
- Khi chọn một cá nhân, người đó đã xem hoặc nộp những hoạt động nào?
- Nếu cá nhân thêm thành viên trong tương lai, quy trình chuyển thành đội sẽ xử lý thế nào?

Nguồn dữ liệu chính:

```text
gold_individual_learning_summary
gold_registered_user_learning_summary
silver_moodle_learning_events
```

Endpoint chi tiết:

```text
GET /api/v1/moodle-logs/individual-activities-detail?email=...
```

Ghi chú tối ưu liên quan:

```text
docs/optimization/02-individual-to-team-group-sync.md
```

## UI v0 đã dựng

File chính:

```text
src/app/static/index.html
src/app/static/styles.css
src/app/static/learning-dashboard.js
```

Các phần đã có:

- Sidebar có mục `Bảng Học Tập`.
- Tab `Tổng quan` hiển thị KPI, trạng thái học tập, trạng thái đội, loại hoạt động, nội dung xem nhiều, nội dung ít chú ý, hoạt động nộp bài và đội đã nộp.
- Tab `Đội` hiển thị bảng tổng hợp từng đội và có nút `Chi tiết` để xem từng thành viên cùng các hoạt động Moodle đã thực hiện.
- Tab `Cá nhân` hiển thị bảng tổng hợp từng thí sinh cá nhân và có nút `Chi tiết` để xem activity log của từng người.

Backlog insight tiếp theo:

```text
docs/plan/13-learning-dashboard-insight-backlog.md
```

Điểm cần tinh chỉnh sau khi xem bằng mắt:

- Độ rộng bảng trên màn hình nhỏ.
- Tên hoạt động hoặc đội quá dài.
- Thứ tự ưu tiên các KPI trên overview.
- Có cần thêm filter theo activity type hoặc submission milestone hay không.
