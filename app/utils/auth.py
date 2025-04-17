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
            # 添加详细日志
            current_app.logger.info(f"JWT验证开始: 请求路径 {request.path}")
            
            # 检查Authorization头是否存在
            auth_header = request.headers.get('Authorization')
            current_app.logger.info(f"Authorization头: {auth_header}")
            
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            current_app.logger.info(f"JWT验证成功: 用户ID {user_id}")
            
            # 添加用户到请求上下文
            user = User.query.get(user_id)
            if not user:
                current_app.logger.warning(f"JWT验证失败：用户ID {user_id} 不存在")
                return APIResponse.error("认证失败：用户不存在", code=401)
            
            current_app.logger.info(f"找到用户: {user.username}, 类型: {user.user_type}")
            
            # 将用户添加到请求上下文
            g.current_user = user
            # 添加用户到请求对象(用于日志)
            request.authenticated_user = user
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.warning(f"JWT验证失败：{str(e)}")
            # 输出更多异常详情
            import traceback
            current_app.logger.error(traceback.format_exc())
            return APIResponse.error("认证失败", code=401)
    
    return wrapper

def admin_required(fn):
    """验证管理员权限"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_app.logger.info(f"管理员权限验证开始: 请求路径 {request.path}")
        
        if not hasattr(g, 'current_user'):
            current_app.logger.warning(f"权限验证失败：g对象没有current_user属性")
            return APIResponse.error("认证失败：未登录", code=401)
            
        if not g.current_user:
            current_app.logger.warning(f"权限验证失败：g.current_user为空")
            return APIResponse.error("认证失败：未登录", code=401)
        
        current_app.logger.info(f"当前用户: {g.current_user.username}, ID: {g.current_user.id}, 类型: {g.current_user.user_type}")
            
        if not g.current_user.is_admin():
            current_app.logger.warning(f"权限验证失败：用户 {g.current_user.id} 非管理员")
            return APIResponse.error("权限不足", code=403)
        
        current_app.logger.info(f"管理员权限验证通过: {g.current_user.username}")
        return fn(*args, **kwargs)
    
    return wrapper

def planner_required(fn):
    """验证规划师权限"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            current_app.logger.warning(f"权限验证失败：未找到当前用户")
            return APIResponse.error("认证失败：未登录", code=401)
            
        if not g.current_user.is_planner():
            current_app.logger.warning(f"权限验证失败：用户 {g.current_user.id} 非规划师")
            return APIResponse.error("权限不足", code=403)
        
        return fn(*args, **kwargs)
    
    return wrapper

def student_required(fn):
    """验证学生权限"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            current_app.logger.warning(f"权限验证失败：未找到当前用户")
            return APIResponse.error("认证失败：未登录", code=401)
            
        if not g.current_user.is_student():
            current_app.logger.warning(f"权限验证失败：用户 {g.current_user.id} 非学生")
            return APIResponse.error("权限不足", code=403)
        
        return fn(*args, **kwargs)
    
    return wrapper
