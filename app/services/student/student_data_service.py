# app/services/student/student_data_service.py
from app.models.studentProfile import Student
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_specialties_type import ZwhSpecialtiesType
from app.models.zwh_xgk_picixian import ZwhXgkPicixian

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
        academic_record = student.academic_record  # 已建立关联
        college_pref = student.college_preference  # 已建立关联
        # 注意：career_preference已合并到college_preference中
        
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

        # 7. 获取模考分数
        mock_exam_score = StudentDataService._parse_score(academic_record.mock_exam_score)

        # 8. 提取学费范围
        tuition_ranges = []
        if college_pref and college_pref.tuition_range:
            tuition_ranges = StudentDataService._parse_tuition_range(college_pref.tuition_range)
        
        # 9. 确定教育层次 (11-本科，12-专科)
        education_level = StudentDataService._determine_education_level(
            student_score if (student_score and student_score > 0) else mock_exam_score,
            subject_type, 
        )
        # print('学历层次', education_level)
        # 组织返回数据
        result = {
            'student_id': student.id,
            'student_score': student_score,
            'subject_type': subject_type,
            'education_level': education_level,
            'student_subjects': student_subjects,
            'area_ids': area_ids,
            'specialty_types': specialty_types,
            'mock_exam_score': mock_exam_score,
            'tuition_ranges': tuition_ranges 
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
        # print(f"preferred_locations_str: {preferred_locations_str}")
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
    def _determine_education_level(student_score, subject_type, province_id=None):
        """
        根据学生分数和科别判断适合的教育层次
        
        :param student_score: 学生高考分数
        :param subject_type: 科别(1-文科/历史组，2-理科/物理组)
        :param province_id: 省份ID
        :return: 教育层次(11-本科，12-专科)
        """
        # 默认为本科
        default_level = 11
    
        try:
            # 查询最新年份的数据
            latest_year = '2025'
            
            if not latest_year:
                return default_level
            
            # 构建查询条件
            query = ZwhXgkPicixian.query.filter(
                ZwhXgkPicixian.dyear == latest_year,
                ZwhXgkPicixian.suid == subject_type,
                ZwhXgkPicixian.newbid == 11  # 查询本科批次线
            )
            
            # 如果有省份信息，添加省份筛选
            if province_id:
                query = query.filter(ZwhXgkPicixian.aid == province_id)
            
            # 获取本科批次线
            cutoff_record = query.order_by(ZwhXgkPicixian.dscore.desc()).first()
            
            # 如果找不到适用的分数线记录，使用默认值
            if not cutoff_record or not cutoff_record.dscore:
                return default_level
            
            # 比较学生分数与批次线
            if student_score >= float(cutoff_record.dscore):
                return 11  # 本科
            else:
                return 12  # 专科
                
        except Exception as e:
            # 出现异常时记录日志并返回默认值
            return default_level

    @staticmethod
    def _parse_tuition_range(tuition_range_str):
        """
        解析学费范围字符串为具体的数值范围，支持中文数字（一、二、三等）+万
        
        :param tuition_range_str: 学费范围字符串，如"1-2万,2-3万"或"一万-二万,二万-三万"
        :return: 学费范围列表，格式为[(min1, max1), (min2, max2), ...]
        """
        if not tuition_range_str:
            return []
        
        # 中文数字映射
        chinese_num_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '两': 2  # 特殊处理"两"
        }
        
        # 简化的中文数字转换，只处理单个数字
        def convert_to_number(value_str):
            # 如果是中文数字，转换为阿拉伯数字
            if value_str in chinese_num_map:
                return chinese_num_map[value_str]
            # 否则尝试直接转换为浮点数
            try:
                return float(value_str)
            except (ValueError, TypeError):
                return 0
        
        result = []
        ranges = [r.strip() for r in tuition_range_str.split(',')]
        
        for range_str in ranges:
            # 统一替换中文"到"为"-"
            range_str = range_str.replace('到', '-')
            
            if "万以内" in range_str:
                # 处理"X万以内"的情况
                try:
                    value_str = range_str.replace('万以内', '').strip()
                    max_value = convert_to_number(value_str) * 10000
                    result.append((0, int(max_value)))
                except (ValueError, TypeError):
                    continue
            elif "万以上" in range_str:
                # 处理"X万以上"的情况
                try:
                    value_str = range_str.replace('万以上', '').strip()
                    min_value = convert_to_number(value_str) * 10000
                    result.append((int(min_value), None))
                except (ValueError, TypeError):
                    continue
            elif "-" in range_str:
                # 处理"X-Y万"的情况
                try:
                    parts = range_str.replace('万', '').split('-')
                    min_str = parts[0].strip()
                    max_str = parts[1].strip()
                    
                    min_value = convert_to_number(min_str) * 10000
                    max_value = convert_to_number(max_str) * 10000
                    result.append((int(min_value), int(max_value)))
                except (ValueError, TypeError, IndexError):
                    continue
        
        return result

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
        college_pref = getattr(student, 'college_preference', None)
        # 注意：career_preference已合并到college_preference中
        
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
        text_parts.append(f"政治面貌：{student.political_status or '未填写'}")  # 新增政治面貌
        text_parts.append(f"出生日期：{student.birth_date.strftime('%Y-%m-%d') if student.birth_date else '未填写'}")  # 新增出生日期
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
            relation1 = f"({student.guardian1_relation})" if student.guardian1_relation else ""  # 新增关系
            text_parts.append(f"第一联系人：{student.guardian1_name or '未填写'}{relation1} ({student.guardian1_phone or '未填写电话'})")
        else:
            text_parts.append("第一联系人：未填写")
            
        if student.guardian2_name or student.guardian2_phone:
            relation2 = f"({student.guardian2_relation})" if student.guardian2_relation else ""  # 新增关系
            text_parts.append(f"第二联系人：{student.guardian2_name or '未填写'}{relation2} ({student.guardian2_phone or '未填写电话'})")
        else:
            text_parts.append("第二联系人：未填写")
        text_parts.append("")
        
        # -- 身体情况 --
        text_parts.append("【身体情况】")
        text_parts.append(f"左眼视力：{student.left_eye_vision or '未检测'}")
        text_parts.append(f"右眼视力：{student.right_eye_vision or '未检测'}")
        text_parts.append(f"色觉情况：{student.color_vision or '未检测'}")
        text_parts.append(f"嗅觉情况：{student.smell_condition or '未检测'}")  # 新增嗅觉情况
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
            if academic_record.bonus_detail:  # 新增加分情况详细说明
                text_parts.append(f"加分情况：{academic_record.bonus_detail}")
            
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
            text_parts.append(f"【模考成绩】：{academic_record.mock_exam_score}")
        else:
            text_parts.append("暂无学业记录信息")
        text_parts.append("")
        
        # 优势和劣势科目
        text_parts.append("【科目情况】")
        text_parts.append(f"优势科目：{student.strong_subjects or '未填写'}")
        text_parts.append(f"劣势科目：{student.weak_subjects or '未填写'}")
        text_parts.append("")
        
        # -- 第三部分：就业倾向与报考意向 (已合并) --
        text_parts.append("【就业倾向与志愿填报意向】")
        if college_pref:
            # 就业倾向信息（从CollegePreference获取）
            text_parts.append(f"就业发展方向：{college_pref.career_direction or '未填写'}")
            text_parts.append(f"公务员意向：{college_pref.civil_service_preference or '未填写'}" if hasattr(college_pref, 'civil_service_preference') else "")
            text_parts.append(f"就业地区偏好：{college_pref.employment_location or '未填写'}" if hasattr(college_pref, 'employment_location') else "")
            
            # 志愿填报意向信息
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
            text_parts.append(f"家庭背景：{college_pref.family_background or '未填写'}")
            # 志愿梯度策略相关
            text_parts.append(f"志愿梯度策略：{college_pref.volunteer_gradient_strategy or '未填写'}")
            if college_pref.volunteer_gradient_strategy == '自由设置' and college_pref.custom_gradient_counts:
                gradient_counts = college_pref.custom_gradient_counts
                if isinstance(gradient_counts, str):
                    try:
                        import json
                        gradient_counts = json.loads(gradient_counts)
                    except:
                        gradient_counts = {}
                text_parts.append(f"自定义梯度设置：冲刺志愿{gradient_counts.get('chasing', 0)}个，稳妥志愿{gradient_counts.get('stable', 0)}个，保底志愿{gradient_counts.get('safe', 0)}个")
                
            text_parts.append(f"报考批次：{college_pref.application_batch or '未填写'}")
            
            # 报考限制信息
            text_parts.append("\n【报考限制条件】")
            text_parts.append(f"接受不可转专业中外合办专业：{'是' if college_pref.accept_nonchangeable_major else '否'}")
            text_parts.append(f"具备美术基础：{'是' if college_pref.has_art_foundation else '否'}")
            text_parts.append(f"接受大学期间需出国就读：{'是' if college_pref.accept_overseas_study else '否'}")
            text_parts.append(f"接受学费刺客专业：{'是' if college_pref.accept_high_fee_increase else '否'}")
            text_parts.append(f"接受在两个城市上学安排：{'是' if college_pref.accept_dual_city_arrangement else '否'}")
            
            if college_pref.application_preference:
                text_parts.append("\n【报考倾向详情】")
                text_parts.append(college_pref.application_preference)
        else:
            text_parts.append("暂无志愿填报意向信息")
        
        # 合并所有文本部分
        return "\n".join(text_parts)
    
    @staticmethod
    def generate_student_data_snapshot(student_id):
        """
        生成学生数据快照，包含生成志愿方案所需的所有信息
        所有键使用中文标签便于直接展示
        
        :param student_id: 学生ID
        :return: 包含所有相关学生信息的字典，键为中文标签
        """
        # 获取学生数据
        student = Student.query.get_or_404(student_id)
        academic_record = student.academic_record
        college_pref = student.college_preference
        
        # 获取目前用于推荐的数据
        recommendation_data = StudentDataService.extract_college_recommendation_data(student_id)
        
        # 组织快照数据（使用中文键）
        snapshot = {
            '学生ID': student_id,
            '姓名': student.name,
            '高考总分': academic_record.gaokao_total_score or '',
            '科别': '文科' if recommendation_data['subject_type'] == 1 else '理科',
            '教育层次': '本科' if recommendation_data['education_level'] == 11 else '专科',
            '选考科目': academic_record.selected_subjects or '',
            '意向地域': college_pref.preferred_locations if college_pref else '',
            '意向专业': college_pref.preferred_majors if college_pref else '',
            '学费范围': college_pref.tuition_range if college_pref else '',
            '志愿梯度策略': college_pref.volunteer_gradient_strategy if college_pref else '',
            '报考批次': college_pref.application_batch if college_pref else '',
            '就业方向': college_pref.career_direction if college_pref else '',
            '模考成绩': academic_record.mock_exam_score or ''
            # 以下是原始数据，用于比较变化，保持与extract_college_recommendation_data一致的格式
            # '_原始数据': recommendation_data
        }
        
        return snapshot