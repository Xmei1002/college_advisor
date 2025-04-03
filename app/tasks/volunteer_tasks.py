# app/tasks/volunteer_tasks.py

from flask import current_app
from app.extensions import celery
from app.services.volunteer.plan_service import generate_complete_volunteer_plan

@celery.task(bind=True)
def generate_volunteer_plan_task(self, student_id, planner_id, user_data_hash):
    """
    异步生成志愿方案任务
    
    :param student_id: 学生ID
    :param planner_id: 规划师ID
    :param user_data_hash: 用户数据哈希
    :return: 任务结果
    """
    task_id = self.request.id
    current_app.logger.info(f"异步生成志愿方案任务开始，任务ID: {task_id}")
    
    try:
        # 调用完整处理流程，并传递用户数据哈希
        result = generate_complete_volunteer_plan(
            student_id=student_id,
            planner_id=planner_id,
            user_data_hash=user_data_hash
        )
        
        # 返回结果
        return {
            'status': 'success',
            'plan_id': result['id'],
            'message': '志愿方案生成成功'
        }
    
    except Exception as e:
        current_app.logger.error(f"异步生成志愿方案失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'志愿方案生成失败: {str(e)}'
        }