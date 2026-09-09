import sys
import os
import logging

# Thiết lập logging để xem chi tiết
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Đảm bảo có thể import được các module trong src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.app.services.member_service import process_sheet_url
from src.app.services.validation_service import validate_member_batch
from src.app.services.moodle_service import sync_member_to_moodle
from src.app.integrations.moodle import moodle_client

def main():
    test_url = "https://docs.google.com/spreadsheets/d/106Ew1uNSyE1edRJa6iaqGq3mSyuGvFy-Ve333f4IEaY/edit?gid=0#gid=0"
    course_id = 12
    
    print("=" * 60)
    print("🚀 BẮT ĐẦU LUỒNG ĐỒNG BỘ DỮ LIỆU LÊN MOODLE (END-TO-END)")
    print(f"🔗 Google Sheet: {test_url}")
    print(f"🎯 Khóa học đích (Course ID): {course_id}")
    print("=" * 60)
    
    # Bước 1 & 2: Parse & Validate
    print("\n[1/3] Đang tải và kiểm tra dữ liệu từ Google Sheet...")
    team_name, members, parse_errors = process_sheet_url(test_url)
    valid_members, validation_errors = validate_member_batch(members)
    
    all_errors = parse_errors + validation_errors
    if all_errors:
        print("⚠️ Có một số dữ liệu không hợp lệ đã bị loại bỏ:")
        for err in all_errors:
            print(f"  - {err}")
            
    if not valid_members:
        print("❌ Không có thành viên nào hợp lệ để đồng bộ.")
        return
        
    print(f"\n[2/3] Dữ liệu hợp lệ: {len(valid_members)} thành viên. Team: '{team_name}'. Chuẩn bị đẩy lên Moodle...")
    
    # Bước 2.5: Tìm hoặc tạo Group trên Moodle
    print(f"\n[+] Đang xử lý Group '{team_name}' trong Khóa {course_id}...")
    groups = moodle_client.get_course_groups(course_id)
    group_id = None
    
    for g in groups:
        if g.get("name") == team_name:
            group_id = g.get("id")
            print(f"   => Group '{team_name}' đã tồn tại (ID: {group_id})")
            break
            
    if not group_id:
        print(f"   => Group '{team_name}' chưa tồn tại. Đang tạo mới...")
        new_group = moodle_client.create_group(course_id, team_name)
        group_id = new_group.get("id")
        print(f"   => Đã tạo Group thành công (ID: {group_id})")
    
    # Bước 3: Đồng bộ lên Moodle
    print("\n[3/3] Bắt đầu đồng bộ User:")
    success_count = 0
    fail_count = 0
    
    for idx, member in enumerate(valid_members, 1):
        print(f"\n⏳ Đang xử lý [{idx}/{len(valid_members)}]: {member.full_name} ({member.email})")
        
        is_success, msg = sync_member_to_moodle(member, course_id, group_id)
        
        if is_success:
            print(f"   ✅ {msg}")
            success_count += 1
        else:
            print(f"   ❌ {msg}")
            fail_count += 1
            
    print("=" * 60)
    print(f"🎉 HOÀN TẤT! Thành công: {success_count} | Thất bại: {fail_count} | Bỏ qua (lỗi data): {len(members) - len(valid_members)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
