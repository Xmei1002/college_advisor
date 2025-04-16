import random
import string
from datetime import timezone
import pytz
def generate_random_string(length=10):
    """生成随机字符串"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def format_datetime(dt):
    """格式化日期时间"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

def convert_utc_to_beijing(utc_datetime):
    """将UTC时间转换为北京时间"""
    if not utc_datetime:
        return ""
    
    # 确保datetime对象有时区信息
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    # 转换到北京时区
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = utc_datetime.astimezone(beijing_tz)
    
    # 格式化为字符串（可根据需要调整格式）
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S')