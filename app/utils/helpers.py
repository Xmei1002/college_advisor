import random
import string

def generate_random_string(length=10):
    """生成随机字符串"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def format_datetime(dt):
    """格式化日期时间"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None