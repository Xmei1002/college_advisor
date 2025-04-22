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
    
    # # 查询该大学的所有专业组
    # group_query = db.session.query(
    #     ZwhXgkFenzu2025.cgid,           # 专业组ID
    #     ZwhXgkFenzu2025.newbid,         # 批次
    #     ZwhXgkFenzu2025.newsuid,        # 科别
    #     ZwhXgkFenzu2025.cgname,         # 专业组名称
    #     ZwhXgkFenzu2025.wu,             # 物理要求
    #     ZwhXgkFenzu2025.shi,            # 历史要求
    #     ZwhXgkFenzu2025.hua,            # 化学要求
    #     ZwhXgkFenzu2025.sheng,          # 生物要求
    #     ZwhXgkFenzu2025.di,             # 地理要求
    #     ZwhXgkFenzu2025.zheng,          # 政治要求
    #     ZwhXgkFenzu2025.minxuefei,      # 最低学费
    #     ZwhXgkFenzu2025.maxxuefei       # 最高学费
    # ).filter(
    #     ZwhXgkFenzu2025.newcid == college_id
    # )
    
    
    # # 执行查询获取专业组信息
    # group_results = group_query.all()
    
    # # 获取所有专业组ID
    # group_ids = [group.cgid for group in group_results]
    
    # # 获取所有专业组的历年投档线数据
    # history_data = {}
    # if group_ids:
    #     for subj_type in [1, 2]:  # 1-文科/历史组，2-理科/物理组
    #         for edu_level in [11, 12]:  # 11-本科，12-专科
    #             # 获取该科别和教育层次下的历年数据
    #             temp_history = CollegeRepository.get_college_group_history_by_ids(
    #                 group_ids, subj_type, edu_level
    #             )
    #             # 合并数据
    #             history_data.update(temp_history)
    
    # # 处理每个专业组的信息
    # for group in group_results:
    #     group_id = group.cgid
        
    #     # 查询该专业组的2025年投档线
    #     line_query = db.session.query(
    #         ZwhXgkFenshuxian2025.yuce,       # 预测分数
    #         ZwhXgkFenshuxian2025.csbplannum  # 计划人数
    #     ).filter(
    #         ZwhXgkFenshuxian2025.cgid == group_id,
    #         ZwhXgkFenshuxian2025.spid == 32767  # 投档线记录
    #     )
        
    #     # 执行查询获取投档线信息
    #     line_result = line_query.first()
    #     prediction_score = line_result.yuce if line_result else None
    #     plan_number = line_result.csbplannum if line_result else None
        
    #     # 获取专业组下的所有专业
    #     specialties = []
    #     if group_id:
    #         # 查询该专业组的所有专业
    #         specialties_result = CollegeRepository.get_specialties_by_group_id(group_id)
    #         specialties = specialties_result  # 直接使用返回的结果
        
    #     # 构建专业组信息
    #     group_info = {
    #         'group_name': group.cgname,
    #         'prediction_score': prediction_score,
    #         'plan_number': plan_number,
    #         'min_tuition': group.minxuefei,
    #         'max_tuition': group.maxxuefei,
    #         'subject_requirements': {
    #             'wu': group.wu,
    #             'shi': group.shi,
    #             'hua': group.hua,
    #             'sheng': group.sheng,
    #             'di': group.di,
    #             'zheng': group.zheng
    #         },
    #         'specialties': specialties,
    #         'history': history_data.get(group_id, {})  # 添加历年数据
    #     }
        
    #     # 添加到大学信息中
    #     college_info['college_groups'].append(group_info)
    
    return college_info
