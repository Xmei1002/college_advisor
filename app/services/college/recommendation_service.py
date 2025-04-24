# app/services/college/recommendation_service.py
from app.core.recommendation.repository import CollegeRepository
from app.core.recommendation.score_classification import ScoreClassifier
from flask import current_app
from app import db
class RecommendationService:
    """院校推荐服务，组合数据访问和业务逻辑"""
    
    @staticmethod
    def get_colleges_by_category_and_group(student_score, subject_type, education_level, 
                                        category_id, group_id, student_subjects,
                                        area_ids=None, specialty_types=None, 
                                        mode='smart', page=1, per_page=20,
                                        tese_types=None, leixing_types=None, teshu_types=None,
                                        tuition_ranges=None, exclude_group_ids=None):
        """
        根据类别和志愿段获取院校专业组列表
        
        :param student_score: 学生分数
        :param subject_type: 科别（1-文科/历史组，2-理科/物理组）
        :param education_level: 学历层次（11-本科，12-专科）
        :param category_id: 类别ID（1-冲，2-稳，3-保）
        :param group_id: 志愿段ID（1-12，对应不同的志愿段）
        :param student_subjects: 学生选科情况，字典格式如{'wu': 1, 'hua': 1, 'sheng': 2, 'shi': 2, 'di': 2, 'zheng': 2}
        :param area_ids: 地区ID列表
        :param specialty_types: 专业类型ID列表
        :param mode: 分类模式（'smart','professional','free'）
        :param page: 页码，从1开始
        :param per_page: 每页记录数
        :param tese_types: 学校特色筛选列表
        :param leixing_types: 学校类型筛选列表
        :param teshu_types: 特殊类型筛选列表
        :param tuition_ranges: 学费范围列表，格式为[(min1, max1), (min2, max2), ...]
        :param exclude_group_ids: 需要排除的院校专业组ID集合
        :return: 查询结果和分页信息
        """
        # 参数预处理，确保area_ids和specialty_types为列表
        area_ids = area_ids or []
        specialty_types = specialty_types or []
        tese_types = tese_types or []
        leixing_types = leixing_types or []
        teshu_types = teshu_types or []
        exclude_group_ids = exclude_group_ids or set()
        tuition_ranges = tuition_ranges or []
        education_level = education_level or 11  # 默认本科

        current_app.logger.info(f"获取院校专业组列表: 学生分数={student_score}, 科别={subject_type}, 学历层次={education_level}, "
              f"类别ID={category_id}, 志愿段ID={group_id}, 学生选科={student_subjects}, "
              f"地区ID={area_ids}, 专业类型={specialty_types}, 模式={mode}, "
              f"每页记录数={per_page}, 学费范围={tuition_ranges}, 排除的专业组ID={exclude_group_ids}")
        
        
        # 1. 获取所有符合条件的专业组
        college_groups = CollegeRepository.get_college_groups_by_category(
            student_score=student_score,
            subject_type=subject_type,
            education_level=education_level,
            category_id=category_id,
            group_id=group_id,
            student_subjects=student_subjects,
            area_ids=area_ids,
            specialty_types=specialty_types,
            mode=mode,
            tese_types=tese_types,
            leixing_types=leixing_types,
            teshu_types=teshu_types,
            tuition_ranges=tuition_ranges  # 添加学费范围参数
        )
        
        # 1.1 过滤掉需要排除的院校专业组
        if exclude_group_ids:
            college_groups = [group for group in college_groups if group.cgid not in exclude_group_ids]
        
        # 计算总记录数
        total = len(college_groups)
        
        # 2. 按分差排序（分差越大排越前面）
        college_groups = sorted(college_groups, key=lambda x: x.score_diff, reverse=True)
        
        # 3. 内存分页
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        paginated_groups = college_groups[start_idx:end_idx]
        
        # 4. 获取专业组ID列表
        group_ids = [group.cgid for group in paginated_groups]
        
        # 5. 获取专业组历年数据
        group_history = CollegeRepository.get_college_group_history_by_ids(
            group_ids, subject_type, education_level
        )
        
        # 6. 根据专业组ID获取专业信息
        specialties = CollegeRepository.get_specialties_by_group_ids(
            group_ids, subject_type, education_level, student_subjects
        )
        
        # 7. 将专业信息按专业组分组
        specialties_by_group = {}
        for specialty in specialties:
            if specialty.cgid not in specialties_by_group:
                specialties_by_group[specialty.cgid] = []
            
            specialty_info = {
                'id': specialty.id,
                'spid': specialty.spid,
                'spname': specialty.spname,
                'spcode': specialty.spcode,
                'specialty_direction': specialty.zyfx,
                'tuition': specialty.tuitions,
                'prediction_score': specialty.yuce,
                'plan_number': specialty.csbplannum,
                'teacher': specialty.teacher,
                'doctor': specialty.doctor,
                'official': specialty.official,
            }
            specialties_by_group[specialty.cgid].append(specialty_info)
        
        # 对每个专业组内的专业按预测分数从低到高排序
        for cgid in specialties_by_group:
            specialties_by_group[cgid] = sorted(
                specialties_by_group[cgid],
                key=lambda x: x['prediction_score']
            )
            
        # 8. 组织最终结果
        result = []
        for group in paginated_groups:
            # 对于每个专业组，构造完整信息
            group_specialty_count = CollegeRepository.count_specialties_by_group_id(
                group.cgid, subject_type, education_level, student_subjects
            )
            
            # 计算分类
            category, group_name, recommendation_msg = ScoreClassifier.classify_by_score_diff(
                group.score_diff, education_level, mode
            )
            
            # 获取并转换特色、类型和特殊类型的文本描述
            tese_text = CollegeRepository.convert_code_to_text(group.tese, 'tese')
            leixing_text = CollegeRepository.convert_code_to_text(group.leixing, 'leixing')
            teshu_text = CollegeRepository.convert_code_to_text(group.teshu, 'teshu')
            
            # 获取专业组历年数据
            history_data_obj = group_history.get(group.cgid, {})
            history_data_array = []
            for year, data in history_data_obj.items():
                if data:  # 确保数据存在
                    # 创建一个新对象，将年份作为属性添加
                    year_data = {
                        "year": year,
                        **data  # 展开原始数据
                    }
                    history_data_array.append(year_data)

            # 可选：按年份排序（从新到旧）
            history_data_array.sort(key=lambda x: x["year"], reverse=True)

            # 计算扩建人数（2025年计划人数 - 2024年计划人数）
            plan_2025 = group.csbplannum or 0
            plan_2024 = history_data_obj.get('2024', {}).get('plan_number') or 0
            plan_increase = plan_2025 - plan_2024
            
            group_info = {
                'cgid': group.cgid,
                'cid': group.cid,
                'cname': group.cname,
                'uncode': group.uncode,
                'school_type': group.leixing,
                'school_type_text': leixing_text[0] if leixing_text else '',
                'school_nature': group.xingzhi == 1 and '公办' or '民办',
                'tese': group.tese,
                'tese_text': tese_text,
                'teshu': group.teshu,
                'teshu_text': teshu_text,
                'area_name': group.area_name,
                'group_name': group.cgname or '',
                'min_score': group.yuce,
                'score_diff': group.score_diff,
                'min_tuition': group.minxuefei,
                'max_tuition': group.maxxuefei,
                'plan_number': group.csbplannum,  # 专业组的计划人数，来自投档线记录
                'plan_increase': plan_increase,  # 添加扩建人数（25-24年计划人数差值）
                'specialty_count': group_specialty_count,
                'recommendation_level': category,
                'recommendation_group': group_name,
                'subject_requirements': {
                    'wu': group.wu,
                    'shi': group.shi,
                    'hua': group.hua,
                    'sheng': group.sheng,
                    'di': group.di,
                    'zheng': group.zheng
                },
                'specialties': specialties_by_group.get(group.cgid, []),
                'recommendation_msg': recommendation_msg,
                'history': history_data_array # 添加历年数据
            }
            result.append(group_info)
                
        # 9. 返回结果和分页信息
        pagination = {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
        return result, pagination

    @staticmethod
    def get_college_count_by_category_and_group(student_score, subject_type, education_level, 
                                            category_id, group_id, student_subjects,
                                            area_ids=None, specialty_types=None, 
                                            mode='smart', tese_types=None, leixing_types=None, teshu_types=None,
                                            tuition_ranges=None):
        """
        获取指定类别和志愿段的院校数量（优化性能的方法）
        
        :param student_score: 学生分数
        :param subject_type: 科别（1-文科/历史组，2-理科/物理组）
        :param education_level: 学历层次（11-本科，12-专科）
        :param category_id: 类别ID（1-冲，2-稳，3-保）
        :param group_id: 志愿段ID（1-12，对应不同的志愿段）
        :param student_subjects: 学生选科情况
        :param area_ids: 地区ID列表
        :param specialty_types: 专业类型ID列表
        :param mode: 分类模式（'smart','professional','free'）
        :param tese_types: 学校特色筛选列表
        :param leixing_types: 学校类型筛选列表
        :param teshu_types: 特殊类型筛选列表
        :param tuition_ranges: 学费范围列表
        :return: 符合条件的院校专业组数量
        """
        # 导入模型（避免循环导入）
        from app.models.zwh_xgk_fenshuxian_2025 import ZwhXgkFenshuxian2025
        from app.models.zwh_xgk_yuanxiao_2025 import ZwhXgkYuanxiao2025
        from app.models.zwh_areas import ZwhAreas
        from app.models.zwh_xgk_fenzu_2025 import ZwhXgkFenzu2025
        from app.core.recommendation.score_classification import ScoreClassifier
        
        # 参数预处理
        area_ids = area_ids or []
        specialty_types = specialty_types or []
        tese_types = tese_types or []
        leixing_types = leixing_types or []
        teshu_types = teshu_types or []
        tuition_ranges = tuition_ranges or []
        
        # 获取分差范围
        score_diff_range = ScoreClassifier.get_score_diff_range(
            category_id, group_id, education_level, mode
        )
        
        # 如果没有找到对应的分差范围，返回0
        if not score_diff_range:
            return 0
            
        min_diff, max_diff = score_diff_range
        
        # 直接进行COUNT查询，只计数而不获取完整数据
        query = db.session.query(
            db.func.count(db.distinct(ZwhXgkFenshuxian2025.cgid))
        ).join(
            ZwhXgkYuanxiao2025, 
            ZwhXgkFenshuxian2025.cid == ZwhXgkYuanxiao2025.cid
        ).join(
            ZwhAreas,
            ZwhXgkYuanxiao2025.aid == ZwhAreas.aid
        ).join(
            ZwhXgkFenzu2025,
            ZwhXgkFenshuxian2025.cgid == ZwhXgkFenzu2025.cgid
        ).filter(
            ZwhXgkFenshuxian2025.suid == subject_type,
            ZwhXgkFenshuxian2025.spid == 32767,  # 仅查询投档线记录
            ZwhXgkFenshuxian2025.newbid == education_level,
            ZwhXgkFenshuxian2025.yuce.isnot(None),
            (ZwhXgkFenshuxian2025.yuce - student_score).between(min_diff, max_diff)
        )
        
        # 添加地区筛选 - 考虑多个地区及其子地区
        if area_ids:
            # 收集所有选中地区及其子地区的ID
            all_area_ids = []
            for area_id in area_ids:
                # 获取当前地区及其所有子地区
                child_area_ids = CollegeRepository.get_all_child_areas(area_id)
                all_area_ids.extend(child_area_ids)
            
            # 去重
            all_area_ids = list(set(all_area_ids))
            
            # 如果有收集到地区ID，添加筛选条件
            if all_area_ids:
                query = query.filter(ZwhXgkYuanxiao2025.aid.in_(all_area_ids))
        
        # 添加专业类型筛选 - 与获取数据方法保持一致
        if specialty_types:
            # 子查询：查找包含任一指定专业类型的专业组
            subquery = db.session.query(ZwhXgkFenshuxian2025.cgid).filter(
                ZwhXgkFenshuxian2025.subclassid.in_(specialty_types),
                ZwhXgkFenshuxian2025.spid != 32767  # 排除投档线记录
            ).distinct().subquery()
            
            # 使用与获取数据方法相同的转换方式
            subquery_select = subquery.select()  # 显式转换为 select()
            query = query.filter(ZwhXgkFenshuxian2025.cgid.in_(subquery_select))
        
        # 添加学校特色筛选
        if tese_types:
            # 构建SQL条件以匹配任意一个特色类型
            tese_conditions = []
            for tese_type in tese_types:
                tese_conditions.append(ZwhXgkYuanxiao2025.tese.like(f'%{tese_type}%'))
            
            # 将所有条件用OR连接
            if tese_conditions:
                query = query.filter(db.or_(*tese_conditions))
        
        # 添加学校类型筛选
        if leixing_types:
            query = query.filter(ZwhXgkYuanxiao2025.leixing.in_(leixing_types))
        
        # 添加特殊类型筛选
        if teshu_types:
            # 构建SQL条件
            teshu_conditions = []
            for teshu_type in teshu_types:
                teshu_conditions.append(ZwhXgkYuanxiao2025.teshu.like(f'%{teshu_type}%'))
            
            if teshu_conditions:
                query = query.filter(db.or_(*teshu_conditions))
        
        # 添加选科匹配条件
        if student_subjects:
            # 遍历学生选科情况
            for subject_key, subject_value in student_subjects.items():
                if subject_value == 1:  # 学生选了该科目
                    continue  # 无需额外筛选
                elif subject_value == 2:  # 学生没选该科目
                    # 只能匹配专业对该科目无要求(值为2)的情况
                    query = query.filter(getattr(ZwhXgkFenzu2025, subject_key) == 2)
        
        # 添加学费范围筛选 - 与获取数据方法保持一致
        if tuition_ranges:
            # 构建学费筛选条件
            tuition_conditions = []
            for min_fee, max_fee in tuition_ranges:
                if max_fee is None:
                    # "X万以上"的情况
                    tuition_conditions.append(ZwhXgkFenzu2025.minxuefei >= min_fee)
                else:
                    # 匹配情况1：学校的最低学费在范围内
                    condition1 = db.and_(
                        ZwhXgkFenzu2025.minxuefei >= min_fee,
                        ZwhXgkFenzu2025.minxuefei <= max_fee
                    )
                    # 匹配情况2：学校的最高学费在范围内
                    condition2 = db.and_(
                        ZwhXgkFenzu2025.maxxuefei >= min_fee,
                        ZwhXgkFenzu2025.maxxuefei <= max_fee
                    )
                    # 匹配情况3：学校的学费范围完全包含所选范围
                    condition3 = db.and_(
                        ZwhXgkFenzu2025.minxuefei <= min_fee,
                        ZwhXgkFenzu2025.maxxuefei >= max_fee
                    )
                    # 将三种匹配情况以OR连接
                    tuition_conditions.append(db.or_(condition1, condition2, condition3))
            
            # 将所有学费范围条件以OR连接
            if tuition_conditions:
                query = query.filter(db.or_(*tuition_conditions))
        
        # 执行查询并直接返回数量
        return query.scalar()