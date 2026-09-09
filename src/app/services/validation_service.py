from typing import List, Tuple, Dict
from src.app.models.member import Member

def validate_member_batch(members: List[Member]) -> Tuple[List[Member], List[str]]:
    """
    Kiểm tra tính hợp lệ của một danh sách Member trước khi đưa lên Moodle.
    Kiểm tra:
    1. Trùng lặp email trong cùng batch.
    2. Trùng lặp MSSV trong cùng batch.
    
    Trả về:
    - Danh sách các Member hợp lệ.
    - Danh sách các lỗi phát hiện được.
    """
    valid_members = []
    errors = []
    
    seen_emails: Dict[str, Member] = {}
    seen_student_ids: Dict[str, Member] = {}
    
    for member in members:
        is_valid = True
        
        # 1. Kiểm tra trùng lặp Email
        email_lower = member.email.lower()
        if email_lower in seen_emails:
            errors.append(f"Trùng lặp Email trong file: '{member.email}' giữa {member.full_name} và {seen_emails[email_lower].full_name}")
            is_valid = False
        else:
            seen_emails[email_lower] = member
            
        # 2. Kiểm tra trùng lặp MSSV (nếu có cung cấp MSSV)
        if member.student_id:
            student_id = member.student_id.strip()
            if student_id in seen_student_ids:
                errors.append(f"Trùng lặp MSSV trong file: '{student_id}' giữa {member.full_name} và {seen_student_ids[student_id].full_name}")
                is_valid = False
            else:
                seen_student_ids[student_id] = member
                
        # 3. Có thể thêm các rule nghiệp vụ khác ở đây
        # Ví dụ: MSSV phải có độ dài nhất định, hoặc email phải có đuôi @st.ueh.edu.vn...
        
        if is_valid:
            valid_members.append(member)
            
    return valid_members, errors
