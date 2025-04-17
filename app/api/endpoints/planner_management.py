# app/api/endpoints/planner_management.py
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.user import User
from app.models.planner_info import PlannerInfo
from flask_smorest import Blueprint
from app.utils.auth import admin_required
from app.extensions import db
from app.core.auth.service import AuthService
from flask import current_app
from datetime import datetime, timezone
from sqlalchemy import func
from app.api.schemas import PaginationQuerySchema
from app.api.schemas.planner_management import (
    CreatePlannerManagementSchema,
    UpdatePlannerManagementSchema,
    PlannerResponseSchema,
    PlannerListResponseSchema
)

# 创建规划师管理蓝图
planner_management_bp = Blueprint(
    'planner_management', 
    'planner_management',
    description='规划师账号管理接口',
)

@planner_management_bp.route('/list', methods=['GET'])
@planner_management_bp.arguments(PaginationQuerySchema, location='query')
@planner_management_bp.response(200, PlannerListResponseSchema)
@api_error_handler
@jwt_required()
def list_planners(query_args):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
        
    page = query_args.get('page', 1)
    per_page = query_args.get('per_page', 10)
    keyword = query_args.get('keyword', '')  # 修改这里，使用keyword而不是search
    
    # 构建查询
    query = User.query.filter_by(user_type=User.USER_TYPE_PLANNER)
    
    # 如果有搜索关键词，添加过滤条件
    if keyword:
        query = query.filter(User.username.ilike(f'%{keyword}%'))
    
    # 获取分页结果
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 构建响应数据，直接使用 to_dict 方法
    items = [planner.to_dict() for planner in pagination.items]
    
    return APIResponse.success(
        data={
            'items': items,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page
            }
        },
        message="获取规划师列表成功"
    )

@planner_management_bp.route('/<int:planner_id>', methods=['GET'])
@planner_management_bp.response(200, PlannerResponseSchema)
@api_error_handler
@jwt_required()
def get_planner(planner_id):
    """
    获取规划师详情
    
    获取指定规划师的详细信息（需要管理员权限）
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    # 查询规划师
    planner = User.query.filter_by(id=planner_id, user_type=User.USER_TYPE_PLANNER).first_or_404()
    
    # 统计学生数量
    student_count = User.query.filter_by(planner_id=planner.id, user_type=User.USER_TYPE_STUDENT).count()
    
    # 构建响应数据
    planner_dict = planner.to_dict()
    planner_dict['student_count'] = student_count
    
    # 添加规划师详细信息
    if hasattr(planner, 'planner_info') and planner.planner_info:
        planner_dict['planner_info'] = planner.planner_info.to_dict()
    
    return APIResponse.success(
        data=planner_dict,
        message="获取规划师详情成功"
    )

@planner_management_bp.route('/create', methods=['POST'])
@planner_management_bp.arguments(CreatePlannerManagementSchema)
@planner_management_bp.response(200, PlannerResponseSchema)
@api_error_handler
@jwt_required()
def create_planner(data):
    """
    创建规划师账号
    
    创建一个新的规划师账号（需要管理员权限）
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    username = data['username']
    password = data['password']
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return APIResponse.error("该用户名已存在", code=400)
    
    try:
        # 创建规划师账号
        planner = AuthService.create_planner(username, password)
        
        # 保存用户基本信息
        db.session.flush()  # 确保user_id已生成
        
        # 创建规划师详细信息记录
        planner_info = PlannerInfo(
            user_id=planner.id,
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )
        db.session.add(planner_info)
        db.session.commit()
        
        # 重新查询以获取完整信息
        planner = User.query.get(planner.id)
        planner_dict = planner.to_dict()
        if hasattr(planner, 'planner_info') and planner.planner_info:
            planner_dict['planner_info'] = planner.planner_info.to_dict()
        
        return APIResponse.success(
            data=planner_dict,
            message="规划师账号创建成功"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建规划师账号失败: {str(e)}")
        return APIResponse.error(f"创建失败: {str(e)}", code=400)

@planner_management_bp.route('/<int:planner_id>', methods=['PUT'])
@planner_management_bp.arguments(UpdatePlannerManagementSchema)
@planner_management_bp.response(200, PlannerResponseSchema)
@api_error_handler
@jwt_required()
def update_planner(data, planner_id):
    """
    更新规划师账号
    
    更新指定规划师的账号信息（需要管理员权限）
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    # 查询规划师
    planner = User.query.filter_by(id=planner_id, user_type=User.USER_TYPE_PLANNER).first_or_404()
    
    try:
        # 更新用户名（需要确保唯一性）
        if 'username' in data and data['username'] and data['username'] != planner.username:
            if User.query.filter_by(username=data['username']).first():
                return APIResponse.error("该用户名已存在", code=400)
            planner.username = data['username']
        
        # 更新密码
        if 'password' in data and data['password']:
            planner.password = data['password']
        
        
        planner.updated_at = datetime.now(timezone.utc)
        
        # 更新或创建规划师详细信息
        planner_info = planner.planner_info
        if not planner_info:
            planner_info = PlannerInfo(user_id=planner.id)
            db.session.add(planner_info)
        
        if 'phone' in data and data['phone'] is not None:
            planner_info.phone = data['phone']
        if 'address' in data and data['address'] is not None:
            planner_info.address = data['address']
        
        db.session.commit()
        
        # 重新查询获取完整信息
        planner = User.query.get(planner.id)
        planner_dict = planner.to_dict()
        if hasattr(planner, 'planner_info') and planner.planner_info:
            planner_dict['planner_info'] = planner.planner_info.to_dict()
        planner_dict['student_count'] = User.query.filter_by(planner_id=planner.id, user_type=User.USER_TYPE_STUDENT).count()
        
        return APIResponse.success(
            data=planner_dict,
            message="规划师信息更新成功"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新规划师信息失败: {str(e)}")
        return APIResponse.error(f"更新失败: {str(e)}", code=400)

@planner_management_bp.route('/<int:planner_id>', methods=['DELETE'])
@planner_management_bp.response(200)
@api_error_handler
@jwt_required()
def delete_planner(planner_id):
    """
    删除规划师账号
    
    删除指定的规划师账号（需要管理员权限）
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    # 查询规划师
    planner = User.query.filter_by(id=planner_id, user_type=User.USER_TYPE_PLANNER).first_or_404()
    
    # 检查是否有关联的学生
    student_count = User.query.filter_by(planner_id=planner.id).count()
    if student_count > 0:
        return APIResponse.error("该规划师有关联的学生，无法删除", code=400)
    
    try:
        # 先删除规划师的详细信息
        if hasattr(planner, 'planner_info') and planner.planner_info:
            db.session.delete(planner.planner_info)
        
        # 然后删除规划师用户
        db.session.delete(planner)
        db.session.commit()
        return APIResponse.success(message="规划师账号删除成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除规划师失败: {str(e)}")
        return APIResponse.error(f"删除失败: {str(e)}", code=400)
