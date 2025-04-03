# app/services/student/student_data_service.py
from app.models.studentProfile import Student
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_specialties_type import ZwhSpecialtiesType

class StudentDataService:
    """处理学生数据提取和转换的服务类"""
    
    @staticmethod
    def extract_college_recommendation_data(student_id):
        """
        从学生数据中提取用于院校推荐的关键信息
        
        :param student_id: 学生ID
        :return: 包含推荐所需数据的字典
        """
        # 1. 获取学生完整数据
        student = Student.query.get_or_404(student_id)
        academic_record = student.academic_record  # 假设已建立关联
        college_pref = student.college_preference  # 假设已建立关联
        career_pref = student.career_preference    # 假设已建立关联
        
        # 2. 提取学生分数
        student_score = StudentDataService._parse_score(academic_record.gaokao_total_score)
        
        # 3. 确定科别 (1-文科/历史组，2-理科/物理组)
        subject_type = StudentDataService._determine_subject_type(academic_record.selected_subjects)
        
        # 4. 解析学生选科情况
        student_subjects = StudentDataService._parse_subject_selection(academic_record.selected_subjects)
        
        # 5. 提取地区ID列表
        area_ids = []
        if college_pref and college_pref.preferred_locations:
            area_ids = StudentDataService._get_area_ids(college_pref.preferred_locations)
        
        # 6. 提取专业类型列表
        specialty_types = []
        if college_pref and college_pref.preferred_majors:
            specialty_types = StudentDataService._get_specialty_type_ids(college_pref.preferred_majors)
        
        education_level = 11 
        # 组织返回数据
        result = {
            'student_id': student.id,
            'student_score': student_score,
            'subject_type': subject_type,
            'education_level': education_level,
            'student_subjects': student_subjects,
            'area_ids': area_ids,
            'specialty_types': specialty_types,
        }
        
        return result
    
    @staticmethod
    def _parse_score(score_str):
        """解析分数字符串为整数"""
        if not score_str:
            return 0
        try:
            # 去除可能的非数字字符，如"分"
            cleaned_score = ''.join(c for c in score_str if c.isdigit() or c == '.')
            return int(float(cleaned_score))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _determine_subject_type(selected_subjects_str):
        """
        根据选科情况确定科别
        :return: 1-文科/历史组，2-理科/物理组
        """
        if not selected_subjects_str:
            return None
        
        subjects_lower = selected_subjects_str.lower()
        
        # 判断是文科还是理科
        if '历史' in subjects_lower:
            return 1
        elif '物理' in subjects_lower:
            return 2
    
    @staticmethod
    def _parse_subject_selection(selected_subjects_str):
        """
        解析选科情况为字典格式
        :return: 格式如{'wu': 1, 'hua': 1, 'sheng': 2, 'shi': 2, 'di': 2, 'zheng': 2}
        值为1表示必选，2表示无要求
        """
        # 默认所有科目为"无要求"
        subjects = {
            'wu': 2,    # 物理
            'shi': 2,   # 历史
            'hua': 2,   # 化学
            'sheng': 2, # 生物
            'di': 2,    # 地理
            'zheng': 2  # 政治
        }
        
        if not selected_subjects_str:
            return subjects
        
        subjects_lower = selected_subjects_str.lower()
        
        # 根据字符串中包含的科目名称设置为"必选"
        subject_mapping = {
            '物理': 'wu',
            '历史': 'shi',
            '化学': 'hua',
            '生物': 'sheng',
            '地理': 'di',
            '政治': 'zheng'
        }
        
        for cn_name, code in subject_mapping.items():
            if cn_name in subjects_lower:
                subjects[code] = 1
        
        return subjects
    
    @staticmethod
    def _get_area_ids(preferred_locations_str):
        """
        将地区名称字符串转换为地区ID列表
        :param preferred_locations_str: 逗号分隔的地区名称
        :return: 地区ID列表
        """
        if not preferred_locations_str:
            return []
        print(f"preferred_locations_str: {preferred_locations_str}")
        area_ids = []
        locations = [loc.strip() for loc in preferred_locations_str.split(',')]
        
        for location in locations:
            # 查询匹配的地区ID
            areas = ZwhAreas.query.filter(ZwhAreas.aname.like(f'%{location}%')).all()
            for area in areas:
                area_ids.append(area.aid)
        
        return area_ids
    
    @staticmethod
    def _get_specialty_type_ids(preferred_majors_str):
        """
        将专业名称字符串转换为专业类型ID列表
        :param preferred_majors_str: 逗号分隔的专业名称
        :return: 专业类型ID列表
        """
        if not preferred_majors_str:
            return []
        
        specialty_ids = []
        majors = [major.strip() for major in preferred_majors_str.split(',')]
        
        for major in majors:
            # 查询完全匹配的专业类型ID
            specialties = ZwhSpecialtiesType.query.filter(
                ZwhSpecialtiesType.sptname == major
            ).all()
            for specialty in specialties:
                specialty_ids.append(specialty.id)
        
        return specialty_ids
    

    @staticmethod
    def generate_student_profile_text(student_id):
        """
        生成学生完整信息的文本报告
        
        :param student_id: 学生ID
        :return: 格式化的文本报告
        """
        # 获取学生完整数据
        student = Student.query.get_or_404(student_id)
        academic_record = student.academic_record  # 假设已建立关联
        career_pref = getattr(student, 'career_preference', None)
        college_pref = getattr(student, 'college_preference', None)
        
        # 开始生成文本报告
        text_parts = []
        
        # -- 标题 --
        text_parts.append(f"学生个人档案 - {student.name}")
        text_parts.append("=" * 50)
        text_parts.append("")
        
        # -- 第一部分：基本信息 --
        text_parts.append("【基本信息】")
        text_parts.append(f"姓名：{student.name}")
        text_parts.append(f"性别：{student.gender}")
        text_parts.append(f"民族：{student.ethnicity or '未填写'}")
        text_parts.append(f"联系电话：{student.phone or '未填写'}")
        text_parts.append(f"微信/QQ：{student.wechat_qq or '未填写'}")
        text_parts.append(f"毕业学校：{student.school or '未填写'}")
        text_parts.append(f"户籍类型：{student.household_type or '未填写'}")
        text_parts.append(f"考生类型：{student.student_type or '未填写'}")
        text_parts.append(f"准考证号：{student.candidate_number or '未填写'}")
        text_parts.append("")
        
        # -- 家长信息 --
        text_parts.append("【家长信息】")
        if student.guardian1_name or student.guardian1_phone:
            text_parts.append(f"第一联系人：{student.guardian1_name or '未填写'} ({student.guardian1_phone or '未填写电话'})")
        else:
            text_parts.append("第一联系人：未填写")
            
        if student.guardian2_name or student.guardian2_phone:
            text_parts.append(f"第二联系人：{student.guardian2_name or '未填写'} ({student.guardian2_phone or '未填写电话'})")
        else:
            text_parts.append("第二联系人：未填写")
        text_parts.append("")
        
        # -- 身体情况 --
        text_parts.append("【身体情况】")
        text_parts.append(f"左眼视力：{student.left_eye_vision or '未检测'}")
        text_parts.append(f"右眼视力：{student.right_eye_vision or '未检测'}")
        text_parts.append(f"色觉情况：{student.color_vision or '未检测'}")
        text_parts.append(f"身高：{student.height or '未填写'} CM")
        text_parts.append(f"体重：{student.weight or '未填写'} KG")
        text_parts.append(f"是否失信考生：{'是' if student.is_discredited else '否'}")
        if student.is_discredited and student.discredit_reason:
            text_parts.append(f"失信原因：{student.discredit_reason}")
        text_parts.append("")
        
        # -- 第二部分：学业记录 --
        text_parts.append("【学业情况】")
        if academic_record:
            text_parts.append(f"外语语种：{student.foreign_language or '未填写'}")
            text_parts.append(f"高考选科：{academic_record.selected_subjects or '未填写'}")
            text_parts.append(f"高考总分：{academic_record.gaokao_total_score or '未填写'}")
            text_parts.append(f"高考位次：{academic_record.gaokao_ranking or '未填写'}")
            text_parts.append(f"标准分数：{academic_record.standard_score or '未填写'}")
            if academic_record.bonus_type:
                text_parts.append(f"加分类型：{academic_record.bonus_type}")
            
            # 添加分科成绩
            text_parts.append("\n【分科成绩】")
            subject_scores = [
                ("语文", academic_record.chinese_score),
                ("数学", academic_record.math_score),
                ("外语", academic_record.foreign_lang_score),
                ("物理", academic_record.physics_score),
                ("历史", academic_record.history_score),
                ("化学", academic_record.chemistry_score),
                ("生物", academic_record.biology_score),
                ("地理", academic_record.geography_score),
                ("政治", academic_record.politics_score)
            ]
            
            for subject, score in subject_scores:
                if score:
                    text_parts.append(f"{subject}：{score}")
            
            # 添加模考成绩
            text_parts.append("\n【模考成绩】")
            if academic_record.mock_exam1_score:
                text_parts.append(f"第一次模考：{academic_record.mock_exam1_score}")
            if academic_record.mock_exam2_score:
                text_parts.append(f"第二次模考：{academic_record.mock_exam2_score}")
            if academic_record.mock_exam3_score:
                text_parts.append(f"第三次模考：{academic_record.mock_exam3_score}")
        else:
            text_parts.append("暂无学业记录信息")
        text_parts.append("")
        
        # 优势和劣势科目
        text_parts.append("【科目情况】")
        text_parts.append(f"优势科目：{student.strong_subjects or '未填写'}")
        text_parts.append(f"劣势科目：{student.weak_subjects or '未填写'}")
        text_parts.append("")
        
        # -- 第三部分：就业倾向 --
        text_parts.append("【就业倾向】")
        if career_pref:
            text_parts.append(f"就业发展方向：{career_pref.career_direction or '未填写'}")
            text_parts.append(f"学术学位偏好：{career_pref.academic_preference or '未填写'}")
            text_parts.append(f"公务员意向：{career_pref.civil_service_preference or '未填写'}")
            text_parts.append(f"就业地区：{career_pref.employment_location or '未填写'}")
            text_parts.append(f"收入预期：{career_pref.income_expectation or '未填写'}")
            text_parts.append(f"工作稳定性要求：{career_pref.work_stability or '未填写'}")
        else:
            text_parts.append("暂无就业倾向信息")
        text_parts.append("")
        
        # -- 第四部分：志愿填报意向 --
        text_parts.append("【志愿填报意向】")
        if college_pref:
            # 处理逗号分隔的列表
            if college_pref.preferred_locations:
                locations = college_pref.preferred_locations.split(',')
                text_parts.append(f"意向地域：{', '.join(locations)}")
            else:
                text_parts.append("意向地域：未填写")
                
            text_parts.append(f"学费范围：{college_pref.tuition_range or '未填写'}")
            
            if college_pref.preferred_majors:
                majors = college_pref.preferred_majors.split(',')
                text_parts.append(f"意向专业：{', '.join(majors)}")
            else:
                text_parts.append("意向专业：未填写")
                
            if college_pref.school_types:
                types = college_pref.school_types.split(',')
                text_parts.append(f"学校类型：{', '.join(types)}")
            else:
                text_parts.append("学校类型：未填写")
                
            if college_pref.preferred_schools:
                schools = college_pref.preferred_schools.split(',')
                text_parts.append(f"意向学校：{', '.join(schools)}")
            else:
                text_parts.append("意向学校：未填写")
                
            text_parts.append(f"填报策略：{college_pref.strategy or '未填写'}")
            
            if college_pref.application_preference:
                text_parts.append("\n【报考倾向详情】")
                text_parts.append(college_pref.application_preference)
        else:
            text_parts.append("暂无志愿填报意向信息")
        
        # 附加信息
        text_parts.append("")
        text_parts.append("=" * 50)
        text_parts.append(f"档案创建时间：{student.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        text_parts.append(f"最后更新时间：{student.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 合并所有文本部分
        return "\n".join(text_parts)