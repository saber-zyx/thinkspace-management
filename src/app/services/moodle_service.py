import logging
from typing import Optional, Tuple
from src.app.models.member import Member
from src.app.services.username_service import generate_base_username
from src.app.integrations.moodle import moodle_client

logger = logging.getLogger(__name__)

def sync_member_to_moodle(member: Member, course_id: Optional[int] = None, group_id: Optional[int] = None) -> Tuple[bool, str, dict]:
    """
    Đồng bộ một Member lên Moodle.
    Luồng (Idempotent):
    1. Kiểm tra tồn tại bằng Email.
    2. Nếu chưa có, xử lý username collision (nếu username đã bị chiếm).
    3. Tạo user mới (mật khẩu mặc định).
    4. Ghi danh khóa học (nếu có).
    5. Thêm vào Group (nếu có).
    
    Trả về Tuple (Thành_công_hay_không, Thông_báo_chi_tiết, dict_chứa_meta_data)
    """
    try:
        # 1. Kiểm tra user tồn tại bằng Email (Khóa chính)
        existing_user = moodle_client.get_user_by_email(member.email)
        moodle_user_id = None
        username = ""
        is_new = False
        
        if existing_user:
            moodle_user_id = existing_user["id"]
            username = existing_user["username"]
            logger.info(f"User {member.email} đã tồn tại với username '{username}' (ID {moodle_user_id}).")
        else:
            # 2. Xử lý Username Collision
            base_username = generate_base_username(member.first_name, member.last_name)
            username = base_username
            counter = 2
            
            # Lặp kiểm tra xem username đã có ai dùng chưa
            while moodle_client.get_user_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1
                
            # 3. Tạo user mới
            logger.info(f"Tạo mới user: {username} ({member.email})")
            new_user = moodle_client.create_user(
                username=username,
                first_name=member.first_name,
                last_name=member.last_name,
                email=member.email,
                student_id=member.student_id or ""
            )
            moodle_user_id = new_user["id"]
            is_new = True
            
        # 4. Ghi danh và phân Group (Nếu có course_id)
        user_meta = {"username": username, "is_new": is_new}
        if course_id and moodle_user_id:
            logger.info(f"Ghi danh user ID {moodle_user_id} vào khóa học {course_id}")
            moodle_client.enroll_user(moodle_user_id, course_id)
            
            if group_id:
                logger.info(f"Thêm user ID {moodle_user_id} vào group {group_id}")
                moodle_client.add_user_to_group(group_id, moodle_user_id)
                return True, f"Thành công: Đã xử lý User '{username}', ghi danh khóa {course_id}, vào nhóm {group_id}.", user_meta
            
            return True, f"Thành công: Đã xử lý User '{username}' và ghi danh vào khóa {course_id}.", user_meta
            
        return True, f"Thành công: Đã tạo/Tìm thấy User '{username}' trên hệ thống.", user_meta
        
    except Exception as e:
        logger.error(f"Lỗi đồng bộ Moodle cho {member.full_name}: {str(e)}")
        return False, f"Thất bại: {str(e)}", {}
