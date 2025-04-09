# app/api/endpoints/recommendation.py
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.college.recommendation_service import RecommendationService
from flask_smorest import Blueprint
from app.models.user import User
from app.services.student.student_data_service import StudentDataService
from app.core.recommendation.repository import CollegeRepository
from app.models.student_volunteer_plan import VolunteerCollege,StudentVolunteerPlan,VolunteerSpecialty
from flask import request
# 创建推荐蓝图
recommendation_bp = Blueprint(
    'recommendation', 
    'recommendation',
    description='高校推荐相关接口',
)

from app.api.schemas.recommendation import (
    CategoryFilterSchema, CollegeCategoryResponseSchema,CategoryFilterSchemaByStuedntID, SpecialtiesRequestSchema
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
    支持地区和专业类型多选，返回所有院校并标记已选择状态。
    结果按volunteer_index排序，已选择的院校排在前面。
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    student_id = data['student_id']
    # 从参数获取类别和志愿段相关信息
    category_id = data.get('category_id', 1)  # 默认冲
    group_id = data.get('group_id', 1)  # 默认第一组
    mode = data.get('mode', 'smart')
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)
    
    # 查找学生当前的志愿方案
    current_plan = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        is_current=True
    ).first()
    
    # 获取已选择的院校专业组ID及其对应的volunteer_index和volunteer_college_id
    selected_college_map = {}
    volunteer_college_ids = []
    if current_plan:
        # 获取当前志愿方案中的所有院校
        selected_colleges = VolunteerCollege.query.filter_by(plan_id=current_plan.id).all()
        # 创建院校专业组ID到volunteer_index的映射
        for college in selected_colleges:
            selected_college_map[college.college_group_id] = {
                'volunteer_index': college.volunteer_index,
                'volunteer_college_id': college.id  # 保存VolunteerCollege表中的id
            }
            volunteer_college_ids.append(college.id)
    
    # 获取所有已选择院校的专业信息
    selected_specialties_map = {}
    if volunteer_college_ids:
        selected_specialties = VolunteerSpecialty.query.filter(
            VolunteerSpecialty.volunteer_college_id.in_(volunteer_college_ids)
        ).all()
        
        # 按volunteer_college_id分组存储专业选择信息
        for specialty in selected_specialties:
            if specialty.volunteer_college_id not in selected_specialties_map:
                selected_specialties_map[specialty.volunteer_college_id] = {}
            
            # 存储专业ID到选择信息的映射
            selected_specialties_map[specialty.volunteer_college_id][specialty.specialty_id] = {
                'is_selected': True,
                'specialty_index': specialty.specialty_index
            }
    
    # 从学生ID提取学生信息
    recommendation_data = StudentDataService.extract_college_recommendation_data(student_id)
    
    # 调用服务获取推荐院校，不再传入exclude_group_ids参数
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
        per_page=per_page,
        tese_types=recommendation_data.get('tese_types'),
        leixing_types=recommendation_data.get('leixing_types'),
        teshu_types=recommendation_data.get('teshu_types'),
        tuition_ranges=recommendation_data.get('tuition_ranges'),
        # 不传入exclude_group_ids参数，获取所有符合条件的院校
    )
    
    # 为每个院校专业组添加标记字段
    for group in college_groups:
        if group['cgid'] in selected_college_map:
            group['is_selected'] = True
            group['volunteer_index'] = selected_college_map[group['cgid']]['volunteer_index']
            group['volunteer_college_id'] = selected_college_map[group['cgid']]['volunteer_college_id']
            
            # 获取该院校的专业选择映射
            volunteer_college_id = group['volunteer_college_id']
            specialty_map = selected_specialties_map.get(volunteer_college_id, {})
            
            # 标记该院校的专业列表
            for specialty in group['specialties']:
                if specialty['spid'] in specialty_map:
                    specialty['is_selected'] = True
                    specialty['specialty_index'] = specialty_map[specialty['spid']]['specialty_index']
                else:
                    specialty['is_selected'] = False
                    specialty['specialty_index'] = None
        else:
            group['is_selected'] = False
            group['volunteer_index'] = None
            group['volunteer_college_id'] = None
            
            # 未选择的院校，所有专业都标记为未选择
            for specialty in group['specialties']:
                specialty['is_selected'] = False
                specialty['specialty_index'] = None
    
    # 先按原始逻辑排序（按score_diff降序）
    college_groups = sorted(college_groups, key=lambda x: x['score_diff'], reverse=True)
    
    # 再按是否选择和volunteer_index排序（已选择的排前面）
    sorted_college_groups = sorted(college_groups, key=lambda x: (
        x['volunteer_index'] is None,  # 首先按是否有volunteer_index排序（False排在True前面）
        x['volunteer_index'] if x['volunteer_index'] is not None else float('inf')  # 然后按volunteer_index排序
    ))
    
    return APIResponse.pagination(
        items=sorted_college_groups,
        total=pagination['total'],
        page=pagination['page'],
        per_page=pagination['per_page'],
        message="获取院校列表成功"
    )

# @recommendation_bp.route('/test/toid', methods=['POST'])
# @jwt_required()
# @api_error_handler
# def begin_recommendation():
#     """
#     测试接口
#     将用户文本信息映射为ID
#     """
#     recommendation_data = StudentDataService.extract_college_recommendation_data(2)
#     return APIResponse.success(recommendation_data, message="成功")


# @recommendation_bp.route('/test/totext', methods=['GET'])
# @jwt_required()
# @api_error_handler
# def begin_recommendation():
#     """
#     测试接口
#     将用户所有信息整理为文本
#     """
#     recommendation_data = StudentDataService.generate_student_profile_text(2)
#     return APIResponse.success(recommendation_data, message="成功")


@recommendation_bp.route('/get_specialties', methods=['GET'])
@recommendation_bp.arguments(SpecialtiesRequestSchema, location="query")
@jwt_required()
@api_error_handler
def get_specialties(args):
    """
    获取专业组对应的专业列表，并标记已选择的专业和序号
    结果按specialty_index排序，已选择的专业排在前面。
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)

    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取志愿院校ID
    volunteer_college_id = args.get('volunteer_college_id')
    college_group_id = args.get('college_group_id')
    # 首先获取专业列表
    specialties = CollegeRepository.get_specialties_by_group_id(college_group_id)
    
    # 如果提供了志愿院校ID，标记已选择的专业
    if volunteer_college_id:
        # 查询与该volunteer_college_id相关的所有专业
        selected_specialties = VolunteerSpecialty.query.filter_by(
            volunteer_college_id=volunteer_college_id
        ).all()

        # 创建映射：专业ID -> {is_selected, specialty_index}
        specialty_map = {}
        for specialty in selected_specialties:
            specialty_map[specialty.specialty_id] = {
                'is_selected': True,
                'specialty_index': specialty.specialty_index
            }
       
        # 标记已选择的专业及其序号
        for specialty in specialties:
            if specialty['specialty_id'] in specialty_map:
                specialty['is_selected'] = True
                specialty['specialty_index'] = specialty_map[specialty['specialty_id']]['specialty_index']
            else:
                specialty['is_selected'] = False
                specialty['specialty_index'] = None
    else:
        # 如果没有提供志愿院校ID，所有专业都标记为未选择
        for specialty in specialties:
            specialty['is_selected'] = False
            specialty['specialty_index'] = None
    
    # 按specialty_index排序，已选择的专业排在前面，未选择的按原顺序排在后面
    sorted_specialties = sorted(specialties, key=lambda x: (x['specialty_index'] is None, x['specialty_index'] or float('inf')))
    
    return APIResponse.success(sorted_specialties, message="成功")