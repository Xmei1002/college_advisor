# app/services/volunteer/ai_college_specialty_service.py
from flask import current_app
from app.extensions import db, celery
from app.models.student_volunteer_plan import StudentVolunteerPlan, VolunteerCollege, VolunteerSpecialty
from app.models.user import User
from app.services.student.student_data_service import StudentDataService
from sqlalchemy.exc import SQLAlchemyError
import json
from app.services.ai.moonshot import MoonshotAI
from datetime import datetime, timezone

class AICollegeSpecialtyAnalysisService:
    """AI院校和专业解读服务类，处理所有与院校和专业相关的AI解析功能"""
    
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
            "teshu_text": college.get('teshu_text'),
            "uncode": college.get('uncode'),
            "min_tuition": college.get('min_tuition'),
            "max_tuition": college.get('max_tuition'),
            "volunteer_index": college.get('volunteer_index'),
            "subject_requirements": college.get('subject_requirements'),
            "specialties": []
        }
        
        # 添加专业信息
        for specialty in college.get('specialties', []):
            simplified_specialty = {
                "specialty_name": specialty.get('specialty_name'),
                "prediction_score": specialty.get('prediction_score'),
                "plan_number": specialty.get('plan_number'),
                "tuition": specialty.get('tuition'),
                "specialty_index": specialty.get('specialty_index'),
                "remarks": specialty.get('remarks'),
            }
            simplified_college["specialties"].append(simplified_specialty)
            
        return simplified_college
    
    @staticmethod
    def _simplify_specialty_for_ai(specialty, college_info=None):
        """
        简化单个专业信息用于AI分析
        
        :param specialty: 完整的专业信息
        :param college_info: 可选的院校信息，用于分析上下文
        :return: 简化后的专业信息
        """
        simplified_specialty = {
            "specialty_name": specialty.get('specialty_name'),
            "specialty_code": specialty.get('specialty_code'),
            "prediction_score": specialty.get('prediction_score'),
            "plan_number": specialty.get('plan_number'),
            "tuition": specialty.get('tuition'),
            "specialty_index": specialty.get('specialty_index'),
            "remarks": specialty.get('remarks'),
        }
        
        # 如果提供了院校信息，添加到上下文
        if college_info:
            simplified_specialty["college_context"] = {
                "college_name": college_info.get('college_name'),
                "prediction_score": college_info.get('prediction_score'),
                "area_name": college_info.get('area_name'),
                "school_type_text": college_info.get('school_type_text'),
                "tese_text": college_info.get('tese_text'),
                "nature": college_info.get('nature'),
                "teshu_text": college_info.get('teshu_text'),
                "plan_number": college_info.get('plan_number'),
            }
            
        return simplified_specialty
    
    @staticmethod
    def get_college_by_id(volunteer_college_id):
        """
        获取指定志愿院校的详细信息
        
        :param volunteer_college_id: 志愿院校ID
        :return: 院校详细信息
        """
        # 获取院校信息
        college = VolunteerCollege.query.get(volunteer_college_id)
        if not college:
            return None
            
        # 获取专业信息
        specialties = VolunteerSpecialty.query.filter_by(
            volunteer_college_id=volunteer_college_id
        ).order_by(VolunteerSpecialty.specialty_index).all()
        
        # 构建完整信息
        college_dict = college.to_dict()
        college_dict['specialties'] = [specialty.to_dict() for specialty in specialties]
        
        return college_dict
    
    @staticmethod
    def get_specialty_by_id(specialty_id):
        """
        获取指定专业的详细信息，包括所属院校
        
        :param specialty_id: 志愿专业ID
        :return: 专业详细信息及所属院校
        """
        # 获取专业信息
        specialty = VolunteerSpecialty.query.get(specialty_id)
        if not specialty:
            return None
            
        # 获取所属院校信息
        college = VolunteerCollege.query.get(specialty.volunteer_college_id)
        if not college:
            return None
            
        # 构建完整信息
        result = {
            'specialty': specialty.to_dict(),
            'college': college.to_dict()
        }
        
        return result
    
    @classmethod
    def analyzing_college(cls, user_info, college_json, temperature=0.3):
        """
        获取AI对院校的分析响应
        
        :param user_info: 用户信息
        :param college_json: 院校信息JSON
        :param temperature: 控制输出的随机性
        :return: AI的分析内容
        """
        
        # 实际调用AI分析
        res = MoonshotAI.analyzing_college(
            user_info=user_info,
            college_json=college_json
        )
        
        return res
    
    @classmethod
    def analyzing_specialty(cls, user_info, specialty_json, temperature=0.3):
        """
        获取AI对专业的分析响应
        
        :param user_info: 用户信息
        :param specialty_json: 专业信息JSON，包含院校上下文
        :param temperature: 控制输出的随机性
        :return: AI的分析内容
        """
        # 这里调用MoonshotAI进行专业分析
        # 实际调用AI分析
        res = MoonshotAI.analyzing_specialty(
            user_info=user_info,
            specialty_json=specialty_json
        )
        
        return res
    
    @staticmethod
    def update_college_analysis(volunteer_college_id, analysis_content):
        """
        更新院校的AI分析结果
        
        :param volunteer_college_id: 志愿院校ID
        :param analysis_content: 分析内容
        :return: 是否成功
        """
        try:
            college = VolunteerCollege.query.get(volunteer_college_id)
            if not college:
                return False
                
            college.ai_analysis = analysis_content
            college.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新院校分析结果失败: {str(e)}")
            return False
    
    @staticmethod
    def update_specialty_analysis(specialty_id, analysis_content):
        """
        更新专业的AI分析结果
        
        :param specialty_id: 志愿专业ID
        :param analysis_content: 分析内容
        :return: 是否成功
        """
        try:
            specialty = VolunteerSpecialty.query.get(specialty_id)
            if not specialty:
                return False
                
            specialty.ai_analysis = analysis_content
            specialty.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新专业分析结果失败: {str(e)}")
            return False
    
    @staticmethod
    def perform_college_analysis(volunteer_college_id):
        """
        执行院校分析的业务逻辑
        
        :param volunteer_college_id: 志愿院校ID
        :return: 分析结果
        """
        try:
            # 1. 获取院校信息
            college_data = AICollegeSpecialtyAnalysisService.get_college_by_id(volunteer_college_id)
            if not college_data:
                return {
                    "status": "error",
                    "message": f"未找到ID为{volunteer_college_id}的院校信息"
                }
            
            # 2. 获取学生信息
            plan_id = college_data.get('plan_id')
            student_id = StudentVolunteerPlan.query.get(plan_id).student_id
            user_info = StudentDataService.generate_student_profile_text(student_id)
            
            # 3. 简化院校信息用于AI分析
            simplified_college = AICollegeSpecialtyAnalysisService._simplify_college_for_ai(college_data)
            college_json = json.dumps(simplified_college, ensure_ascii=False)
            
            # 4. 调用AI分析
            analysis_result = AICollegeSpecialtyAnalysisService.analyzing_college(
                user_info=user_info,
                college_json=college_json
            )
            
            # 5. 存储分析结果
            success = AICollegeSpecialtyAnalysisService.update_college_analysis(
                volunteer_college_id=volunteer_college_id,
                analysis_content=analysis_result
            )
            
            if not success:
                return {
                    "status": "error",
                    "message": "存储院校分析结果失败"
                }
            
            # 6. 返回成功
            return {
                "status": "success",
                "message": "院校分析完成",
                "volunteer_college_id": volunteer_college_id,
                "analysis": analysis_result
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            current_app.logger.error(f"院校分析执行失败: {str(e)}\n{error_trace}")
            
            return {
                "status": "error",
                "message": f"分析过程出错: {str(e)}",
                "error_detail": error_trace
            }
    
    @staticmethod
    def perform_specialty_analysis(specialty_id):
        """
        执行专业分析的业务逻辑
        
        :param specialty_id: 志愿专业ID
        :return: 分析结果
        """
        try:
            # 1. 获取专业和院校信息
            data = AICollegeSpecialtyAnalysisService.get_specialty_by_id(specialty_id)
            if not data:
                return {
                    "status": "error",
                    "message": f"未找到ID为{specialty_id}的专业信息"
                }
            
            specialty_data = data.get('specialty')
            college_data = data.get('college')
            
            # 2. 获取学生信息
            plan_id = college_data.get('plan_id')
            student_id = StudentVolunteerPlan.query.get(plan_id).student_id
            user_info = StudentDataService.generate_student_profile_text(student_id)
            
            # 3. 简化专业信息用于AI分析
            simplified_specialty = AICollegeSpecialtyAnalysisService._simplify_specialty_for_ai(
                specialty_data, 
                college_data
            )
            specialty_json = json.dumps(simplified_specialty, ensure_ascii=False)
            
            # 4. 调用AI分析
            analysis_result = AICollegeSpecialtyAnalysisService.analyzing_specialty(
                user_info=user_info,
                specialty_json=specialty_json
            )
            
            # 5. 存储分析结果
            success = AICollegeSpecialtyAnalysisService.update_specialty_analysis(
                specialty_id=specialty_id,
                analysis_content=analysis_result
            )
            
            if not success:
                return {
                    "status": "error",
                    "message": "存储专业分析结果失败"
                }
            
            # 6. 返回成功
            return {
                "status": "success",
                "message": "专业分析完成",
                "specialty_id": specialty_id,
                "analysis": analysis_result
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            current_app.logger.error(f"专业分析执行失败: {str(e)}\n{error_trace}")
            
            return {
                "status": "error",
                "message": f"分析过程出错: {str(e)}",
                "error_detail": error_trace
            }