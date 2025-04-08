# app/services/volunteer/ai_analysis_service.py
from flask import current_app
from app.extensions import db, celery
from app.models.student_volunteer_plan import StudentVolunteerPlan, VolunteerCollege, VolunteerCategoryAnalysis
from app.models.user import User
from app.services.student.student_data_service import StudentDataService
from sqlalchemy.exc import SQLAlchemyError
import json
from app.services.ai.moonshot import MoonshotAI
from datetime import datetime, timezone
from app.models.student_volunteer_plan import VolunteerSpecialty

class AIVolunteerAnalysisService:
    """AI志愿解读服务类，专门处理所有与志愿填报相关的AI解析功能"""
    
    # AI 分析类别常量
    CATEGORY_MAP = {
        1: "冲刺志愿",
        2: "稳妥志愿",
        3: "保底志愿"
    }
    
    @staticmethod
    def _simplify_colleges_for_ai(colleges):
        """
        简化院校信息用于AI分析
        
        :param colleges: 完整的院校信息列表
        :return: 简化后的院校信息列表
        """
        simplified_colleges = []
        
        for college in colleges:
            simplified_college = AIVolunteerAnalysisService._simplify_college_for_ai(college)
            simplified_colleges.append(simplified_college)
        
        return simplified_colleges

    @staticmethod
    def _simplify_college_for_ai(college):
        """
        简化单个院校信息用于AI分析
        
        :param college: 完整的院校信息
        :return: 简化后的院校信息
        """
        # 提取关键信息
        simplified_college = {
            "college_name": college.get('college_name'),
            "score_diff": college.get('score_diff'),
            "prediction_score": college.get('prediction_score'),
            "area_name": college.get('area_name'),
            "school_type_text": college.get('school_type_text'),
            "tese_text": college.get('tese_text'),
        }
        
        # 提取精简的专业信息
        simplified_specialties = []
        for specialty in college.get('specialties', []):
            simplified_specialty = {
                "specialty_name": specialty.get('specialty_name'),
                "prediction_score": specialty.get('prediction_score'),
                "plan_number": specialty.get('plan_number'),
                "tuition": specialty.get('tuition'),
            }
            simplified_specialties.append(simplified_specialty)
        
        simplified_college['specialties'] = simplified_specialties
        return simplified_college
    
    @staticmethod
    def get_volunteers_by_category(plan_id, category_id):
        """
        获取指定方案中特定类别的志愿信息
        
        :param plan_id: 志愿方案ID
        :param category_id: 类别ID(1:冲, 2:稳, 3:保)
        :return: 该类别的志愿信息列表
        """
        # 验证类别ID是否有效
        if category_id not in [1, 2, 3]:
            raise ValueError("无效的类别ID，必须是 1(冲)、2(稳) 或 3(保)")
        
        # 构建查询
        colleges_query = VolunteerCollege.query.filter_by(
            plan_id=plan_id,
            category_id=category_id
        ).order_by(VolunteerCollege.volunteer_index)
        
        # 执行查询获取结果
        colleges = colleges_query.all()
        college_ids = [college.id for college in colleges]
        
        # 获取分类名称
        category_name = AIVolunteerAnalysisService.CATEGORY_MAP.get(category_id)
        
        # 如果没有找到志愿
        if not colleges:
            return None
        
        # 批量获取所有专业
        specialties = VolunteerSpecialty.query.filter(
            VolunteerSpecialty.volunteer_college_id.in_(college_ids)
        ).order_by(VolunteerSpecialty.specialty_index).all()
        
        # 按院校ID分组专业
        all_specialties = {}
        for specialty in specialties:
            if specialty.volunteer_college_id not in all_specialties:
                all_specialties[specialty.volunteer_college_id] = []
            all_specialties[specialty.volunteer_college_id].append(specialty.to_dict())
        
        # 构建完整的志愿信息
        volunteer_colleges = []
        for college in colleges:
            college_dict = college.to_dict()
            college_dict['specialties'] = all_specialties.get(college.id, [])
            volunteer_colleges.append(college_dict)
        
        return {
            "category_id": category_id,
            "category_name": category_name,
            "colleges": volunteer_colleges
        }
    
    @classmethod
    def analyzing_category(cls, user_info, simplified_colleges_json, category, temperature=0.3):
        """
        获取 AI 的分析响应
        
        :param user_info: 用户信息
        :param simplified_colleges_json: 简化后的院校信息JSON
        :param category: 类别名称
        :param temperature: 控制输出的随机性，默认为0.3
        :return: AI 的分析内容
        """
        res = MoonshotAI.analyzing_category(
            user_info=user_info,
            simplified_colleges_json=simplified_colleges_json,
            category=category,
        )
        
        return res
    
    @staticmethod
    def store_category_analysis(plan_id, category_id, analysis_content, status=None, error_message=None):
        """
        存储类别分析结果
        
        :param plan_id: 志愿方案ID
        :param category_id: 类别ID
        :param analysis_content: 分析内容
        :param status: 分析状态，默认为completed
        :param error_message: 错误信息，当状态为failed时使用
        :return: 是否成功
        """
        try:
            # 如果未指定状态，默认为完成
            if status is None:
                status = VolunteerCategoryAnalysis.STATUS_COMPLETED
                
            # 查找现有分析记录
            analysis = VolunteerCategoryAnalysis.query.filter_by(
                plan_id=plan_id,
                category_id=category_id
            ).first()
            
            if analysis:
                # 更新现有记录
                analysis.status = status
                
                # 根据状态设置不同的字段
                if status == VolunteerCategoryAnalysis.STATUS_COMPLETED:
                    analysis.analysis_content = analysis_content
                    analysis.analyzed_at = datetime.now(timezone.utc)
                    analysis.error_message = None
                elif status == VolunteerCategoryAnalysis.STATUS_FAILED:
                    analysis.error_message = error_message
                    analysis.analyzed_at = datetime.now(timezone.utc)
            else:
                # 创建新记录
                analysis = VolunteerCategoryAnalysis(
                    plan_id=plan_id,
                    category_id=category_id,
                    status=status
                )
                
                # 根据状态设置不同的字段
                if status == VolunteerCategoryAnalysis.STATUS_COMPLETED:
                    analysis.analysis_content = analysis_content
                    analysis.analyzed_at = datetime.now(timezone.utc)
                elif status == VolunteerCategoryAnalysis.STATUS_FAILED:
                    analysis.error_message = error_message
                    analysis.analyzed_at = datetime.now(timezone.utc)
                    
                db.session.add(analysis)
            
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"存储类别分析结果失败: {str(e)}")
            return False
        
    @staticmethod
    def perform_volunteer_category_analysis(plan_id, category_id):
        """
        执行志愿类别分析的实际业务逻辑
        
        :param plan_id: 志愿方案ID
        :param category_id: 类别ID
        :return: 分析结果
        """
        try:
            # 1. 获取学生ID
            student_id = StudentVolunteerPlan.query.get(plan_id).student_id
            # 2. 获取学生数据
            user_info = StudentDataService.generate_student_profile_text(student_id)
            # 3. 获取该类别的志愿信息
            volunteer_data = AIVolunteerAnalysisService.get_volunteers_by_category(plan_id, category_id)
            
            # 如果没有志愿数据，更新为失败状态并返回
            if not volunteer_data:
                error_msg = f"未找到类别{category_id}的志愿信息"
                AIVolunteerAnalysisService.store_category_analysis(
                    plan_id=plan_id,
                    category_id=category_id,
                    analysis_content=None,
                    status=VolunteerCategoryAnalysis.STATUS_FAILED,
                    error_message=error_msg
                )
                return {
                    "status": "error",
                    "message": error_msg
                }
            
            # 4. 简化院校信息用于AI分析
            simplified_colleges = AIVolunteerAnalysisService._simplify_colleges_for_ai(volunteer_data["colleges"])
            simplified_colleges_json = json.dumps(simplified_colleges, ensure_ascii=False)
            
            # 5. 获取类别名称
            category_name = AIVolunteerAnalysisService.CATEGORY_MAP.get(category_id)
            
            # 6. 调用AI分析
            analysis_result = AIVolunteerAnalysisService.analyzing_category(
                user_info=user_info,
                simplified_colleges_json=simplified_colleges_json,
                category=category_name
            )
            
            # 7. 存储分析结果
            success = AIVolunteerAnalysisService.store_category_analysis(
                plan_id=plan_id,
                category_id=category_id,
                analysis_content=analysis_result
            )
            
            if not success:
                error_msg = "存储分析结果失败"
                AIVolunteerAnalysisService.store_category_analysis(
                    plan_id=plan_id,
                    category_id=category_id,
                    analysis_content=None,
                    status=VolunteerCategoryAnalysis.STATUS_FAILED,
                    error_message=error_msg
                )
                return {
                    "status": "error",
                    "message": error_msg
                }
            
            # 8. 返回成功
            return {
                "status": "success",
                "message": f"{category_name}分析完成",
                "plan_id": plan_id,
                "category_id": category_id,
                "analysis": analysis_result  # 可选：返回分析内容
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            current_app.logger.error(f"志愿分析执行失败: {str(e)}\n{error_trace}")
            
            # 更新为失败状态
            AIVolunteerAnalysisService.store_category_analysis(
                plan_id=plan_id,
                category_id=category_id,
                analysis_content=None,
                status=VolunteerCategoryAnalysis.STATUS_FAILED,
                error_message=str(e)
            )
            
            return {
                "status": "error",
                "message": f"分析过程出错: {str(e)}",
                "error_detail": error_trace
            }