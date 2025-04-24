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
    CategoryFilterSchema, CollegeCategoryResponseSchema,CategoryFilterSchemaByStuedntID, SpecialtiesRequestSchema,
    CollegeStatsRequestSchema, CollegeStatsResponseSchema
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
    
    # 获取参数
    student_id = data['student_id']
    category_id = data['category_id']
    group_id = data['group_id']
    mode = data.get('mode', 'smart')
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)
    
    # 查找学生当前的志愿方案
    current_plan = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        is_current=True
    ).first()
    
    # 获取已选择的院校和专业信息
    volunteer_college_ids = []
    selected_colleges_map = {}
    selected_specialties_map = {}
    
    if current_plan:
        # 获取当前志愿方案中的所有院校
        selected_colleges = VolunteerCollege.query.filter_by(
            plan_id=current_plan.id,
            category_id=category_id,
            group_id=group_id
        ).all()
        
        # 按专业组ID和院校ID存储选择信息
        for college in selected_colleges:
            # 存储volunteer_college_id，用于后续查询专业
            volunteer_college_ids.append(college.id)
            
            # 按专业组ID和院校ID存储
            key = (college.college_group_id, college.college_id)
            selected_colleges_map[key] = {
                'is_selected': True,
                'volunteer_college_id': college.id,
                'volunteer_index': college.volunteer_index
            }
    
    # 如果有选择的院校，获取专业选择信息
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
    
    # 调用服务获取推荐院校
    college_groups, pagination = RecommendationService.get_colleges_by_category_and_group(
        student_score = recommendation_data['student_score'] if recommendation_data['student_score'] is not None and recommendation_data['student_score'] > 0 else recommendation_data['mock_exam_score'],
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
        tuition_ranges=recommendation_data.get('tuition_ranges')
    )
        
    # 为每个专业组添加选择状态信息
    for group in college_groups:
        group_key = (group['cgid'], group['cid'])
        group_selection = selected_colleges_map.get(group_key, {'is_selected': False})
        
        # 添加选择状态信息到院校
        group['is_selected'] = group_selection.get('is_selected', False)
        group['volunteer_college_id'] = group_selection.get('volunteer_college_id')
        group['volunteer_index'] = group_selection.get('volunteer_index')
        
        # 为每个专业添加选择状态信息
        if group['is_selected'] and group['volunteer_college_id'] in selected_specialties_map:
            specialties_selection = selected_specialties_map[group['volunteer_college_id']]
            
            for specialty in group['specialties']:
                specialty_id = specialty['spid']
                specialty_selection = specialties_selection.get(specialty_id, {'is_selected': False})
                
                # 添加选择状态信息到专业
                specialty['is_selected'] = specialty_selection.get('is_selected', False)
                specialty['specialty_index'] = specialty_selection.get('specialty_index')
    
    # 根据是否选择和volunteer_index排序：已选择的排在前面，按volunteer_index升序
    college_groups.sort(key=lambda x: (0 if x.get('is_selected') else 1, x.get('volunteer_index', float('inf'))))
    
    return APIResponse.pagination(
        items=college_groups,
        total=pagination['total'],
        page=pagination['page'],
        per_page=pagination['per_page'],
        message="获取成功"
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

@recommendation_bp.route('/college-stats', methods=['POST'])
@recommendation_bp.arguments(CollegeStatsRequestSchema)
@recommendation_bp.response(200, CollegeStatsResponseSchema)
@jwt_required()
@api_error_handler
def get_college_stats(data):
    """
    获取冲稳保各类别及志愿段的院校数量统计
    
    根据学生信息统计各类别和志愿段的院校数量，用于前端展示
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    student_id = data['student_id']
    mode = data.get('mode', 'smart')
    
    # 从学生ID提取学生信息
    recommendation_data = StudentDataService.extract_college_recommendation_data(student_id)
    
    # 导入哈希计算工具和缓存
    from app.extensions import cache
    from app.utils.user_hash import calculate_user_data_hash
    # 获取当前学生数据的哈希值
    current_hash = calculate_user_data_hash(recommendation_data)
    
    # 为该接口使用特定的缓存键，包含哈希值，确保数据变化时自动失效
    cache_key = f"college_stats:{student_id}:{current_hash}"
    
    # 尝试从缓存获取结果
    cached_result = cache.get(cache_key)

    # 如果缓存存在，直接返回缓存结果
    if cached_result:
        return APIResponse.success(cached_result, message="获取院校统计数据成功(缓存)")
    from app.utils.cache_utils import delete_old_cache_for_student
    
    # 删除旧缓存
    delete_old_cache_for_student(student_id, current_hash)
    # 初始化结果
    result = {
        'categories': [],
        'total_colleges': 0
    }
    
    # 定义类别名称映射
    category_names = {
        1: "冲",
        2: "稳",
        3: "保"
    }
    
    # 批量查询所有组的院校数量，减少数据库查询次数
    student_score = recommendation_data['student_score'] if recommendation_data['student_score'] is not None and recommendation_data['student_score'] > 0 else recommendation_data['mock_exam_score']
    subject_type = recommendation_data['subject_type']
    education_level = recommendation_data['education_level']
    student_subjects = recommendation_data['student_subjects']
    area_ids = recommendation_data['area_ids']
    specialty_types = recommendation_data['specialty_types']
    
    # 遍历三个类别（冲、稳、保）
    for category_id in [1, 2, 3]:
        category_data = {
            'category_id': category_id,
            'category_name': category_names[category_id],
            'total_colleges': 0,
            'groups': []
        }
        
        # 每个类别只有4个组（而不是12个）
        # 计算起始组ID和结束组ID
        start_group_id = (category_id - 1) * 4 + 1
        end_group_id = start_group_id + 3
        
        # 遍历当前类别下的4个志愿段
        for group_id in range(start_group_id, end_group_id + 1):
            # 使用优化的方法获取院校数量
            group_college_count = RecommendationService.get_college_count_by_category_and_group(
                student_score=student_score,
                subject_type=subject_type,
                education_level=education_level,
                category_id=category_id,
                group_id=group_id,
                student_subjects=student_subjects,
                area_ids=area_ids,
                specialty_types=specialty_types,
                mode=mode,
                tese_types=recommendation_data.get('tese_types'),
                leixing_types=recommendation_data.get('leixing_types'),
                teshu_types=recommendation_data.get('teshu_types'),
                tuition_ranges=recommendation_data.get('tuition_ranges')
            )
            
            # 添加该组的统计数据（移除selected_count）
            category_data['groups'].append({
                'group_id': group_id,
                'total_colleges': group_college_count
            })
            
            # 累加到类别总数
            category_data['total_colleges'] += group_college_count
            
        # 添加类别数据到结果
        result['categories'].append(category_data)
        
        # 累加到总院校数
        result['total_colleges'] += category_data['total_colleges']
    
    # 将结果存入缓存，有效期1天
    cache.set(cache_key, result, timeout=86400)  # 一天
    
    return APIResponse.success(result, message="获取院校统计数据成功")