# app/tasks/volunteer_tasks.py

from flask import current_app
from app.extensions import celery
from app.services.volunteer.plan_service import generate_complete_volunteer_plan
from app.services.volunteer.volunteer_analysis_service import AIVolunteerAnalysisService
from app.services.volunteer.ai_college_specialty_service import AICollegeSpecialtyAnalysisService
from app.models.student_volunteer_plan import StudentVolunteerPlan, VolunteerCategoryAnalysis
from app.extensions import db
from app.services.ai.llm_service import LLMService
from app.services.volunteer.consultation_status_service import update_student_plan_status
from app.services.chat.chat_service import ChatService

@celery.task(bind=True)
def generate_volunteer_plan_task(self, student_id, planner_id, user_data_hash, is_first = False):
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
            user_data_hash=user_data_hash,
            is_first=is_first
        )
        
        if not is_first:
            print("生成方案成功，开始更新学生志愿方案状态")
            # 更新学生志愿方案状态
            update_student_plan_status(student_id)
        
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
    

@celery.task(bind=True)
def analyze_student_snapshots_ai(self, plan_id, current_snapshot, previous_snapshot):
    """
    异步任务：使用AI分析两次学生数据快照的差异
    
    :param current_snapshot: 当前方案的学生数据快照
    :param previous_snapshot: 前一个方案的学生数据快照
    :return: 任务结果
    """
    try:
        current_plan = StudentVolunteerPlan.query.get(plan_id)

        if previous_snapshot is None:
            current_plan.data_changes = "第一次生成方案"
        else:
            changes_text = LLMService.analyzing_student_snapshots(current_snapshot, previous_snapshot)
            # 更新方案的变更记录和分析状态
            current_plan.data_changes = changes_text
        db.session.commit()
        return {
            "status": "success", 
            "message": "AI分析完成",
        }
        
    except Exception as e:
        current_plan = StudentVolunteerPlan.query.get(plan_id)
        current_plan.data_changes = f"分析失败"
        db.session.commit()
        
        return {
            "status": "error", 
            "message": f"AI分析失败: {str(e)}",
            "plan_id": plan_id
        }
    

@celery.task(bind=True)
def generate_conversation_title_task(self, conversation_id, message_content):
    """
    异步生成会话标题的Celery任务
    
    :param conversation_id: 会话ID
    :param message_content: 用户消息内容
    """
    try:
        
        # 调用AI生成标题
        generated_title = LLMService.generate_conversation_title(message_content)
        
        # 确保生成的标题不为空且不超过30个字符
        if generated_title and len(generated_title.strip()) > 0:
            title = generated_title
            # 更新会话标题
            ChatService.update_conversation_title(conversation_id, title)
            return {"status": "success", "title": title}
        else:
            return {"status": "error", "message": "生成的标题为空"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery.task(bind=True)
def analyze_volunteer_plan_task(self, plan_id):
    """
    异步分析整体志愿方案
    
    :param plan_id: 志愿方案ID
    :return: 任务结果
    """
    task_id = self.request.id
    current_app.logger.info(f"异步分析整体志愿方案任务开始，任务ID: {task_id}")
    
    try:
        # 更新分析状态为处理中，使用VolunteerCategoryAnalysis表的category_id=0表示整体分析
        plan_analysis = VolunteerCategoryAnalysis.query.filter_by(
            plan_id=plan_id,
            category_id=0
        ).first()
        
        if not plan_analysis:
            plan_analysis = VolunteerCategoryAnalysis(
                plan_id=plan_id,
                category_id=0,  # 0表示整体分析
                status=VolunteerCategoryAnalysis.STATUS_PROCESSING
            )
            db.session.add(plan_analysis)
        else:
            plan_analysis.status = VolunteerCategoryAnalysis.STATUS_PROCESSING
            
        db.session.commit()
        
        # 执行分析
        result = AIVolunteerAnalysisService.perform_volunteer_plan_analysis(plan_id)
        
        return {
            'status': result.get('status', 'success'),
            'message': result.get('message', '整体志愿方案分析完成'),
            'plan_id': plan_id,
            'analysis': result.get('analysis', None)
        }
    
    except Exception as e:
        current_app.logger.error(f"异步分析整体志愿方案失败: {str(e)}")
        
        try:
            # 更新为失败状态
            plan_analysis = VolunteerCategoryAnalysis.query.filter_by(
                plan_id=plan_id,
                category_id=0
            ).first()
            if plan_analysis:
                plan_analysis.status = VolunteerCategoryAnalysis.STATUS_FAILED
                plan_analysis.error_message = str(e)
                db.session.commit()
        except:
            pass
            
        return {
            'status': 'error',
            'message': f'整体志愿方案分析失败: {str(e)}',
            'plan_id': plan_id
        }