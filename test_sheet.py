import sys
import os

# Đảm bảo có thể import được các module trong src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.app.services.member_service import process_sheet_url
from src.app.services.validation_service import validate_member_batch
from src.app.services.username_service import generate_base_username

def main():
    test_url = "https://docs.google.com/spreadsheets/d/106Ew1uNSyE1edRJa6iaqGq3mSyuGvFy-Ve333f4IEaY/edit?gid=0#gid=0"
    
    print("🚀 Bắt đầu tải và parse dữ liệu từ Google Sheet...")
    print(f"🔗 URL: {test_url}")
    print("-" * 50)
    
    try:
        # Bước 1: Parse dữ liệu
        members, parse_errors = process_sheet_url(test_url)
        
        # Bước 2: Validate dữ liệu (tìm trùng lặp)
        valid_members, validation_errors = validate_member_batch(members)
        
        print(f"✅ Đã parse thành công {len(members)} thành viên. Trong đó hợp lệ: {len(valid_members)}.")
        
        # In ra các thành viên hợp lệ và Username sinh ra
        for idx, member in enumerate(valid_members, 1):
            username = generate_base_username(member.first_name, member.last_name)
            print(f"  {idx}. {member.full_name}")
            print(f"     Email: {member.email} | MSSV: {member.student_id}")
            print(f"     => Username Moodle dự kiến: [{username}]")
            
        # Gộp tất cả các lỗi lại để in ra
        all_errors = parse_errors + validation_errors
        if all_errors:
            print("\n⚠️  Cảnh báo / Lỗi phát hiện được:")
            for err in all_errors:
                print(f"  - {err}")
                
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    main()
