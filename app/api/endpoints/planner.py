# app/api/endpoints/planner.py
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.user import User
from flask_smorest import Blueprint
from app.models.studentProfile import Student,AcademicRecord
from app.api.schemas import PaginationQuerySchema
from app.models.user import User
from app.extensions import db
# 创建规划师管理蓝图
planner_bp = Blueprint(
    'planner', 
    'planner',
    description='规划师与学生关系管理接口',
)

from app.models.collegePreference import CollegePreference
from app.models.careerPreference import CareerPreference
# @planner_bp.route('/assign-student', methods=['POST'])
# @planner_bp.arguments(AssignStudentSchema)
# @planner_bp.response(200)
# @jwt_required()
# @api_error_handler
# def assign_student(data):
#     """
#     分配学生给规划师
    
#     将指定学生分配给当前规划师
#     """
#     student_id = data['student_id']
    
#     # 获取当前用户（规划师）
#     planner_id = get_jwt_identity()
#     planner = User.query.get_or_404(planner_id)
    
#     if not planner.is_planner():
#         return APIResponse.error("当前用户不是规划师", code=403)
    
#     # 获取学生
#     student = User.query.get(student_id)
#     if not student:
#         return APIResponse.error("学生不存在", code=404)
    
#     if not student.is_student():
#         return APIResponse.error("目标用户不是学生", code=400)
    
#     # 分配规划师
#     try:
#         student.assign_planner(planner)
#         return APIResponse.success(message="学生分配成功")
#     except ValueError as e:
#         return APIResponse.error(str(e), code=400)

@planner_bp.route('/my-students', methods=['GET'])
@planner_bp.arguments(PaginationQuerySchema, location='query')
@planner_bp.response(200)
@jwt_required()
@api_error_handler
def get_my_students(args):
    """
    获取我的学生列表
    
    返回当前规划师的所有学生，支持分页和搜索
    """
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    keyword = args.get('keyword')
    
    # 获取当前用户（规划师）
    planner_id = get_jwt_identity()
    planner = User.query.get_or_404(planner_id)
    
    if not planner.is_planner():
        return APIResponse.error("当前用户不是规划师", code=403)
    
    try:
        # 基础查询 - 只获取有学生信息的用户
        # 通过JOIN Student表确保只返回有学生信息的用户
        query = User.query.join(
            Student, User.id == Student.user_id
        ).filter(User.planner_id == planner.id)
        
        # 添加搜索条件
        if keyword:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{keyword}%'),
                    Student.name.like(f'%{keyword}%'),
                    Student.phone.like(f'%{keyword}%'),
                    Student.school.like(f'%{keyword}%'),
                    Student.candidate_number.like(f'%{keyword}%')
                )
            )
        
        # 按更新时间降序排序（最近更新的在前）
        query = query.order_by(User.updated_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        # 获取详细的学生信息
        students_data = []
        for user in pagination.items:
            # 由于已经通过JOIN确保了所有用户都有学生信息，所以可以安全地包含学生档案
            user_dict = user.to_dict(include_student_profile=True)
            students_data.append(user_dict)
        
        pagination_info = {
            'total': pagination.total,
            'pages': pagination.pages,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        
        # 创建一个包含数据项和分页信息的新数据结构
        data = {
            "items": students_data,
            "pagination": pagination_info
        }
        
        # 使用 success 方法返回
        return APIResponse.success(
            data=data,
            message="获取成功"
        )
        
    except Exception as e:
        return APIResponse.error(f"获取学生列表失败: {str(e)}", code=400)
    
@planner_bp.route('/my-students/<int:student_id>/information', methods=['GET'])
@planner_bp.response(200)  # 这个Schema需要定义，见下文
@jwt_required()
@api_error_handler
def get_student_information(student_id):
    """
    获取学生完整信息
    
    规划师获取指定学生的基本信息和学业记录
    """
    # 获取当前用户（规划师）
    planner_id = get_jwt_identity()
    planner = User.query.get_or_404(int(planner_id))
    
    # 验证身份是否为规划师
    if not planner.is_planner():
        return APIResponse.error("权限不足，仅限规划师操作", code=403)
    
    user_id = Student.query.get_or_404(student_id).user_id
    
    # 获取学生用户信息
    student_user = User.query.get_or_404(user_id)
    
    # 验证学生是否属于该规划师
    if student_user.planner_id != planner.id:
        return APIResponse.error("无权访问此学生信息", code=403)
    
    # 验证用户类型是否为学生
    if not student_user.is_student():
        return APIResponse.error("指定用户不是学生", code=400)
    
    # 获取学生档案信息
    student_profile = Student.query.filter_by(user_id=student_user.id).first()
    if not student_profile:
        return APIResponse.error("学生档案不存在", code=404)
    
    # 获取学业记录
    academic_record = AcademicRecord.query.filter_by(student_id=student_profile.id).first()
    
    # 组装返回数据
    result = {
        "user": student_user.to_dict(),
        "profile": student_profile.to_dict(),
        "academic_record": academic_record.to_dict() if academic_record else None
    }
    
    return APIResponse.success(
        data=result,
        message="获取学生信息成功"
    )

@planner_bp.route('/my-students/<int:student_id>/preferences', methods=['GET'])
@planner_bp.response(200)
@jwt_required()
@api_error_handler
def get_student_preferences(student_id):
    """
    获取学生志愿和就业倾向
    
    规划师获取指定学生的志愿填报意向和就业倾向完整信息
    """
    # 获取当前用户（规划师）
    planner_id = get_jwt_identity()
    planner = User.query.get_or_404(int(planner_id))
    
    # 验证身份是否为规划师
    if not planner.is_planner():
        return APIResponse.error("权限不足，仅限规划师操作", code=403)
    
    user_id = Student.query.get_or_404(student_id).user_id
    
    # 获取学生用户信息
    student_user = User.query.get_or_404(user_id)
    
    # 验证学生是否属于该规划师
    if student_user.planner_id != planner.id:
        return APIResponse.error("无权访问此学生信息", code=403)
    
    # 验证用户类型是否为学生
    if not student_user.is_student():
        return APIResponse.error("指定用户不是学生", code=400)
    
    # 获取学生档案信息
    student = Student.query.filter_by(user_id=student_user.id).first()
    if not student:
        return APIResponse.error("学生档案不存在", code=404)
    
    # 获取志愿填报意向
    college_preference = CollegePreference.query.filter_by(student_id=student.id).first()
    
    # 获取就业倾向信息
    career_preference = CareerPreference.query.filter_by(student_id=student.id).first()
    
    # 组装返回数据
    result = {
        "user": student_user.to_dict(),
        "college_preference": college_preference.to_dict() if college_preference else None,
        "career_preference": career_preference.to_dict() if career_preference else None
    }
    
    return APIResponse.success(
        data=result,
        message="获取学生志愿和就业倾向信息成功"
    )





