# app/tasks/volunteer_tasks.py

from flask import current_app
from app.extensions import celery
from app.services.volunteer.plan_service import generate_complete_volunteer_plan
from app.services.volunteer.volunteer_analysis_service import AIVolunteerAnalysisService
from app.services.volunteer.ai_college_specialty_service import AICollegeSpecialtyAnalysisService

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
    
@celery.task(bind=True)
def analyze_volunteer_category_task(self, plan_id, category_id):
    """
    异步分析志愿类别任务
    
    :param plan_id: 志愿方案ID
    :param category_id: 类别ID
    :return: 任务结果
    """
    task_id = self.request.id
    current_app.logger.info(f"异步分析志愿类别任务开始，任务ID: {task_id}, 方案ID: {plan_id}, 类别ID: {category_id}")
    
    try:
        # 调用实际的业务逻辑函数
        result = AIVolunteerAnalysisService.perform_volunteer_category_analysis(
            plan_id=plan_id,
            category_id=category_id,
        )
        
        return result
        
    except Exception as e:
        current_app.logger.error(f"异步分析志愿类别任务异常，任务ID: {task_id}, 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"任务执行异常: {str(e)}"
        }
    

@celery.task(bind=True)
def analyze_college_task(self, volunteer_college_id):
    """
    异步分析院校的任务
    
    :param volunteer_college_id: 志愿院校ID
    :return: 任务结果
    """
    task_id = self.request.id
    current_app.logger.info(f"异步分析院校任务开始，任务ID: {task_id}, 院校ID: {volunteer_college_id}")
    
    try:
        result = AICollegeSpecialtyAnalysisService.perform_college_analysis(volunteer_college_id)
        
        return result
    
    except Exception as e:
        current_app.logger.error(f"异步分析院校任务失败: {str(e)}")
        return {
            'status': 'error',
            'volunteer_college_id': volunteer_college_id,
            'message': f'分析过程出错: {str(e)}'
        }

@celery.task(bind=True)
def analyze_specialty_task(self, specialty_id):
    """
    异步分析专业的任务
    
    :param specialty_id: 志愿专业ID
    :return: 任务结果
    """
    task_id = self.request.id
    current_app.logger.info(f"异步分析专业任务开始，任务ID: {task_id}, 专业ID: {specialty_id}")
    
    try:
        result = AICollegeSpecialtyAnalysisService.perform_specialty_analysis(specialty_id)
        
        return result
    
    except Exception as e:
        current_app.logger.error(f"异步分析专业任务失败: {str(e)}")
        return {
            'status': 'error',
            'specialty_id': specialty_id,
            'message': f'分析过程出错: {str(e)}'
        }