# app/api/endpoints/volunteer_plan.py

from flask import current_app,request 
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.student_volunteer_plan import StudentVolunteerPlan
from app.services.volunteer.plan_service import VolunteerPlanService, generate_complete_volunteer_plan
from app.tasks.volunteer_tasks import generate_volunteer_plan_task
from flask_smorest import Blueprint
from app.api.schemas.volunteer_plan import (
    PlanHistoryResponseSchema, PlanDetailResponseSchema,GenerateAiPlanSchema,
    PlanHistoryQueryParamsSchema, PlanDetailQueryParamsSchema,UpdateVolunteerPlanSchema,
    VolunteerPlanResponseSchema
)
from app.models.user import User
from app.utils.user_hash import calculate_user_data_hash
from app.services.student.student_data_service import StudentDataService
from app.services.volunteer.consultation_status_service import update_student_plan_status
# 添加防重复提交检查
from flask import session
import time
from flask import send_file

# 创建志愿方案蓝图
volunteer_plan_bp = Blueprint(
    'volunteer_plan', 
    'volunteer_plan',
    description='志愿方案管理相关接口',
)


@volunteer_plan_bp.route('/generate-ai-plan', methods=['POST'])
@volunteer_plan_bp.arguments(GenerateAiPlanSchema)
@volunteer_plan_bp.response(202)
@jwt_required()
@api_error_handler
def generate_ai_volunteer_plan(data):
    """
    AI自动生成志愿方案(异步)
    
    根据学生信息自动生成完整的志愿方案，包含12个批次共48个院校志愿
    """
    student_id = data['student_id']
    planner_id = get_jwt_identity()  # 当前登录的规划师ID
    
    # 获取学生当前数据
    student_data = StudentDataService.extract_college_recommendation_data(student_id)
    # 计算当前数据哈希
    current_hash = calculate_user_data_hash(student_data)
    
    # 检查是否存在最近的成功方案
    latest_plan = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        is_current=True,
        generation_status=StudentVolunteerPlan.GENERATION_STATUS_SUCCESS
    ).order_by(StudentVolunteerPlan.version.desc()).first()
    
    # 如果存在最近方案且数据哈希相同，拒绝重新生成
    if latest_plan and latest_plan.user_data_hash == current_hash:
        return APIResponse.success(
            message="用户数据未发生变化，无需重新生成志愿方案",
            code=200
        )
    
    # 启动异步任务，并传递当前数据哈希
    task = generate_volunteer_plan_task.delay(
        student_id=student_id,
        planner_id=planner_id,
        user_data_hash=current_hash
    )
    
    return APIResponse.success(
        message="志愿方案生成任务已启动",
        code=202
    )

@volunteer_plan_bp.route('/history/<int:student_id>', methods=['GET'])
@volunteer_plan_bp.response(200, PlanHistoryResponseSchema)
@volunteer_plan_bp.arguments(PlanHistoryQueryParamsSchema, location="query")
@jwt_required()
@api_error_handler
def get_plan_history(query_args, student_id):
    """
    查看学生所有历史志愿方案版本
    
    获取指定学生的所有志愿方案版本列表，按版本号降序排列
    """
    # 获取当前用户ID
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取分页参数
    page = query_args.get('page', 1)
    per_page = query_args.get('per_page', 10)
    
    # 查询学生的历史志愿方案版本
    plans = StudentVolunteerPlan.query.filter_by(
        student_id=student_id
    ).order_by(
        StudentVolunteerPlan.version.desc()
    ).paginate(
        page=page, per_page=per_page
    )
    
    # 构建响应数据
    plan_list = [plan.to_dict() for plan in plans.items]
    
    return APIResponse.pagination(
        items=plan_list,
        total=plans.total,
        page=page,
        per_page=per_page,
        message="获取历史志愿方案成功"
    )

@volunteer_plan_bp.route('/detail/<int:plan_id>', methods=['GET'])
@volunteer_plan_bp.response(200, PlanDetailResponseSchema)
@volunteer_plan_bp.arguments(PlanDetailQueryParamsSchema, location="query")
@jwt_required()
@api_error_handler
def get_plan_detail(query_args, plan_id):
    """
    获取志愿方案详细信息
    
    获取指定版本志愿方案的详细信息，包括院校志愿和专业志愿。
    可选按类别ID、志愿段ID或志愿序号过滤结果。
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取查询参数
    include_details = query_args.get('include_details', True)
    category_id = query_args.get('category_id')
    group_id = query_args.get('group_id')
    volunteer_index = query_args.get('volunteer_index')
    
    # 使用服务获取志愿方案详情
    plan_detail = VolunteerPlanService.get_volunteer_plan(
        plan_id=plan_id,
        include_details=include_details,
        category_id=category_id,
        group_id=group_id,
        volunteer_index=volunteer_index
    )
    
    return APIResponse.success(
        data=plan_detail,
        message="获取志愿方案详情成功"
    )

@volunteer_plan_bp.route('/current/<int:student_id>', methods=['GET'])
@volunteer_plan_bp.response(200, PlanDetailResponseSchema)
@volunteer_plan_bp.arguments(PlanDetailQueryParamsSchema, location="query")
@jwt_required()
@api_error_handler
def get_current_plan(query_args, student_id):
    """
    查看学生当前(最新)志愿方案版本
    
    获取指定学生的当前最新志愿方案版本。
    可选按类别ID、志愿段ID或志愿序号过滤结果。
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # 检查用户类型权限 - 只有规划师可以访问该接口
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 查询学生的当前志愿方案版本
    plan = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        is_current=True
    ).first()
    
    if not plan:
        return APIResponse.error("当前学生没有志愿方案", code=404)
    
    # 获取查询参数
    include_details = query_args.get('include_details', True)
    category_id = query_args.get('category_id')
    group_id = query_args.get('group_id')
    volunteer_index = query_args.get('volunteer_index')
    
    # 使用服务获取志愿方案详情
    plan_detail = VolunteerPlanService.get_volunteer_plan(
        plan_id=plan.id,
        include_details=include_details,
        category_id=category_id,
        group_id=group_id,
        volunteer_index=volunteer_index
    )
    
    return APIResponse.success(
        data=plan_detail,
        message="获取当前志愿方案成功"
    )

@volunteer_plan_bp.route('/plan/<int:plan_id>', methods=['PUT'])
@volunteer_plan_bp.arguments(UpdateVolunteerPlanSchema)
@volunteer_plan_bp.response(200, VolunteerPlanResponseSchema)
@jwt_required()
@api_error_handler
def update_volunteer_plan(data, plan_id):
    """
    更新志愿方案
    
    更新指定ID的志愿方案，可以选择创建新版本或更新当前版本
    """
    # 获取当前用户
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # 检查权限,如果不是规划师，则返回403错误
    if current_user.user_type != User.USER_TYPE_PLANNER:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取上次提交时间
    last_submit_time = session.get('last_update_time', 0)
    current_time = time.time()
    
    # 如果两次提交间隔小于10秒，则认为是重复提交
    if current_time - last_submit_time < 10:
        return APIResponse.error("请勿频繁提交，请稍后再试", code=429)
    
    # 更新提交时间
    session['last_update_time'] = current_time
    
    # 调用服务更新志愿方案
    updated_plan = VolunteerPlanService.update_volunteer_plan(
        plan_id=plan_id,
        update_data=data,
    )
    
    # 获取方案对应的学生ID并更新咨询状态
    plan = StudentVolunteerPlan.query.get(plan_id)
    if plan:
        update_student_plan_status(plan.student_id)
    
    # 记录更新日志
    current_app.logger.info(
        f"用户 {current_user_id} 更新了志愿方案 {plan_id}，"
    )
    
    return APIResponse.success(
        data=updated_plan,
        message="志愿方案更新成功"
    )


@volunteer_plan_bp.route('/export/<int:plan_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def export_volunteer_plan(plan_id):
    """导出志愿方案为Excel文件"""
    
    # 添加日志记录，帮助调试
    current_app.logger.info(f"开始导出志愿方案 {plan_id} 为Excel文件")
    
    result = VolunteerPlanService.export_volunteer_plan_to_excel(plan_id)
    
    # 记录结果
    current_app.logger.info(f"导出结果: {result}")
    
    if result['success']:
        return send_file(
            result['filepath'],
            as_attachment=True,
            download_name=result['filename'],
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        return APIResponse.error(
            message=result.get('error', '导出志愿方案失败'),  # 使用 get 方法避免键不存在的情况
            code=500
        )