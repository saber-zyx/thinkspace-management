from src.app.models.member import Member
from src.app.utils.text_utils import remove_vietnamese_accents, clean_alphanumeric

def generate_base_username(first_name: str, last_name: str) -> str:
    """
    Tạo username cơ bản từ tên và họ.
    Quy tắc: Tên + [Chữ cái đầu của từng chữ trong Họ và Tên Đệm]
    Ví dụ: 
    - first="Trường", last="Võ Thiên" -> "truong" + "v" + "t" = "truongvt"
    - first="Anh", last="Nguyễn Thị" -> "anhnt"
    """
    # 1. Bỏ dấu tiếng Việt và chuyển sang chữ thường
    first_clean = clean_alphanumeric(remove_vietnamese_accents(first_name)).lower().strip()
    last_clean = clean_alphanumeric(remove_vietnamese_accents(last_name)).lower().strip()
    
    # 2. Lấy toàn bộ tên chính (first_name), xóa dấu cách nếu tên chính có nhiều chữ
    base = first_clean.replace(" ", "")
    
    # 3. Lấy chữ cái đầu tiên của từng từ trong họ và tên đệm
    last_words = last_clean.split()
    initials = "".join([word[0] for word in last_words if word])
    
    username = base + initials
    return username

def get_unique_username(base_username: str, existing_usernames: set[str]) -> str:
    """
    Kiểm tra và gắn thêm số vào cuối username nếu bị trùng lặp (collision).
    Ví dụ: truongvt, truongvt2, truongvt3
    """
    if base_username not in existing_usernames:
        return base_username
        
    counter = 2
    while f"{base_username}{counter}" in existing_usernames:
        counter += 1
        
    return f"{base_username}{counter}"
