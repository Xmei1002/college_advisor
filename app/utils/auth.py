# app/utils/auth.py
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import request, g, current_app
from app.utils.response import APIResponse
from app.models.user import User

def jwt_required(fn):
    """验证JWT令牌"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # 添加用户到请求上下文
            user = User.query.get(user_id)
            if not user:
                current_app.logger.warning(f"JWT验证失败：用户ID {user_id} 不存在")
                return APIResponse.error("认证失败：用户不存在", code=401)
            
            # 将用户添加到请求上下文
            g.current_user = user
            # 添加用户到请求对象(用于日志)
            request.authenticated_user = user
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.warning(f"JWT验证失败：{str(e)}")
            return APIResponse.error("认证失败", code=401)
    
    return wrapper

def admin_required(fn):
    """验证管理员权限"""
    @wraps(fn)
    @jwt_required
    def wrapper(*args, **kwargs):
        if not g.current_user.role == 'planner':
            current_app.logger.warning(f"权限验证失败：用户 {g.current_user.id} 非规划师")
            return APIResponse.error("权限不足", code=403)
        
        return fn(*args, **kwargs)
    
    return wrapper
