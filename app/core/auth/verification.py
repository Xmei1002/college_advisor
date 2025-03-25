# app/core/auth/verification.py
import random
import redis
from flask import current_app
from datetime import timedelta

class VerificationService:
    """验证码服务"""
    
    # Redis键前缀
    CODE_PREFIX = "verification_code:"
    
    @staticmethod
    def generate_code():
        """生成6位随机验证码"""
        return ''.join(random.choices('0123456789', k=6))
    
    @staticmethod
    def save_code(phone, code, expire_minutes=5):
        """将验证码保存到Redis，并设置过期时间"""
        redis_client = redis.Redis.from_url(current_app.config['CELERY_BROKER_URL'])
        key = f"{VerificationService.CODE_PREFIX}{phone}"
        redis_client.set(key, code)
        redis_client.expire(key, timedelta(minutes=expire_minutes))
    
    @staticmethod
    def verify_code(phone, code):
        """验证手机号码与验证码是否匹配"""
        redis_client = redis.Redis.from_url(current_app.config['CELERY_BROKER_URL'])
        key = f"{VerificationService.CODE_PREFIX}{phone}"
        saved_code = redis_client.get(key)
        
        if not saved_code:
            return False
        
        # 验证成功后删除验证码，防止重复使用
        if saved_code.decode() == code:
            redis_client.delete(key)
            return True
        
        return False
    
    @staticmethod
    def send_sms(phone, code):
        """发送短信验证码（模拟）"""
        # 实际项目中这里会调用短信服务API
        current_app.logger.info(f"向 {phone} 发送验证码: {code}")
        # 调用短信服务API的代码
        return True