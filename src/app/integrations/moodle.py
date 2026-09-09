import httpx
from typing import Optional, Dict, Any
from src.app.core.config import settings

class MoodleClient:
    def __init__(self):
        self.base_url = settings.moodle_base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/webservice/rest/server.php"
        self.token = settings.moodle_token
        self.role_id = int(settings.moodle_default_role_id) if settings.moodle_default_role_id else 5
        self.default_params = {
            "wstoken": self.token,
            "moodlewsrestformat": "json"
        }

    def _post(self, wsfunction: str, data: Dict[str, Any]) -> Any:
        params = self.default_params.copy()
        params["wsfunction"] = wsfunction
        
        # Tăng timeout lên 60 giây vì Moodle có thể mất nhiều thời gian để gửi Email khi tạo User
        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.endpoint, params=params, data=data)
            response.raise_for_status()
            result = response.json()
            
            # API của Moodle thường trả về dict chứa key "exception" nếu có lỗi nội bộ
            if isinstance(result, dict) and "exception" in result:
                debug_info = result.get('debuginfo', '')
                raise Exception(f"Lỗi từ Moodle API ({wsfunction}): {result.get('message')} - {debug_info}")
                
            return result

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """
        Tìm kiếm user trên Moodle dựa vào username.
        Trả về dict thông tin user nếu tìm thấy, hoặc None nếu không tồn tại.
        """
        data = {
            "criteria[0][key]": "username",
            "criteria[0][value]": username
        }
        result = self._post("core_user_get_users", data)
        
        users = result.get("users", [])
        if users:
            return users[0]
        return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Tìm kiếm user trên Moodle dựa vào email.
        """
        data = {
            "criteria[0][key]": "email",
            "criteria[0][value]": email
        }
        result = self._post("core_user_get_users", data)
        
        users = result.get("users", [])
        if users:
            return users[0]
        return None

    def create_user(self, username: str, first_name: str, last_name: str, email: str, student_id: str = "") -> dict:
        """
        Tạo user mới trên Moodle. 
        Sử dụng mật khẩu mặc định và bắt buộc đổi mật khẩu ở lần đăng nhập đầu tiên.
        """
        data = {
            "users[0][username]": username,
            "users[0][password]": "Sandbox@2026",
            "users[0][firstname]": first_name,
            "users[0][lastname]": last_name,
            "users[0][email]": email,
            "users[0][preferences][0][type]": "auth_forcepasswordchange",
            "users[0][preferences][0][value]": 1,
        }
        
        if student_id:
            data["users[0][idnumber]"] = student_id
            
        result = self._post("core_user_create_users", data)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        raise Exception(f"Không thể tạo user {username}. Kết quả trả về: {result}")

    def enroll_user(self, user_id: int, course_id: int) -> bool:
        """
        Ghi danh một user vào một khóa học bằng role Học viên (Student).
        """
        data = {
            "enrolments[0][roleid]": self.role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id
        }
        # Hàm này thường trả về null/empty nếu thành công
        self._post("enrol_manual_enrol_users", data)
        return True

    def get_course_groups(self, course_id: int) -> list:
        """
        Lấy danh sách các groups trong khóa học.
        Trả về list of dicts.
        """
        data = {
            "courseid": course_id
        }
        result = self._post("core_group_get_course_groups", data)
        if isinstance(result, list):
            return result
        return []

    def create_group(self, course_id: int, name: str, description: str = "") -> dict:
        """
        Tạo group mới trong khóa học.
        """
        data = {
            "groups[0][courseid]": course_id,
            "groups[0][name]": name,
            "groups[0][description]": description
        }
        result = self._post("core_group_create_groups", data)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        raise Exception(f"Không thể tạo group {name}.")

    def add_user_to_group(self, group_id: int, user_id: int) -> bool:
        """
        Thêm user vào group.
        """
        data = {
            "members[0][groupid]": group_id,
            "members[0][userid]": user_id
        }
        self._post("core_group_add_group_members", data)
        return True

moodle_client = MoodleClient()
