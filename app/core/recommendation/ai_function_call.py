from app.extensions import db
from app.models.zwh_xgk_zhuanye_2025 import ZwhXgkZhuanye2025
# 导入模型（避免循环导入）
from app.models.zwh_xgk_fenshuxian_2025 import ZwhXgkFenshuxian2025
from app.models.zwh_xgk_fenshuxian_2024 import ZwhXgkFenshuxian2024
from app.models.zwh_xgk_fenshuxian_2023 import ZwhXgkFenshuxian2023
from app.models.zwh_xgk_fenshuxian_2022 import ZwhXgkFenshuxian2022
from app.models.zwh_xgk_fenshuxian_2021 import ZwhXgkFenshuxian2021
from app.models.zwh_xgk_yuanxiao_2025 import ZwhXgkYuanxiao2025
from app.models.zwh_xgk_picixian import ZwhXgkPicixian
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_xgk_fenzu_2025 import ZwhXgkFenzu2025
from app.core.recommendation.score_classification import ScoreClassifier
from app.core.recommendation.repository import CollegeRepository
from app.services.student.student_data_service import StudentDataService


def get_college_detail_by_name(arguments):
    """
    根据大学名称查询大学详细信息，包括基本信息、专业组、专业和历年分数线
    
    :param school_name: 大学名称，用于模糊匹配
    :param subject_type: 科别（1-文科/历史组，2-理科/物理组），不指定则返回所有科别
    :param education_level: 学历层次（11-本科，12-专科），不指定则返回所有层次
    :return: 大学详细信息
    """
    school_name = arguments['school_full_name']
    print('大学名称',school_name)
    # 基础查询 - 获取大学基本信息
    college_query = db.session.query(
        ZwhXgkYuanxiao2025.cid,          # 学校ID
        ZwhXgkYuanxiao2025.cname,        # 学校名称
        ZwhXgkYuanxiao2025.uncode,       # 学校代码
        ZwhXgkYuanxiao2025.leixing,      # 学校类型
        ZwhXgkYuanxiao2025.xingzhi,      # 学校性质
        ZwhXgkYuanxiao2025.tese,         # 学校特色
        ZwhXgkYuanxiao2025.teshu,        # 特殊类型
        ZwhXgkYuanxiao2025.minxuefei,    # 最低学费
        ZwhXgkYuanxiao2025.maxxuefei,    # 最高学费
        ZwhXgkYuanxiao2025.baoyan,       # 保研情况
        ZwhAreas.aname.label('area_name'),  # 地区名称
        ZwhAreas.aid.label('area_id')       # 地区ID
    ).join(
        ZwhAreas,
        ZwhXgkYuanxiao2025.aid == ZwhAreas.aid
    ).filter(
        ZwhXgkYuanxiao2025.cname.like(f'%{school_name}%')
    )
    
    # 执行查询获取大学信息
    college_result = college_query.first()
    print('执行查询获取大学信息', college_result)
    # 如果没有找到大学，返回空结果
    if not college_result:
        return None
    
    # 处理大学基本信息
    college_id = college_result.cid
    
    # 获取地区完整路径
    area_path = CollegeRepository.get_complete_area_path(college_result.area_id)
    
    # 组合地区名称成一个完整字符串，跳过国家级（索引0）
    full_area_name = college_result.area_name
    if len(area_path) > 1:
        # 从省级开始（索引1）
        path_names = [area['aname'] for area in area_path[1:]]
        full_area_name = ''.join(path_names)
    
    # 获取并转换特色、类型和特殊类型的文本描述
    tese_text = CollegeRepository.convert_code_to_text(college_result.tese, 'tese')
    leixing_text = CollegeRepository.convert_code_to_text(college_result.leixing, 'leixing')
    teshu_text = CollegeRepository.convert_code_to_text(college_result.teshu, 'teshu')
    
    # 构建大学基本信息
    college_info = {
        'cname': college_result.cname,
        'school_type_text': leixing_text[0] if leixing_text else '',
        'school_nature': college_result.xingzhi == 1 and '公办' or '民办',
        'tese_text': tese_text,
        'teshu_text': teshu_text,
        'area_name': full_area_name,
        'min_tuition': college_result.minxuefei,
        'max_tuition': college_result.maxxuefei,
        'baoyan': college_result.baoyan,
        'college_groups': []
    }
    
    # 查询该大学的所有专业组
    group_query = db.session.query(
        ZwhXgkFenzu2025.cgid,           # 专业组ID
        ZwhXgkFenzu2025.newbid,         # 批次
        ZwhXgkFenzu2025.newsuid,        # 科别
        ZwhXgkFenzu2025.cgname,         # 专业组名称
        ZwhXgkFenzu2025.wu,             # 物理要求
        ZwhXgkFenzu2025.shi,            # 历史要求
        ZwhXgkFenzu2025.hua,            # 化学要求
        ZwhXgkFenzu2025.sheng,          # 生物要求
        ZwhXgkFenzu2025.di,             # 地理要求
        ZwhXgkFenzu2025.zheng,          # 政治要求
        ZwhXgkFenzu2025.minxuefei,      # 最低学费
        ZwhXgkFenzu2025.maxxuefei       # 最高学费
    ).filter(
        ZwhXgkFenzu2025.newcid == college_id
    )
    
    
    # 执行查询获取专业组信息
    group_results = group_query.all()
    
    # 获取所有专业组ID
    group_ids = [group.cgid for group in group_results]
    
    # 获取所有专业组的历年投档线数据
    history_data = {}
    if group_ids:
        for subj_type in [1, 2]:  # 1-文科/历史组，2-理科/物理组
            for edu_level in [11, 12]:  # 11-本科，12-专科
                # 获取该科别和教育层次下的历年数据
                temp_history = CollegeRepository.get_college_group_history_by_ids(
                    group_ids, subj_type, edu_level
                )
                # 合并数据
                history_data.update(temp_history)
    
    # 处理每个专业组的信息
    for group in group_results:
        group_id = group.cgid
        
        # 查询该专业组的2025年投档线
        line_query = db.session.query(
            ZwhXgkFenshuxian2025.yuce,       # 预测分数
            ZwhXgkFenshuxian2025.csbplannum  # 计划人数
        ).filter(
            ZwhXgkFenshuxian2025.cgid == group_id,
            ZwhXgkFenshuxian2025.spid == 32767  # 投档线记录
        )
        
        # 执行查询获取投档线信息
        line_result = line_query.first()
        prediction_score = line_result.yuce if line_result else None
        plan_number = line_result.csbplannum if line_result else None
        
        # 获取专业组下的所有专业
        specialties = []
        if group_id:
            # 查询该专业组的所有专业
            specialties_result = CollegeRepository.get_specialties_by_group_id(group_id)
            specialties = specialties_result  # 直接使用返回的结果
        
        # 构建专业组信息
        group_info = {
            'group_name': group.cgname,
            'prediction_score': prediction_score,
            'plan_number': plan_number,
            # 'min_tuition': group.minxuefei,
            # 'max_tuition': group.maxxuefei,
            # 'subject_requirements': {
            #     'wu': group.wu,
            #     'shi': group.shi,
            #     'hua': group.hua,
            #     'sheng': group.sheng,
            #     'di': group.di,
            #     'zheng': group.zheng
            # },
            'specialties': specialties,
            'history': history_data.get(group_id, {})  # 添加历年数据
        }
        
        # 添加到大学信息中
        college_info['college_groups'].append(group_info)
    
    return college_info

def get_colleges_by_major_names(arguments):
    """
    根据专业名称列表查询提供这些专业的大学及其录取情况
    
    :param arguments: 包含以下参数的字典:
        - major_names: 专业名称列表，用于模糊匹配
        - student_id: 学生ID，用于获取学生数据
    :return: 包含学生信息和大学列表的字典
    """
    major_names = arguments.get('major_names', [])
    student_id = arguments.get('student_id', None)
    
    # 初始化返回结果结构
    result = {
        'student_info': None,
        'colleges': []
    }
    
    # 如果没有提供专业名称，直接返回空结果
    if not major_names:
        return result
    
    # 获取学生数据
    student_data = None
    student_score = 0
    subject_type = None
    education_level = None
    student_subjects = None
    area_ids = None
    tuition_ranges = None
    
    if student_id:
        student_data = StudentDataService.extract_college_recommendation_data(student_id)
        # 使用高考分数，如果没有则使用模考分数
        student_score = student_data.get('student_score', 0)
        if student_score is None or student_score == 0:
            student_score = student_data.get('mock_exam_score', 0) or 0
        
        subject_type = student_data.get('subject_type')
        education_level = student_data.get('education_level')
        student_subjects = student_data.get('student_subjects', {})
        area_ids = student_data.get('area_ids', [])
        tuition_ranges = student_data.get('tuition_ranges', [])
        
        # 添加学生信息到返回结果
        result['student_info'] = {
            'student_score': student_score,
            'subject_type': subject_type,
            'education_level': education_level,
            'student_subjects': student_subjects,
            'tuition_ranges': tuition_ranges
        }
    
    # 1. 查询匹配的专业
    major_conditions = []
    for major_name in major_names:
        major_conditions.append(ZwhXgkZhuanye2025.spname.like(f'%{major_name}%'))
    
    if not major_conditions:
        return result
    
    major_query = db.session.query(
        ZwhXgkZhuanye2025.spid,  # 专业ID
        ZwhXgkZhuanye2025.spname  # 专业名称
    ).filter(db.or_(*major_conditions))
    
    # 执行查询获取专业ID
    major_results = major_query.all()
    
    # 如果没有找到匹配的专业，返回空结果
    if not major_results:
        return result
    
    # 获取匹配专业的ID
    major_ids = [major.spid for major in major_results]
    
    # 2. 构建大学专业查询
    # 基础查询 - 查询提供这些专业的大学和录取情况
    query = db.session.query(
        ZwhXgkFenshuxian2025.id,          # 分数线记录ID
        ZwhXgkFenshuxian2025.cgid,        # 专业组ID
        ZwhXgkFenshuxian2025.cid,         # 学校ID
        ZwhXgkYuanxiao2025.cname,         # 学校名称
        ZwhXgkYuanxiao2025.uncode,        # 学校代码
        ZwhAreas.aname.label('area_name'),# 地区名称
        ZwhXgkFenshuxian2025.spid,        # 专业ID
        ZwhXgkFenshuxian2025.spname,      # 专业名称
        ZwhXgkFenshuxian2025.spcode,      # 专业代码
        ZwhXgkFenshuxian2025.suid,        # 科别(文/理)
        ZwhXgkFenshuxian2025.newbid,      # 批次(本科/专科)
        ZwhXgkFenshuxian2025.yuce,        # 预测分数
        ZwhXgkFenshuxian2025.tuitions,    # 学费
        ZwhXgkFenshuxian2025.csbplannum,  # 计划人数
        (ZwhXgkFenshuxian2025.yuce - student_score).label('score_diff')  # 分数差
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
        ZwhXgkFenshuxian2025.spid.in_(major_ids),
        ZwhXgkFenshuxian2025.spid != 32767,  # 排除投档线记录
        ZwhXgkFenshuxian2025.yuce.isnot(None)
    )
    
    # 添加分数范围筛选 (12 到 -40)
    max_diff = 12
    min_diff = -40
    query = query.filter(
        (ZwhXgkFenshuxian2025.yuce - student_score).between(min_diff, max_diff)
    )
    
    # 添加科别筛选
    if subject_type:
        query = query.filter(ZwhXgkFenshuxian2025.suid == subject_type)
    
    # 添加学历层次筛选
    if education_level:
        query = query.filter(ZwhXgkFenshuxian2025.newbid == education_level)
    
    # 添加地区筛选
    if area_ids:
        # 收集所有选中地区及其子地区的ID
        all_area_ids = []
        for area_id in area_ids:
            child_area_ids = CollegeRepository.get_all_child_areas(area_id)
            all_area_ids.extend(child_area_ids)
        
        # 去重
        all_area_ids = list(set(all_area_ids))
        
        if all_area_ids:
            query = query.filter(ZwhXgkYuanxiao2025.aid.in_(all_area_ids))
    
    # 添加选科匹配条件
    if student_subjects:
        for subject_key, subject_value in student_subjects.items():
            if subject_value == 1:  # 学生选了该科目
                continue  # 无需额外筛选
            elif subject_value == 2:  # 学生没选该科目
                # 只能匹配专业对该科目无要求(值为2)的情况
                query = query.filter(getattr(ZwhXgkFenzu2025, subject_key) == 2)
    
    # 添加学费范围筛选
    if tuition_ranges:
        tuition_conditions = []
        for min_fee, max_fee in tuition_ranges:
            if max_fee is None:
                # "X万以上"的情况
                tuition_conditions.append(ZwhXgkFenshuxian2025.tuitions >= min_fee)
            else:
                # 学费在范围内
                tuition_conditions.append(
                    db.and_(
                        ZwhXgkFenshuxian2025.tuitions >= min_fee,
                        ZwhXgkFenshuxian2025.tuitions <= max_fee
                    )
                )
        
        if tuition_conditions:
            query = query.filter(db.or_(*tuition_conditions))
    
    subquery = query.with_entities(ZwhXgkFenshuxian2025.cid).distinct().limit(20).subquery()
    subquery_select = subquery.select()  # 显式转换为select()
    query = query.filter(ZwhXgkFenshuxian2025.cid.in_(subquery_select))
    
    # 执行查询
    results = query.all()
    
    # 按大学ID分组处理结果
    colleges_by_id = {}
    for college in results:
        cid = college.cid
        
        # 如果大学ID不在字典中，添加基本信息
        if cid not in colleges_by_id:
            # 获取地区完整路径
            area_path = CollegeRepository.get_complete_area_path(ZwhXgkYuanxiao2025.query.get(cid).aid)
            area_name = college.area_name
            
            # 从省级开始组合地区名称
            if len(area_path) > 1:
                path_names = [area['aname'] for area in area_path[1:]]
                area_name = ''.join(path_names)
            
            colleges_by_id[cid] = {
                'cid': cid,
                'cname': college.cname,
                'uncode': college.uncode,
                'area_name': area_name,
                'majors': []
            }
        
        # 添加专业信息
        if college.spid and college.spid != 32767:  # 排除投档线记录
            major_info = {
                'id': college.id,
                'spid': college.spid,
                'spname': college.spname,
                'spcode': college.spcode,
                'prediction_score': college.yuce,
                'score_diff': college.score_diff,
                'tuition': college.tuitions,
                'plan_number': college.csbplannum
            }
            colleges_by_id[cid]['majors'].append(major_info)
    
    # 将大学字典转换为列表
    result['colleges'] = list(colleges_by_id.values())
    
    # 按学校名称排序
    result['colleges'].sort(key=lambda x: x['cname'])
    
    return result

def get_colleges_by_location(arguments):
    """
    根据地域名称获取学校列表
    
    :param arguments: 包含以下参数的字典:
        - location_names: 地域名称列表，如["北京", "上海"]
        - student_id: 学生ID，用于获取学生数据
    :return: 包含学生信息和大学列表的字典
    """
    
    location_names = arguments.get('location_names', [])
    student_id = arguments.get('student_id', None)
    
    # 初始化返回结果结构
    result = {
        'student_info': None,
        'colleges': []
    }
    
    # 如果没有提供地域名称，直接返回空结果
    if not location_names:
        return result
    
    # 使用_get_area_ids方法将地域名称转换为地区ID
    location_names_str = ','.join(location_names)
    area_ids = StudentDataService._get_area_ids(location_names_str)
    
    # 如果没有找到匹配的地区，返回空结果
    if not area_ids:
        return result
    
    # 获取学生数据
    student_data = None
    student_score = 0
    subject_type = None
    education_level = None
    student_subjects = None
    tuition_ranges = None
    specialty_types = []  

    if student_id:
        student_data = StudentDataService.extract_college_recommendation_data(student_id)
        # 使用高考分数，如果没有则使用模考分数
        student_score = student_data.get('student_score', 0)
        if student_score is None or student_score == 0:
            student_score = student_data.get('mock_exam_score', 0) or 0
        
        subject_type = student_data.get('subject_type')
        education_level = student_data.get('education_level')
        student_subjects = student_data.get('student_subjects', {})
        tuition_ranges = student_data.get('tuition_ranges', [])
        specialty_types = student_data.get('specialty_types', [])

        # 添加学生信息到返回结果
        result['student_info'] = {
            'student_score': student_score,
            'subject_type': subject_type,
            'education_level': education_level,
            'student_subjects': student_subjects,
            'area_ids': area_ids,
            'tuition_ranges': tuition_ranges,
            'specialty_types': specialty_types  # 添加这一行
        }
    
    # 收集所有选中地区及其子地区的ID
    all_area_ids = []
    for area_id in area_ids:
        # 获取当前地区及其所有子地区
        child_area_ids = CollegeRepository.get_all_child_areas(area_id)
        all_area_ids.extend(child_area_ids)
    
    # 去重
    all_area_ids = list(set(all_area_ids))
    
    # 如果没有有效的地区ID，返回空结果
    if not all_area_ids:
        return result
    
    # 构建查询 - 直接查询学校和专业信息
    query = db.session.query(
        ZwhXgkYuanxiao2025.cid,         # 学校ID
        ZwhXgkYuanxiao2025.cname,       # 学校名称
        ZwhXgkYuanxiao2025.uncode,      # 学校代码
        ZwhXgkYuanxiao2025.leixing,     # 学校类型
        ZwhXgkYuanxiao2025.xingzhi,     # 学校性质
        ZwhXgkYuanxiao2025.tese,        # 学校特色
        ZwhXgkYuanxiao2025.teshu,       # 特殊类型
        ZwhAreas.aname.label('area_name'), # 地区名称
        ZwhAreas.aid.label('area_id')   # 地区ID
    ).join(
        ZwhAreas,
        ZwhXgkYuanxiao2025.aid == ZwhAreas.aid
    ).filter(
        ZwhXgkYuanxiao2025.aid.in_(all_area_ids)
    )
    
    # 执行查询获取学校基本信息
    college_results = query.all()
    
    # 创建学校基本信息字典
    college_info_dict = {}
    college_cids = []
    
    for college in college_results:
        # 获取地区完整路径
        area_path = CollegeRepository.get_complete_area_path(college.area_id)
        area_name = college.area_name
        
        # 从省级开始组合地区名称
        if len(area_path) > 1:
            path_names = [area['aname'] for area in area_path[1:]]
            area_name = ''.join(path_names)
        
        # 获取特色、类型的文本描述
        tese_text = CollegeRepository.convert_code_to_text(college.tese, 'tese')
        leixing_text = CollegeRepository.convert_code_to_text(college.leixing, 'leixing')
        teshu_text = CollegeRepository.convert_code_to_text(college.teshu, 'teshu')
        
        college_info_dict[college.cid] = {
            'cid': college.cid,
            'cname': college.cname,
            'uncode': college.uncode,
            'area_name': area_name,
            'leixing': college.leixing,
            'leixing_text': leixing_text[0] if leixing_text else '',
            'tese': college.tese,
            'tese_text': tese_text,
            'teshu': college.teshu,
            'teshu_text': teshu_text,
            'xingzhi': college.xingzhi,
            'majors': []
        }
        
        college_cids.append(college.cid)
    
    # 如果有学校，则查询这些学校的专业信息
    if college_cids:
        # 查询专业信息
        major_query = db.session.query(
            ZwhXgkFenshuxian2025.id,          # 分数线记录ID
            ZwhXgkFenshuxian2025.cid,         # 学校ID
            ZwhXgkFenshuxian2025.spid,        # 专业ID
            ZwhXgkFenshuxian2025.spname,      # 专业名称
            ZwhXgkFenshuxian2025.spcode,      # 专业代码
            ZwhXgkFenshuxian2025.suid,        # 科别(文/理)
            ZwhXgkFenshuxian2025.newbid,      # 批次(本科/专科)
            ZwhXgkFenshuxian2025.yuce,        # 预测分数
            ZwhXgkFenshuxian2025.tuitions,    # 学费
            ZwhXgkFenshuxian2025.csbplannum,  # 计划人数
            (ZwhXgkFenshuxian2025.yuce - student_score).label('score_diff')  # 分数差
        ).join(
            ZwhXgkFenzu2025,
            ZwhXgkFenshuxian2025.cgid == ZwhXgkFenzu2025.cgid,
            isouter=True  # 使用外连接避免无匹配专业组的问题
        ).filter(
            ZwhXgkFenshuxian2025.cid.in_(college_cids),
            ZwhXgkFenshuxian2025.spid != 32767,  # 排除投档线记录，只获取专业
            ZwhXgkFenshuxian2025.yuce.isnot(None)
        )
        
        # 添加科别筛选
        if subject_type:
            major_query = major_query.filter(ZwhXgkFenshuxian2025.suid == subject_type)
        
        # 添加学历层次筛选
        if education_level:
            major_query = major_query.filter(ZwhXgkFenshuxian2025.newbid == education_level)
        
        # 添加选科匹配条件
        if student_subjects:
            for subject_key, subject_value in student_subjects.items():
                if subject_value == 1:  # 学生选了该科目
                    continue  # 无需额外筛选
                elif subject_value == 2:  # 学生没选该科目
                    # 只能匹配专业对该科目无要求(值为2)的情况
                    major_query = major_query.filter(getattr(ZwhXgkFenzu2025, subject_key) == 2)
        
        # 添加学费范围筛选 - 使用与第二个函数相同的逻辑
        if tuition_ranges:
            tuition_conditions = []
            for min_fee, max_fee in tuition_ranges:
                if max_fee is None:
                    # "X万以上"的情况
                    tuition_conditions.append(ZwhXgkFenshuxian2025.tuitions >= min_fee)
                else:
                    # 学费在范围内
                    tuition_conditions.append(
                        db.and_(
                            ZwhXgkFenshuxian2025.tuitions >= min_fee,
                            ZwhXgkFenshuxian2025.tuitions <= max_fee
                        )
                    )
            
            if tuition_conditions:
                major_query = major_query.filter(db.or_(*tuition_conditions))

        # 添加专业类型筛选
        if specialty_types:
            # 子查询：查找包含任一指定专业类型的专业组
            subquery = db.session.query(ZwhXgkFenshuxian2025.cgid).filter(
                ZwhXgkFenshuxian2025.subclassid.in_(specialty_types),
                ZwhXgkFenshuxian2025.spid != 32767  # 排除投档线记录
            ).distinct().subquery()
            subquery_select = subquery.select()  # 显式转换为 select()
            major_query = major_query.filter(ZwhXgkFenshuxian2025.cgid.in_(subquery_select))

        # 添加分数差范围筛选 - 使用更宽松的范围
        if student_score > 0:
            max_diff = 12
            min_diff = -40
            major_query = major_query.filter(
                (ZwhXgkFenshuxian2025.yuce - student_score).between(min_diff, max_diff)
            )

        # 执行查询
        major_results = major_query.all()
        
        # 按大学ID分组处理专业信息
        for record in major_results:
            cid = record.cid
            
            # 如果学校信息不在字典中，跳过
            if cid not in college_info_dict:
                continue
            
            # 添加专业信息
            major_info = {
                'id': record.id,
                'spid': record.spid,
                'spname': record.spname,
                'spcode': record.spcode,
                'prediction_score': record.yuce,
                'score_diff': record.score_diff,
                'tuition': record.tuitions,
                'plan_number': record.csbplannum
            }
            college_info_dict[cid]['majors'].append(major_info)
    
    # 将大学字典转换为列表，并只包含有专业的学校
    result['colleges'] = [college for college in college_info_dict.values() if college['majors']]
    
    # 按学校名称排序
    result['colleges'].sort(key=lambda x: x['cname'])
    
    return result