# Tối Ưu 01: Ánh Xạ Danh Tính Qua Ba Nguồn Dữ Liệu

## Trạng Thái
Ghi chú tối ưu tương lai. Chưa triển khai tối ưu ngay trong giai đoạn hiện tại.

## Bối Cảnh
Pipeline Moodle analytics hiện cần nối ba nguồn dữ liệu để biết một event học tập thuộc về thí sinh và đội nhóm nào:

```text
bronze_moodle_log_events
  -> Moodle participants export
  -> registrations
```

Lý do:
- `bronze_moodle_log_events` có `user_full_name_raw` và `moodle_user_id`, nhưng không có email.
- Moodle participants export có `First name`, `Last name`, `Email address`, `Groups`.
- `registrations` có email, thông tin đăng ký, vai trò và đội nhóm từ quy trình onboarding.

Luồng ánh xạ v0:

```text
bronze_moodle_log_events.user_full_name_raw
  = participants.First name + ' ' + participants.Last name
  -> participants.Email address
  = registrations.email
  -> registration_id, team_name, role, student_id
```

## Vì Sao Đây Chưa Phải Thiết Kế Tối Ưu Cuối Cùng
Join qua ba nguồn giúp đáng tin hơn map thẳng bằng tên, nhưng vẫn có một số điểm yếu:

- Tên người dùng có thể trùng nhau.
- Tên trong Moodle log có thể khác dấu, khác thứ tự hoặc khác định dạng.
- File participants là export thủ công, nên nếu quên cập nhật thì mapping có thể cũ.
- `Groups` trong participants có thể khác `team_name` trong registrations, cần kiểm tra chéo.
- Nếu import nhiều khóa học, mỗi file participants có thể có danh sách khác nhau.

## Hướng Tối Ưu Sau Này
Các hướng có thể quay lại tối ưu khi pipeline v0 đã chạy ổn:

1. Lấy `moodle_user_id` trực tiếp từ Moodle participants API hoặc Moodle database, rồi dùng `moodle_user_id` làm khóa mapping chính.
2. Tạo bảng dimension ổn định như `dim_moodle_users`, chứa `moodle_user_id`, `email`, `full_name`, `registration_id`, `team_name`, `course_id`.
3. Dùng dbt để quản lý các model:

```text
stg_moodle_participants
stg_registrations
int_moodle_user_identity_map
silver_moodle_learning_events
```

4. Thêm kiểm tra chất lượng dữ liệu:

```text
Moodle users không map được email
Email participants không có trong registrations
Tên trùng trong participants
Groups khác team_name
Một Moodle user map ra nhiều email
```

## Quyết Định Tạm Thời
Trong giai đoạn v0, vẫn dùng participants export làm cầu nối danh tính vì đây là cách đáng tin nhất với dữ liệu hiện có.

Không tối ưu sớm bằng cách bỏ bảng participants, vì Moodle log không chứa email. Nếu bỏ participants, dashboard theo team sẽ dễ sai.

