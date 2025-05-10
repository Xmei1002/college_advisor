from app.models.user import User
from app.models.studentProfile import Student
from app.models.student_volunteer_plan import StudentVolunteerPlan
from app.extensions import db
from datetime import datetime

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
    
    current_date = datetime.now()
    current_month = current_date.month
    current_day = current_date.day
    
    # 计算该学生成功生成的方案数量
    plan_count = StudentVolunteerPlan.query.filter_by(
        student_id=student_id,
        generation_status=StudentVolunteerPlan.GENERATION_STATUS_SUCCESS
    ).count()

    # 如果是高考出分后，只计算出分后的方案；如果是出分前，只计算出分前的方案
    cutoff_date = datetime(current_date.year, 6, 9)
    if is_after_exam_results:
        # 出分后，只统计出分后的方案
        query = query.filter(StudentVolunteerPlan.created_at >= cutoff_date)
    else:
        # 出分前，只统计出分前的方案
        query = query.filter(StudentVolunteerPlan.created_at < cutoff_date)
    
    plan_count = query.count()


    
    is_after_exam_results = (current_month > 6) or (current_month == 6 and current_day >= 9)
    
    # 根据高考出分情况，设置不同的状态前缀
    prefix = "正式" if is_after_exam_results else "模拟"
    
    # 更新学生的咨询状态
    status_text = f"{prefix}方案{plan_count}次"
    user.consultation_status = status_text
    db.session.commit()
    
    return status_text