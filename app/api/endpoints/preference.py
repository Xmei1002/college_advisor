# app/api/endpoints/preference.py
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.studentProfile import Student
from app.models.collegePreference import CollegePreference
from app.models.careerPreference import CareerPreference
from app.models.user import User
from app.extensions import db
from datetime import datetime, timezone

# 创建志愿填报意向蓝图
preference_bp = Blueprint(
    'preference', 
    'preference',
    description='志愿填报意向信息管理接口',
)

from app.api.schemas.preference import (
    CollegePreferenceBaseSchema, CollegePreferenceStrategySchema, 
    CollegePreferenceFullSchema, CareerPreferenceSchema,
    CollegePreferenceResponseSchema, CareerPreferenceResponseSchema
)

@preference_bp.route('/college', methods=['POST'])
@preference_bp.arguments(CollegePreferenceBaseSchema)
@preference_bp.response(201, CollegePreferenceResponseSchema)
@jwt_required()
@api_error_handler
def create_college_preference(data):
    """
    创建/更新志愿填报意向信息
    
    保存学生的志愿填报意向信息（地域、学费、专业、学校）
    """
    # 获取当前用户
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("请先创建学生基本信息档案", code=400)
    
    # 检查是否已有志愿填报意向
    preference = CollegePreference.query.filter_by(student_id=student.id).first()
    
    if not preference:
        # 创建新记录
        preference = CollegePreference(
            student_id=student.id,
            **{k: v for k, v in data.items() if v is not None}
        )
        preference.save()
        message = "志愿填报意向信息创建成功"
    else:
        # 更新现有记录
        for field, value in data.items():
            if value is not None:
                setattr(preference, field, value)
        db.session.commit()
        message = "志愿填报意向信息更新成功"
    
    return APIResponse.success(
        data=preference.to_dict(),
        message=message,
        code=201 if not preference else 200
    )

@preference_bp.route('/college/strategy', methods=['POST'])
@preference_bp.arguments(CollegePreferenceStrategySchema)
@preference_bp.response(200, CollegePreferenceResponseSchema)
@jwt_required()
@api_error_handler
def update_college_strategy(data):
    """
    填报策略
    
    设置学生的填报策略（院校优先或专业优先）
    """
    # 获取当前用户
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("请先创建学生基本信息档案", code=400)
    
    # 检查是否已有志愿填报意向
    preference = CollegePreference.query.filter_by(student_id=student.id).first()
    if not preference:
        return APIResponse.error("请先填写志愿填报意向信息", code=400)
    
    # 更新策略
    preference.strategy = data['strategy']
    db.session.commit()
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="填报策略设置成功"
    )

@preference_bp.route('/college', methods=['GET'])
@preference_bp.response(200, CollegePreferenceResponseSchema)
@jwt_required()
@api_error_handler
def get_college_preference():
    """
    获取志愿填报意向信息
    
    获取当前学生的志愿填报意向完整信息
    """
    # 获取当前用户
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("学生档案不存在", code=404)
    
    # 获取志愿填报意向
    preference = CollegePreference.query.filter_by(student_id=student.id).first()
    if not preference:
        return APIResponse.error("志愿填报意向信息不存在", code=404)
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="获取志愿填报意向信息成功"
    )


@preference_bp.route('/career', methods=['POST'])
@preference_bp.arguments(CareerPreferenceSchema)
@preference_bp.response(201, CareerPreferenceResponseSchema)
@jwt_required()
@api_error_handler
def create_career_preference(data):
    """
    创建/更新就业倾向信息
    
    保存学生的就业倾向信息
    """
    # 获取当前用户
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("请先创建学生基本信息档案", code=400)
    
    # 检查是否已有就业倾向信息
    preference = CareerPreference.query.filter_by(student_id=student.id).first()
    
    if not preference:
        # 创建新记录
        preference = CareerPreference(
            student_id=student.id,
            **{k: v for k, v in data.items() if v is not None}
        )
        preference.save()
        message = "就业倾向信息创建成功"
    else:
        # 更新现有记录
        for field, value in data.items():
            if value is not None:
                setattr(preference, field, value)
        db.session.commit()
        message = "就业倾向信息更新成功"
    
    return APIResponse.success(
        data=preference.to_dict(),
        message=message,
        code=201 if not preference else 200
    )

@preference_bp.route('/career', methods=['GET'])
@preference_bp.response(200, CareerPreferenceResponseSchema)
@jwt_required()
@api_error_handler
def get_career_preference():
    """
    获取就业倾向信息
    
    获取当前学生的就业倾向完整信息
    """
    # 获取当前用户
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 获取学生档案
    student = Student.query.filter_by(user_id=user.id).first()
    if not student:
        return APIResponse.error("学生档案不存在", code=404)
    
    # 获取就业倾向信息
    preference = CareerPreference.query.filter_by(student_id=student.id).first()
    if not preference:
        return APIResponse.error("就业倾向信息不存在", code=404)
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="获取就业倾向信息成功"
    )


@preference_bp.route('/planner/students/<int:student_id>/college', methods=['GET'])
@preference_bp.response(200, CollegePreferenceResponseSchema)
@jwt_required()
@api_error_handler
def planner_get_college_preference(student_id):
    """
    规划师获取学生志愿填报意向
    
    规划师查看特定学生的志愿填报意向信息
    """
    # 获取当前用户并验证权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 检查是否为规划师
    if not user.is_planner():
        return APIResponse.error("权限不足", code=403)
    
    # 获取学生
    student = Student.query.get_or_404(student_id)
    
    # 获取志愿填报意向
    preference = CollegePreference.query.filter_by(student_id=student.id).first()
    if not preference:
        return APIResponse.error("该学生的志愿填报意向信息不存在", code=404)
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="获取志愿填报意向信息成功"
    )

@preference_bp.route('/planner/students/<int:student_id>/college', methods=['PUT'])
@preference_bp.arguments(CollegePreferenceFullSchema)
@preference_bp.response(200, CollegePreferenceResponseSchema)
@jwt_required()
@api_error_handler
def planner_update_college_preference(data, student_id):
    """
    规划师更新学生志愿填报意向
    
    规划师修改特定学生的志愿填报意向信息
    """
    # 获取当前用户并验证权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    # 检查是否为规划师
    if not user.is_planner():
        return APIResponse.error("权限不足", code=403)
    
    # 获取学生
    student = Student.query.get_or_404(student_id)
    # 获取或创建志愿填报意向
    preference = CollegePreference.query.filter_by(student_id=student.id).first()
    if not preference:
        preference = CollegePreference(student_id=student.id)
        db.session.add(preference)
    
    # 更新字段
    for field, value in data.items():
        if value is not None:
            setattr(preference, field, value)

    user_student = User.query.get_or_404(student.user_id)
    user_student.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="更新志愿填报意向信息成功"
    )

@preference_bp.route('/planner/students/<int:student_id>/career', methods=['PUT'])
@preference_bp.arguments(CareerPreferenceSchema)
@preference_bp.response(200, CareerPreferenceResponseSchema)
@jwt_required()
@api_error_handler
def planner_update_career_preference(data, student_id):
    """
    规划师更新学生就业倾向
    
    规划师修改特定学生的就业倾向信息
    """
    # 获取当前用户并验证权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    
    # 检查是否为规划师
    if not user.is_planner():
        return APIResponse.error("权限不足", code=403)
    
    # 获取学生
    student = Student.query.get_or_404(student_id)
    
    # 获取或创建就业倾向信息
    preference = CareerPreference.query.filter_by(student_id=student.id).first()
    if not preference:
        preference = CareerPreference(student_id=student.id)
        db.session.add(preference)
    
    # 更新字段
    for field, value in data.items():
        if value is not None:
            setattr(preference, field, value)
    
    user_student = User.query.get_or_404(student.user_id)
    user_student.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    
    return APIResponse.success(
        data=preference.to_dict(),
        message="更新就业倾向信息成功"
    )