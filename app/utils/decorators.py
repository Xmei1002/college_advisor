import traceback
from functools import wraps
from flask import current_app
from app.utils.response import APIResponse

def api_error_handler(f):
    """捕获API接口异常的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # 记录错误到日志
            current_app.logger.error(
                f"接口异常: {str(e)}", 
                exc_info=True
            )
            # 获取堆栈跟踪信息（仅在开发环境显示）
            error_details = None
            if current_app.config.get('DEBUG', False):
                error_details = traceback.format_exc()
            # 返回统一错误格式
            return APIResponse.error(
                message=f"服务异常: {str(e)}", 
                errors=error_details, 
                code=500
            )
    return decorated