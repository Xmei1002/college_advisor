# app/api/endpoints/recommendation.py
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.college.recommendation_service import RecommendationService
from flask_smorest import Blueprint
from app.models.user import User
from app.services.student.student_data_service import StudentDataService
from app.core.recommendation.repository import CollegeRepository

# 创建推荐蓝图
recommendation_bp = Blueprint(
    'recommendation', 
    'recommendation',
    description='高校推荐相关接口',
)

from app.api.schemas.recommendation import (
    CategoryFilterSchema, CollegeCategoryResponseSchema,CategoryFilterSchemaByStuedntID
)

# @recommendation_bp.route('/colleges-by-category', methods=['POST'])
# @recommendation_bp.arguments(CategoryFilterSchema)
# @recommendation_bp.response(200, CollegeCategoryResponseSchema)
# @jwt_required()
# @api_error_handler
# def get_colleges_by_category(data):
#     """
#     根据冲稳保类别和志愿段获取院校专业组列表
    
#     按特定类别和志愿段筛选高校专业组，并支持分页查询。
#     支持地区和专业类型多选。
#     """
#     # 获取当前用户并验证权限
#     current_user_id = get_jwt_identity()
#     current_user = User.query.get_or_404(current_user_id)
    
#     # 检查用户类型权限 - 只有规划师可以访问该接口
#     is_planner = current_user.user_type == User.USER_TYPE_PLANNER
#     if not is_planner:
#         return APIResponse.error("无权限访问该接口", code=403)
    
#     # 获取参数
#     student_score = data['score']
#     subject_type = data['subject_type']
#     education_level = data['education_level']
#     category_id = data['category_id']
#     group_id = data['group_id']
#     area_ids = data.get('area_ids', [])  # 多选地区
#     student_subjects = data['student_subjects']
#     specialty_types = data.get('specialty_types', [])  # 多选专业类型
#     mode = data.get('mode', 'smart')
#     page = data.get('page', 1)
#     per_page = data.get('per_page', 20)
#     tese_types = data.get('tese_types', [])
#     leixing_types = data.get('leixing_types', [])
#     teshu_types = data.get('teshu_types', [])

#     # 调用服务
#     college_groups, pagination = RecommendationService.get_colleges_by_category_and_group(
#         student_score=student_score,
#         subject_type=subject_type,
#         education_level=education_level,
#         category_id=category_id,
#         group_id=group_id,
#         student_subjects=student_subjects,
#         area_ids=area_ids,  # 传递多个地区ID
#         specialty_types=specialty_types,  # 传递多个专业类型ID
#         mode=mode,
#         page=page,
#         per_page=per_page,
#         tese_types=tese_types,
#         leixing_types=leixing_types,
#         teshu_types=teshu_types
#     )
    
#     return APIResponse.pagination(
#         items=college_groups,
#         total=pagination['total'],
#         page=pagination['page'],
#         per_page=pagination['per_page'],
#         message="获取成功"
#     )

@recommendation_bp.route('/generate-plan', methods=['POST'])
@recommendation_bp.arguments(CategoryFilterSchemaByStuedntID)
@recommendation_bp.response(200, CollegeCategoryResponseSchema)
@jwt_required()
@api_error_handler
def get_colleges_by_category(data):
    """
    根据学生ID和冲稳保类别获取院校专业组列表
    
    自动提取学生信息，按特定类别和志愿段筛选高校专业组，并支持分页查询。
    支持地区和专业类型多选。
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    student_id =data['student_id']
    # 从参数获取类别和志愿段相关信息
    category_id = data.get('category_id', 1)  # 默认冲
    group_id = data.get('group_id', 1)  # 默认第一组
    mode = data.get('mode', 'smart')
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)
    
    # 从学生ID提取学生信息
    recommendation_data = StudentDataService.extract_college_recommendation_data(student_id)
    # print(recommendation_data)
    # 调用服务
    college_groups, pagination = RecommendationService.get_colleges_by_category_and_group(
        student_score=recommendation_data['student_score'],
        subject_type=recommendation_data['subject_type'],
        education_level=recommendation_data['education_level'],
        category_id=category_id,
        group_id=group_id,
        student_subjects=recommendation_data['student_subjects'],
        area_ids=recommendation_data['area_ids'],
        specialty_types=recommendation_data['specialty_types'],
        mode=mode,
        page=page,
        per_page=per_page
    )
    
    return APIResponse.pagination(
        items=college_groups,
        total=pagination['total'],
        page=pagination['page'],
        per_page=pagination['per_page'],
        message="获取成功"
    )

@recommendation_bp.route('/test/toid', methods=['POST'])
@jwt_required()
@api_error_handler
def begin_recommendation():
    """
    测试接口
    将用户文本信息映射为ID
    """
    recommendation_data = StudentDataService.extract_college_recommendation_data(2)
    return APIResponse.success(recommendation_data, message="成功")


@recommendation_bp.route('/test/totext', methods=['GET'])
@jwt_required()
@api_error_handler
def begin_recommendation():
    """
    测试接口
    将用户所有信息整理为文本
    """
    recommendation_data = StudentDataService.generate_student_profile_text(2)
    return APIResponse.success(recommendation_data, message="成功")

@recommendation_bp.route('/get_specialties/<int:college_group_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def get_specialties(college_group_id):
    """
    获取专业组对应的专业列表
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)

    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    # 调用服务
    specialties = CollegeRepository.get_specialties_by_group_id(college_group_id)
    return APIResponse.success(specialties, message="成功")