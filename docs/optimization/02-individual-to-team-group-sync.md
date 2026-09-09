# Tối ưu: chuyển thí sinh cá nhân thành nhóm trên Moodle

## Bối cảnh

Hiện tại dashboard phân biệt hai luồng chính:

- Thí sinh theo đội: có `team_name` trong bảng đăng ký và có Moodle group tương ứng.
- Thí sinh cá nhân: chưa có `team_name`, nhưng trong tương lai có thể mời thêm thành viên bên ngoài.

Trong Moodle, nếu một thí sinh cá nhân được thêm vào `Groups`, về mặt vận hành người đó đã bắt đầu có cấu trúc giống một team. Nếu pipeline chỉ dựa vào cấu hình cứng hoặc sửa database thủ công, mỗi lần có cá nhân thêm thành viên sẽ phải vào sâu hệ thống để chỉnh mapping.

## Vấn đề cần tối ưu

Cần thiết kế một cách thuận tiện để:

- Phát hiện thí sinh cá nhân đã có Moodle group mới.
- Đồng bộ group đó về lớp dữ liệu phân tích mà không phải sửa code.
- Cho phép manager xác nhận cá nhân đó đã chuyển thành nhóm hay chưa.
- Giữ lịch sử thay đổi để dashboard không bị đếm sai trước và sau thời điểm chuyển nhóm.

## Hướng xử lý đề xuất sau này

Tạo một bảng cấu hình nghiệp vụ, ví dụ `learning_team_overrides`, để quản lý các trường hợp chuyển đổi:

```text
email
old_participation_type
new_team_name
moodle_group_name
effective_from
approved_by
note
is_active
```

Pipeline Gold khi tính team sẽ ưu tiên:

```text
team_name từ registrations
-> team override đã được duyệt
-> Moodle group name
-> individual
```

## Lý do chưa làm ngay

Hiện tại dashboard v0 cần ổn định trước ở ba lớp:

```text
registered user summary
team summary
individual summary
```

Sau khi dashboard có nhu cầu thực tế về cá nhân thêm thành viên, ta sẽ quay lại thiết kế workflow cập nhật group/override có giao diện quản lý riêng, tránh thao tác thủ công trong DBeaver hoặc code.

