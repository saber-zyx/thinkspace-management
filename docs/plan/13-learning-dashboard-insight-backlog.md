# Backlog Insight Cho Bảng Điều Khiển Học Tập

## Mục tiêu

Tài liệu này lưu các ý tưởng insight có thể đưa vào bảng điều khiển học tập để hỗ trợ nhà quản lý chương trình theo dõi tiến độ, phát hiện rủi ro và ra quyết định vận hành.

Nguyên tắc triển khai:

```text
Mỗi lần chỉ chọn một insight nhỏ để thiết kế dữ liệu, viết SQL kiểm chứng, tạo API và đưa lên UI.
```

## Nhóm Insight Ưu Tiên Cao

### 1. Danh sách người cần nhắc nhở

Câu hỏi business:

```text
Ai chưa từng truy cập Moodle hoặc đã lâu không quay lại học?
```

Metric đề xuất:

```text
not_started_users
inactive_users
days_since_last_access
last_access_at
```

Nguồn dữ liệu:

```text
gold_registered_user_learning_summary
gold_team_learning_summary
```

Giá trị cho manager:

```text
Giúp ban tổ chức biết cần nhắc ai trước, thay vì chỉ nhìn tổng số người đã học.
```

### 2. Heatmap tiến độ theo đội và activity

Câu hỏi business:

```text
Đội nào đã xem hoặc nộp từng activity quan trọng?
```

Metric đề xuất:

```text
team_name
activity_name
unique_viewers
submission_final_count
member_completion_ratio
```

Nguồn dữ liệu:

```text
gold_registered_user_learning_summary
silver_moodle_learning_events
dim_moodle_course_activities
```

Giá trị cho manager:

```text
Nhìn nhanh đội nào đang theo kịp lộ trình, đội nào bỏ qua nhiều nội dung.
```

### 3. Phễu học tập theo mốc nội dung

Câu hỏi business:

```text
Người học rơi rụng ở mốc nào trong hành trình học?
```

Metric đề xuất:

```text
read_me_first_viewers
guideline_viewers
milestone_submission_viewers
final_submission_viewers
final_submitters
```

Nguồn dữ liệu:

```text
silver_moodle_learning_events
dim_moodle_course_activities
```

Giá trị cho manager:

```text
Cho biết nội dung nào tạo điểm nghẽn để điều chỉnh truyền thông hoặc hỗ trợ mentor.
```

## Nhóm Insight Ưu Tiên Trung Bình

### 4. Bảng xếp hạng mức độ tương tác theo đội

Câu hỏi business:

```text
Đội nào đang hoạt động tích cực nhất?
```

Metric đề xuất:

```text
active_users
learning_event_count
viewed_activity_count
active_days_count
latest_activity_at
```

Nguồn dữ liệu:

```text
gold_team_learning_summary
silver_moodle_learning_events
```

Lưu ý:

```text
Không nên xem event count là điểm số chất lượng tuyệt đối. Event count chỉ là tín hiệu tương tác.
```

### 5. Nội dung ít được chú ý nhưng quan trọng

Câu hỏi business:

```text
Activity quan trọng nào có ít người xem hoặc chưa có ai submit?
```

Metric đề xuất:

```text
activity_name
activity_type
unique_viewers
unique_submitters
last_access_at
attention_status
```

Nguồn dữ liệu:

```text
dim_moodle_course_activities
silver_moodle_learning_events
```

Giá trị cho manager:

```text
Giúp phát hiện tài nguyên học tập cần được nhắc lại hoặc đưa vào announcement.
```

### 6. Theo dõi submission theo milestone

Câu hỏi business:

```text
Milestone nào đã có đội nộp, đội nào chưa nộp?
```

Metric đề xuất:

```text
milestone_name
submitted_teams
submitted_users
latest_submission_at
team_submission_status
```

Nguồn dữ liệu:

```text
silver_moodle_learning_events
dim_moodle_course_activities
gold_team_learning_summary
```

## Nhóm Insight Sau Này

### 7. Cảnh báo bất thường dữ liệu

Câu hỏi business:

```text
Có user nào bị trùng tên, trùng email, thiếu group hoặc không map được registration không?
```

Nguồn dữ liệu:

```text
raw_moodle_participants
int_moodle_user_identity_map
registrations
```

### 8. Xu hướng học theo ngày

Câu hỏi business:

```text
Hoạt động học tăng hay giảm theo từng ngày?
```

Nguồn dữ liệu:

```text
silver_moodle_learning_events
```

### 9. Snapshot tiến độ định kỳ

Câu hỏi business:

```text
So với hôm qua hoặc tuần trước, đội nào cải thiện hoặc tụt lại?
```

Nguồn dữ liệu tương lai:

```text
gold_user_progress_snapshots
gold_team_progress_snapshots
```

Ghi chú:

```text
Insight này nên làm sau khi có pipeline tự động lấy log định kỳ.
```
