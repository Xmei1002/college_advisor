from app.models.user import User
from app.models.studentProfile import Student
from app.models.student_volunteer_plan import StudentVolunteerPlan
from app.extensions import db

def update_student_plan_status(student_id):
    """
    更新学生的咨询状态为"方案X次"
    
    Args:
        student_id: 学生ID
    
    Returns:
        更新后的状态文本
    """
    print("更新学生咨询状态")
    # 查询 Student 记录
    student = Student.query.get(student_id)

    # 检查 Student 是否存在
    if not student:
        raise ValueError("学生ID不存在")

    # 获取关联的 User
    user = User.query.get(student.user_id)

    # 检查 User 是否存在且为学生类型
    if not user or user.user_type != User.USER_TYPE_STUDENT:
        raise ValueError("无效的学生用户或用户类型不匹配")
    
    # 计算该学生成功生成的方案数量
    plan_count = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        generation_status=StudentVolunteerPlan.GENERATION_STATUS_SUCCESS
    ).count()
    
    # 更新学生的咨询状态
    status_text = f"方案{plan_count}次"
    user.consultation_status = status_text
    db.session.commit()
    
    return status_text