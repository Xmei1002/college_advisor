# app/api/endpoints/volunteer_plan.py
from flask import current_app,request 
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from flask_smorest import Blueprint
from app.api.schemas.volunteer_analysis import (
  VolunteerCategorySchema, QueryAnalysisResultSchema, CollegeAnalysisSchema, SpecialtyAnalysisSchema
)
from app.models.student_volunteer_plan import VolunteerCollege, VolunteerSpecialty, VolunteerCategoryAnalysis
from app.tasks.volunteer_tasks import analyze_volunteer_category_task, analyze_college_task, analyze_specialty_task
from app.models.user import User
from app.services.student.student_data_service import StudentDataService
# 创建志愿方案蓝图
volunteer_analysis_bp = Blueprint(
    'volunteer_analysis', 
    'volunteer_analysis',
    description='AI志愿分析相关接口',
)

@volunteer_analysis_bp.route('/category', methods=['POST'])
@volunteer_analysis_bp.arguments(VolunteerCategorySchema)  # 使用 Schema 解析请求数据
@jwt_required()
@api_error_handler
def analyze_volunteer_category(data):
    """
    AI对每个志愿的冲稳保三类进行分析
    """
    # data 已由 VolunteerCategorySchema 解析为字典

    plan_id = data['plan_id']
    category_id = data['category_id']
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    has_analysis = VolunteerCategoryAnalysis.query.filter_by(
        plan_id=plan_id,
        category_id=category_id
    ).first()

    if has_analysis and has_analysis.status == VolunteerCategoryAnalysis.STATUS_COMPLETED:
        return APIResponse.error("该方案当前类别已存在分析结果", code=400)

    task = analyze_volunteer_category_task.delay(plan_id, category_id)
    return APIResponse.success(
        message="AI志愿分析任务已提交，正在处理中",
        data={
            "task_id": task.id
        },
        code=200
    )

@volunteer_analysis_bp.route('/category/<int:plan_id>/<int:category_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def get_analysis_result(plan_id, category_id):
    """
    获取AI分析结果

    请求示例:
    GET /volunteer-analysis/category/1/2
    """
    # 获取当前用户并验证权限
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)

    # 获取分析结果
    result = VolunteerCategoryAnalysis.query.filter_by(
        plan_id=plan_id,
        category_id=category_id
    ).first()

    if not result or result.status != VolunteerCategoryAnalysis.STATUS_COMPLETED:
        return APIResponse.error("该方案当前类别尚未生成AI分析结果", code=404)
    else:
        analysis = result.analysis_content

    return APIResponse.success(
        data=analysis,
        message="获取AI分析结果成功",
        code=200
    )

# 院校分析接口
@volunteer_analysis_bp.route('/college', methods=['POST'])
@volunteer_analysis_bp.arguments(CollegeAnalysisSchema)
@jwt_required()
@api_error_handler
def analyze_college(data):
    """
    AI分析志愿院校
    
    启动异步任务分析指定志愿院校
    """
    volunteer_college_id = data['volunteer_college_id']
    current_user_id = get_jwt_identity()
    
    # 验证用户权限（只有规划师可以访问）
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 验证院校是否存在
    college = VolunteerCollege.query.get(volunteer_college_id)
    if not college:
        return APIResponse.error(f"未找到ID为{volunteer_college_id}的院校信息", code=404)
    
    # 判断是否已有分析
    if college.ai_analysis:
        return APIResponse.error("该院校已存在AI分析结果", code=400)
    
    # 启动异步任务
    task = analyze_college_task.delay(volunteer_college_id)
    
    return APIResponse.success(
        message="AI院校分析任务已提交，正在处理中",
        data={
            "task_id": task.id
        },
        code=200
    )

@volunteer_analysis_bp.route('/college/<int:volunteer_college_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def get_college_analysis(volunteer_college_id):
    """
    获取志愿院校的AI分析结果
    
    返回指定志愿院校的AI分析内容
    """
    current_user_id = get_jwt_identity()
    
    # 验证用户权限
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取院校信息
    college = VolunteerCollege.query.get(volunteer_college_id)
    if not college:
        return APIResponse.error(f"未找到ID为{volunteer_college_id}的院校信息", code=404)
    
    # 判断是否有分析结果
    if not college.ai_analysis:
        return APIResponse.error("该院校尚未生成AI分析结果", code=404)
    
    # 返回分析结果
    return APIResponse.success(
        data={
            "volunteer_college_id": volunteer_college_id,
            "ai_analysis": college.ai_analysis
        },
        message="获取院校AI分析结果成功"
    )

# 专业分析接口
@volunteer_analysis_bp.route('/specialty', methods=['POST'])
@volunteer_analysis_bp.arguments(SpecialtyAnalysisSchema)
@jwt_required()
@api_error_handler
def analyze_specialty(data):
    """
    AI分析志愿专业
    
    启动异步任务分析指定志愿专业
    """
    specialty_id = data['specialty_id']
    current_user_id = get_jwt_identity()
    
    # 验证用户权限（只有规划师可以访问）
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 验证专业是否存在
    specialty = VolunteerSpecialty.query.get(specialty_id)
    if not specialty:
        return APIResponse.error(f"未找到ID为{specialty_id}的专业信息", code=404)
    
    # 判断是否已有分析
    if specialty.ai_analysis:
        return APIResponse.error("该专业已存在AI分析结果", code=400)
    
    # 启动异步任务
    analyze_specialty_task.delay(specialty_id)
    
    return APIResponse.success(
        message="AI专业分析任务已提交，正在处理中",
        code=200
    )

@volunteer_analysis_bp.route('/specialty/<int:specialty_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def get_specialty_analysis(specialty_id):
    """
    获取志愿专业的AI分析结果
    
    返回指定志愿专业的AI分析内容
    """
    current_user_id = get_jwt_identity()
    
    # 验证用户权限
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取专业信息
    specialty = VolunteerSpecialty.query.get(specialty_id)
    if not specialty:
        return APIResponse.error(f"未找到ID为{specialty_id}的专业信息", code=404)
    
    # 判断是否有分析结果
    if not specialty.ai_analysis:
        return APIResponse.error("该专业尚未生成AI分析结果", code=404)
    
    # 返回分析结果
    return APIResponse.success(
        data={
            "specialty_id": specialty_id,
            "ai_analysis": specialty.ai_analysis
        },
        message="获取专业AI分析结果成功"
    )

# 批量分析接口
@volunteer_analysis_bp.route('/college/batch', methods=['POST'])
@jwt_required()
@api_error_handler
def batch_analyze_colleges():
    """
    批量分析院校
    
    一次性启动对多个院校的分析任务
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 验证用户权限
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取院校ID列表
    college_ids = data.get('college_ids', [])
    if not college_ids:
        return APIResponse.error("未提供院校ID列表", code=400)
    
    # 验证所有院校是否存在
    colleges = VolunteerCollege.query.filter(VolunteerCollege.id.in_(college_ids)).all()
    if len(colleges) != len(college_ids):
        return APIResponse.error("部分院校ID不存在", code=400)
    
    # 启动多个异步任务
    task_count = 0
    for college_id in college_ids:
        college = VolunteerCollege.query.get(college_id)
        if not college.ai_analysis:  # 只分析没有结果的院校
            analyze_college_task.delay(college_id)
            task_count += 1
    
    return APIResponse.success(
        data={"task_count": task_count},
        message=f"已提交{task_count}个院校分析任务"
    )

@volunteer_analysis_bp.route('/specialty/batch', methods=['POST'])
@jwt_required()
@api_error_handler
def batch_analyze_specialties():
    """
    批量分析专业
    
    一次性启动对多个专业的分析任务
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 验证用户权限
    current_user = User.query.get_or_404(current_user_id)
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取专业ID列表
    specialty_ids = data.get('specialty_ids', [])
    if not specialty_ids:
        return APIResponse.error("未提供专业ID列表", code=400)
    
    # 验证所有专业是否存在
    specialties = VolunteerSpecialty.query.filter(VolunteerSpecialty.id.in_(specialty_ids)).all()
    if len(specialties) != len(specialty_ids):
        return APIResponse.error("部分专业ID不存在", code=400)
    
    # 启动多个异步任务
    task_count = 0
    for specialty_id in specialty_ids:
        specialty = VolunteerSpecialty.query.get(specialty_id)
        if not specialty.ai_analysis:  # 只分析没有结果的专业
            analyze_specialty_task.delay(specialty_id)
            task_count += 1
    
    return APIResponse.success(
        data={"task_count": task_count},
        message=f"已提交{task_count}个专业分析任务"
    )