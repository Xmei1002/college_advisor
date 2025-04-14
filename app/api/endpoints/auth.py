# app/api/endpoints/auth.py
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity,create_access_token
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.core.auth.service import AuthService
from app.core.auth.verification import VerificationService
from app.models.user import User
from flask_smorest import Blueprint
from app.utils.decorators import api_error_handler

# 创建认证蓝图
auth_bp = Blueprint(
    'auth', 
    'auth',
    description='用户认证与账号管理相关接口',
)

from app.api.schemas import (
    SendVerificationSchema, VerifyCodeSchema, StudentRegisterSchema,
    LoginSchema, CreatePlannerSchema, AuthResponseSchema, UserSchema
)

@auth_bp.route('/send-verification', methods=['POST'])
@auth_bp.arguments(SendVerificationSchema)
@auth_bp.response(200)
@api_error_handler
def send_verification(data):
    """
    发送手机验证码
    
    向指定手机号发送注册验证码
    """
    phone = data['phone']
    
    # 检查手机号是否已注册
    # user = User.query.filter_by(username=phone).first()
    # if user:
    #     return APIResponse.error("该手机号已注册", code=400)
    
    # 生成并发送验证码
    code = VerificationService.generate_code()
    VerificationService.save_code(phone, code)
    VerificationService.send_sms(phone, code)
    
    return APIResponse.success(message="验证码发送成功")

@auth_bp.route('/verify-code', methods=['POST'])
@auth_bp.arguments(VerifyCodeSchema)
@auth_bp.response(200, AuthResponseSchema)
@api_error_handler
def verify_code(data):
    """验证手机验证码并登录/注册"""
    phone = data['phone']
    code = data['code']
    planner_id = data['planner_id']
    
    # 验证规划师ID是否存在且有效
    planner = User.query.get(planner_id)
    if not planner:
        return APIResponse.error("规划师不存在", code=404)
    
    if not planner.is_planner():
        return APIResponse.error("指定的用户不是规划师", code=400)
    
    # 验证验证码
    is_valid = VerificationService.verify_code(phone, code)
    if not is_valid:
        return APIResponse.error("验证码错误或已过期", code=400)
    
    # 检查用户是否存在
    user = User.query.filter_by(username=phone).first()
    
    # 用户不存在，创建新用户（注册）
    if not user:
        consultation_status = User.CONSULTATION_STATUS_PENDING  # 默认咨询状态为待定
        user = AuthService.register_student(phone, '123456',consultation_status)
        # 为新用户分配规划师
        user.assign_planner(planner)
        registration_message = "注册并登录成功"
    else:
        # 用户存在，检查状态
        if user.status != User.USER_STATUS_ACTIVE:
            return APIResponse.error("账号已被禁用，请联系管理员", code=403)
        
        # 为现有用户分配或更新规划师
        user.assign_planner(planner)
        registration_message = "登录成功"
    
    # 更新登录信息
    user.update_login_info(request.remote_addr)
    
    # 生成令牌
    tokens = AuthService.generate_tokens(user)
    
    return APIResponse.success(
        data=tokens,
        message=registration_message
    )

@auth_bp.route('/register', methods=['POST'])
@auth_bp.arguments(StudentRegisterSchema)
@auth_bp.response(200, AuthResponseSchema)
@api_error_handler
def register(data):
    """
    学生用户注册
    
    创建新的学生用户账号
    """
    username = data['username']  # 手机号作为用户名
    password = data['password']
    verification_code = data['verification_code']
    
    # 检查手机号是否已注册
    user = User.query.filter_by(username=username).first()
    if user:
        return APIResponse.error("该用户名已被注册", code=400)
    
    # 验证验证码
    is_valid = VerificationService.verify_code(username, verification_code)
    if not is_valid:
        return APIResponse.error("验证码错误或已过期", code=400)
    
    # 创建新用户
    user = AuthService.register_student(username, password)
    
    # 更新登录信息
    user.update_login_info(request.remote_addr)
    
    # 生成令牌
    tokens = AuthService.generate_tokens(user)
    
    return APIResponse.success(
        data=tokens,
        message="注册成功",
        code=200
    )

@auth_bp.route('/login', methods=['POST'])
@auth_bp.arguments(LoginSchema)
@auth_bp.response(200, AuthResponseSchema)
@api_error_handler
def login(data):
    """
    用户登录
    
    学生和规划师通用的登录接口
    """
    username = data['username']
    password = data['password']
    
    user = AuthService.authenticate(username, password)
    if not user:
        return APIResponse.error("用户名或密码错误", code=401)
    
    # 检查账号状态
    if user.status != User.USER_STATUS_ACTIVE:
        return APIResponse.error("账号已被禁用，请联系管理员", code=403)
    
    # 更新登录信息
    user.update_login_info(request.remote_addr)
    
    # 生成令牌
    tokens = AuthService.generate_tokens(user)
    
    return APIResponse.success(
        data=tokens,
        message="登录成功"
    )

@auth_bp.route('/planner', methods=['POST'])
@auth_bp.arguments(CreatePlannerSchema)
@auth_bp.response(200, AuthResponseSchema)
# @jwt_required()
@api_error_handler
def create_planner(data):
    """
    创建规划师账号
    
    管理员创建规划师账号（需要管理员权限）
    """
    # 获取当前用户并验证权限
    # current_user_id = get_jwt_identity()
    # current_user = User.query.get_or_404(current_user_id)
    
    # # 检查是否有管理员权限（这里简化为是否为规划师，实际中可能需要更复杂的权限系统）
    # if not current_user.is_planner():
    #     return APIResponse.error("权限不足", code=403)
    
    username = data['username']
    password = data['password']
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return APIResponse.error("该用户名已存在", code=400)
    
    # 创建规划师账号
    user = AuthService.create_planner(username, password)
    
    # 生成令牌
    tokens = AuthService.generate_tokens(user)
    
    return APIResponse.success(
        data=tokens,
        message="规划师账号创建成功",
        code=200
    )

@auth_bp.route('/me', methods=['GET'])
@auth_bp.response(200, UserSchema)
@jwt_required()
@api_error_handler
def get_current_user():
    """
    获取当前用户信息
    
    返回当前登录用户的详细信息
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    return APIResponse.success(
        data=user.to_dict(),
        message="获取成功"
    )


@auth_bp.route('/refresh', methods=['POST'])
@auth_bp.response(200, AuthResponseSchema)
@jwt_required(refresh=True)  # 指定这是一个刷新令牌端点
@api_error_handler
def refresh_token():
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 创建新的访问令牌
    access_token = create_access_token(identity=str(user.id))
    
    return APIResponse.success(
        data={
            'access_token': access_token,
            'user': user.to_dict()
        },
        message="令牌刷新成功"
    )