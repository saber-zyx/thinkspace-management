import unicodedata
import re


TEAM_NAME_ALIASES = {
    "diep thanh bang": "DIỆP THANH BÀNG",
    "diêp thanh bàng": "DIỆP THANH BÀNG",
    "stabily - thiết bị đeo ổn định chuyển động tay cho người mắc parkinson": (
        "STABILY - Thiết bị đeo ổn định chuyển động tay cho người mắc Parkinson"
    ),
}


def remove_vietnamese_accents(text: str) -> str:
    """
    Loại bỏ dấu tiếng Việt khỏi chuỗi.
    Ví dụ: 'Võ Thiên Trường' -> 'Vo Thien Truong'
    """
    # Xử lý các ký tự đặc biệt của tiếng Việt (đ, Đ) không nằm trong bảng mã chuẩn Unicode NFD
    text = text.replace('đ', 'd').replace('Đ', 'D')
    
    # Chuẩn hóa về dạng phân tách ký tự và dấu (NFD), sau đó loại bỏ các ký tự dấu
    normalized = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in normalized if not unicodedata.combining(c))
    
    return stripped

def clean_alphanumeric(text: str) -> str:
    """
    Chỉ giữ lại chữ cái và số, xóa các ký tự đặc biệt.
    """
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)


def collapse_spaces(value: object) -> str:
    """Chuẩn hóa khoảng trắng để các nguồn dữ liệu so sánh ổn định hơn."""
    return " ".join(str(value or "").split())


def normalized_text_key(value: object) -> str | None:
    """Tạo khóa so sánh không phân biệt chữ hoa/thường và khoảng trắng."""
    cleaned = collapse_spaces(value)
    if not cleaned:
        return None
    return cleaned.lower()


def normalized_team_name(value: object) -> str | None:
    """Chuẩn hóa tên đội trước khi lưu và trước khi tính chỉ số báo cáo."""
    cleaned = collapse_spaces(value)
    if not cleaned:
        return None

    key = normalized_text_key(cleaned)
    return TEAM_NAME_ALIASES.get(key, cleaned)
