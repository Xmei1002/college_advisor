# app/api/endpoints/institution.py (更新)
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.institution.institution_service import InstitutionService
from flask_smorest import Blueprint
from app.api.schemas.institution import (
    CreateInstitutionSchema, UpdateInstitutionSchema, 
    InstitutionResponseSchema, InstitutionQuerySchema,
    InstitutionListResponseSchema
)
from app.models.user import User

institution_bp = Blueprint(
    'institution', 
    'institution',
    description='机构管理相关接口'
)

@institution_bp.route('/create', methods=['POST'])
@institution_bp.arguments(CreateInstitutionSchema, location="form")
@institution_bp.response(200, InstitutionResponseSchema)
@jwt_required()
@api_error_handler
def create_institution(schema_args):
    """
    创建机构
    
    创建新的机构信息
    """
    # 检查权限 (假设只有管理员可以创建机构)
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    logo_file = request.files.get('logo_path')
    qrcode_file = request.files.get('qrcode_path')
    print("logo_file", logo_file)
    print("qrcode_file", qrcode_file)
    institution = InstitutionService.create_institution(schema_args, logo_file, qrcode_file)
    
    return APIResponse.success(
        data=institution.to_dict(),
        message="机构创建成功",
        code=200
    )

@institution_bp.route('/<int:institution_id>', methods=['PUT'])
@institution_bp.arguments(UpdateInstitutionSchema, location="form")
@institution_bp.response(200, InstitutionResponseSchema)
@jwt_required()
@api_error_handler
def update_institution(schema_args, institution_id):
    """
    更新机构
    
    更新指定机构的信息
    """
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    logo_file = request.files.get('logo_path')
    qrcode_file = request.files.get('qrcode_path')
    
    institution = InstitutionService.update_institution(institution_id, schema_args, logo_file, qrcode_file)
    
    return APIResponse.success(
        data=institution.to_dict(),
        message="机构更新成功"
    )

@institution_bp.route('/<int:institution_id>', methods=['GET'])
@institution_bp.response(200, InstitutionResponseSchema)
@jwt_required()
@api_error_handler
def get_institution(institution_id):
    """
    获取机构详情
    
    获取指定机构的详细信息
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    institution = InstitutionService.get_institution(institution_id)
    
    return APIResponse.success(
        data=institution.to_dict(),
        message="获取成功"
    )

@institution_bp.route('/list', methods=['GET'])
@institution_bp.arguments(InstitutionQuerySchema, location="query")
@institution_bp.response(200, InstitutionListResponseSchema)
@jwt_required()
@api_error_handler
def list_institutions(schema_args):
    """
    获取机构列表
    
    获取所有机构的列表，支持分页和筛选
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    page = schema_args.get('page', 1)
    per_page = schema_args.get('per_page', 20)
    name = schema_args.get('name')
    status = schema_args.get('status')
    
    institutions, pagination = InstitutionService.list_institutions(
        page=page, 
        per_page=per_page, 
        name=name,
        status=status
    )
    
    data = [institution.to_dict() for institution in institutions]
    
    return APIResponse.success(
        data={
            'items': data,
            'pagination': {
                'total': pagination['total'],
                'pages': pagination.get('pages', 0),
                'page': pagination['page'],
                'per_page': pagination['per_page']
            }
        },
        message="获取成功"
    )

@institution_bp.route('/<int:institution_id>', methods=['DELETE'])
@institution_bp.response(200)
@jwt_required()
@api_error_handler
def delete_institution(institution_id):
    """
    删除机构
    
    删除指定的机构
    """
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    InstitutionService.delete_institution(institution_id)
    
    return APIResponse.success(
        message="机构删除成功"
    )