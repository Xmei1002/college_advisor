# app/api/endpoints/student.py
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.studentProfile import Student,AcademicRecord
from app.models.user import User
from app.extensions import db
from datetime import datetime, timezone

# 创建学生信息蓝图
student_bp = Blueprint(
    'student', 
    'student',
    description='学生信息管理接口',
)

from app.api.schemas.student import (
    StudentProfileSchema, AcademicRecordSchema,
    StudentResponseSchema, AcademicRecordResponseSchema
)

@student_bp.route('/profile', methods=['POST'])
@student_bp.arguments(StudentProfileSchema)
@student_bp.response(201, StudentResponseSchema)
@jwt_required()
@api_error_handler
def create_student_profile(data):
    """
    创建或更新学生基本信息
    
    为当前登录用户创建或更新学生基本信息档案
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 检查是否已有学生档案
    existing_profile = Student.query.filter_by(user_id=user.id).first()
    
    if existing_profile:
        # 如果已存在学生档案，就更新它
        for key, value in data.items():
            if hasattr(existing_profile, key) and value is not None:
                setattr(existing_profile, key, value)
        
        existing_profile.save()
        message = "学生信息更新成功"
        code = 200
        student = existing_profile
    else:
        # 创建新的学生档案
        student = Student(
            user_id=user.id,
            name=data['name'],
            gender=data['gender'],
            ethnicity=data.get('ethnicity'),
            phone=data.get('phone'),
            wechat_qq=data.get('wechat_qq'),
            school=data.get('school'),
            address=data.get('address'),
            candidate_number=data.get('candidate_number'),
            id_card_number=data.get('id_card_number'),
            household_type=data.get('household_type'),
            student_type=data.get('student_type'),
            guardian1_name=data.get('guardian1_name'),
            guardian1_phone=data.get('guardian1_phone'),
            guardian2_name=data.get('guardian2_name'),
            guardian2_phone=data.get('guardian2_phone'),
            left_eye_vision=data.get('left_eye_vision'),
            right_eye_vision=data.get('right_eye_vision'),
            color_vision=data.get('color_vision'),
            height=data.get('height'),
            weight=data.get('weight'),
            foreign_language=data.get('foreign_language'),
            is_discredited=data.get('is_discredited', False),
            discredit_reason=data.get('discredit_reason'),
            strong_subjects=data.get('strong_subjects'),
            weak_subjects=data.get('weak_subjects')
        )
        
        student.save()
        message = "学生信息创建成功"
        code = 201
    
    return APIResponse.success(
        data=student.to_dict(),
        message=message,
        code=code
    )

@student_bp.route('/profile', methods=['GET'])
@student_bp.response(200, StudentResponseSchema)
@jwt_required()
@api_error_handler
def get_student_profile():
    """
    获取学生基本信息
    
    获取当前登录用户的学生基本信息档案
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("学生档案不存在，请先创建", code=404)
    
    return APIResponse.success(
        data=student.to_dict(),
        message="获取学生信息成功"
    )

@student_bp.route('/academic-record', methods=['POST'])
@student_bp.arguments(AcademicRecordSchema)
@student_bp.response(201, AcademicRecordResponseSchema)
@jwt_required()
@api_error_handler
def create_academic_record(data):
    """
    创建或更新学业记录
    
    为当前登录用户创建或更新学业记录
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("请先创建学生基本信息档案", code=400)
    
    # 检查是否已有学业记录
    existing_record = AcademicRecord.query.filter_by(student_id=student.id).first()
    
    if existing_record:
        # 如果学业记录已存在，就更新它
        for key, value in data.items():
            if hasattr(existing_record, key) and value is not None:
                setattr(existing_record, key, value)
        
        existing_record.save()
        message = "学业记录更新成功"
        code = 200
        academic_record = existing_record
    else:
        # 创建新的学业记录
        academic_record = AcademicRecord(
            student_id=student.id,
            selected_subjects=data.get('selected_subjects'),
            gaokao_total_score=data.get('gaokao_total_score'),
            gaokao_ranking=data.get('gaokao_ranking'),
            standard_score=data.get('standard_score'),
            bonus_type=data.get('bonus_type'),
            chinese_score=data.get('chinese_score'),
            math_score=data.get('math_score'),
            foreign_lang_score=data.get('foreign_lang_score'),
            physics_score=data.get('physics_score'),
            history_score=data.get('history_score'),
            chemistry_score=data.get('chemistry_score'),
            biology_score=data.get('biology_score'),
            geography_score=data.get('geography_score'),
            politics_score=data.get('politics_score'),
            mock_exam1_score=data.get('mock_exam1_score'),
            mock_exam2_score=data.get('mock_exam2_score'),
            mock_exam3_score=data.get('mock_exam3_score')
        )
        
        academic_record.save()
        message = "学业记录创建成功"
        code = 201
    
    return APIResponse.success(
        data=academic_record.to_dict(),
        message=message,
        code=code
    )

@student_bp.route('/academic-record', methods=['GET'])
@student_bp.response(200, AcademicRecordResponseSchema)
@jwt_required()
@api_error_handler
def get_academic_record():
    """
    获取学业记录
    
    获取当前登录用户的学业记录
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("学生档案不存在", code=404)
    
    # 获取学业记录
    academic_record = AcademicRecord.query.filter_by(student_id=student.id).first()
    if not academic_record:
        return APIResponse.error("学业记录不存在，请先创建", code=404)
    
    return APIResponse.success(
        data=academic_record.to_dict(),
        message="获取学业记录成功"
    )

@student_bp.route('/planner/students/<int:student_id>/profile', methods=['PUT'])
@student_bp.arguments(StudentProfileSchema)
@student_bp.response(200, StudentResponseSchema)
@jwt_required()
@api_error_handler
def planner_update_student_profile(data, student_id):
    """
    更新学生基本信息
    
    规划师更新特定学生的基本信息
    """
    # 获取当前用户（规划师）
    planner_id = get_jwt_identity()
    planner = User.query.get_or_404(int(planner_id))
    
    # 验证权限
    if not planner.is_planner():
        return APIResponse.error("权限不足，仅限规划师操作", code=403)
    
    # 获取学生信息
    student = Student.query.get(student_id)
    if not student:
        return APIResponse.error("未找到该学生", code=404)
    
    # 验证学生是否属于该规划师
    student_user = User.query.get(student.user_id)
    if not student_user or student_user.planner_id != planner.id:
        return APIResponse.error("无权操作此学生信息", code=403)

    try:
        
        # 更新字段
        for field, value in data.items():
            if hasattr(student, field) and value is not None:
                setattr(student, field, value)
        student_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return APIResponse.success(
            data=student.to_dict(),
            message="学生信息更新成功"
        )
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"更新失败: {str(e)}", code=400)

@student_bp.route('/planner/students/<int:student_id>/academic-record', methods=['PUT'])
@student_bp.arguments(AcademicRecordSchema)
@student_bp.response(200, AcademicRecordResponseSchema)
@jwt_required()
@api_error_handler
def planner_update_academic_record(data, student_id):
    """
    更新学业记录
    
    规划师更新特定学生的学业记录
    """
    # 获取当前用户（规划师）
    planner_id = get_jwt_identity()
    planner = User.query.get_or_404(int(planner_id))
    
    # 验证权限
    if not planner.is_planner():
        return APIResponse.error("权限不足，仅限规划师操作", code=403)
    
    # 获取学生信息
    student = Student.query.get_or_404(student_id)
    
    # 验证学生是否属于该规划师
    student_user = User.query.get(student.user_id)
    if not student_user or student_user.planner_id != planner.id:
        return APIResponse.error("无权操作此学生信息", code=403)
    
    try:
        # 获取学业记录
        academic_record = AcademicRecord.query.filter_by(student_id=student.id).first()
        
        if not academic_record:
            # 如果学业记录不存在，创建一个新的
            academic_record = AcademicRecord(
                student_id=student.id,
                **{k: v for k, v in data.items() if v is not None}
            )
            academic_record.save()

            student_user.updated_at = datetime.now(timezone.utc)
            return APIResponse.success(
                data=academic_record.to_dict(),
                message="学业记录创建成功"
            )
        
        # 更新字段
        for field, value in data.items():
            if hasattr(academic_record, field) and value is not None:
                setattr(academic_record, field, value)
        
        db.session.commit()
        
        return APIResponse.success(
            data=academic_record.to_dict(),
            message="学业记录更新成功"
        )
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"更新失败: {str(e)}", code=400)
    
@student_bp.route('/my-planner', methods=['GET'])
@jwt_required()
@api_error_handler
def get_my_planner():
    """
    获取我的规划师
    
    返回当前学生的规划师信息
    """
    # 获取当前用户（学生）
    student_id = get_jwt_identity()
    student = User.query.get_or_404(student_id)
    
    if not student.is_student():
        return APIResponse.error("当前用户不是学生", code=403)
    
    if not student.planner:
        return APIResponse.error("您还没有分配规划师", code=404)
    
    return APIResponse.success(
        data=student.planner.to_dict(),
        message="获取成功"
    )