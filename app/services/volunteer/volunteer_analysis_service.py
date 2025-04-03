# app/services/volunteer/volunteer_analysis_service.py

class AIVolunteerAnalysisService:
    """AI志愿解读服务类，专门处理所有与志愿填报相关的AI解析功能"""
  
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
            "college_id": college.get('college_id'),
            "college_name": college.get('college_name'),
            "volunteer_index": college.get('volunteer_index'),
            "category_id": college.get('category_id'),
            "group_id": college.get('group_id'),
            "score_diff": college.get('score_diff'),
            "prediction_score": college.get('prediction_score'),
            "area_name": college.get('area_name'),
            "school_type_text": college.get('school_type_text'),
            "tese_text": college.get('tese_text'),
            "min_tuition": college.get('min_tuition'),
            "max_tuition": college.get('max_tuition'),
        }
        
        # 提取精简的专业信息
        simplified_specialties = []
        for specialty in college.get('specialties', []):
            simplified_specialty = {
                "specialty_id": specialty.get('specialty_id'),
                "specialty_name": specialty.get('specialty_name'),
                "specialty_index": specialty.get('specialty_index'),
                "prediction_score": specialty.get('prediction_score'),
                "plan_number": specialty.get('plan_number'),
                "tuition": specialty.get('tuition'),
            }
            simplified_specialties.append(simplified_specialty)
        
        simplified_college['specialties'] = simplified_specialties
        return simplified_college