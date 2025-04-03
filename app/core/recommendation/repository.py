# app/core/recommendation/repository.py
from app.extensions import db
from sqlalchemy import func
from app.models.zwh_xgk_zhuanye_2025 import ZwhXgkZhuanye2025
# 导入模型（避免循环导入）
from app.models.zwh_xgk_fenshuxian_2025 import ZwhXgkFenshuxian2025
from app.models.zwh_xgk_fenshuxian_2024 import ZwhXgkFenshuxian2024
from app.models.zwh_xgk_fenshuxian_2023 import ZwhXgkFenshuxian2023
from app.models.zwh_xgk_fenshuxian_2022 import ZwhXgkFenshuxian2022
from app.models.zwh_xgk_fenshuxian_2021 import ZwhXgkFenshuxian2021
from app.models.zwh_xgk_yuanxiao_2025 import ZwhXgkYuanxiao2025
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_xgk_fenzu_2025 import ZwhXgkFenzu2025
from app.core.recommendation.score_classification import ScoreClassifier

class CollegeRepository:
    """院校数据仓库，负责从数据库获取院校数据"""

    @staticmethod
    def convert_code_to_text(code, code_type):
        """
        将代码转换为对应的文本描述
        
        :param code: 代码值
        :param code_type: 代码类型('tese', 'leixing', 'teshu')
        :return: 文本描述列表
        """
        code_mappings = {
            'tese': {
                101: "211", 102: "985", 103: "研究生院", 104: "卓越计划", 
                105: "双一流大学", 107: "强基计划", 110: "省部共建", 
                111: "硕博点", 112: "硕士点"
            },
            'leixing': {
                101: "综合", 102: "工科", 103: "农业", 104: "林业", 
                105: "医药", 106: "师范", 107: "语言", 108: "财经", 
                109: "政法", 110: "体育", 111: "艺术", 112: "民族"
            },
            'teshu': {
                101: '定向', 102: '农林矿', 103: '软件类', 104: '医护类', 
                105: '较高收费', 106: '其他单列', 107: '异地校区'
            }
        }
        
        if not code or code_type not in code_mappings:
            return []
        
        # 如果code是以逗号分隔的字符串，分割并转换每个代码
        if isinstance(code, str) and ',' in code:
            code_list = [int(c.strip()) for c in code.split(',') if c.strip().isdigit()]
            return [code_mappings[code_type].get(c, "") for c in code_list if c in code_mappings[code_type]]
        
        # 如果code是单个值
        if isinstance(code, (int, str)):
            code_int = int(code) if isinstance(code, str) and code.isdigit() else code
            return [code_mappings[code_type].get(code_int, "")] if code_int in code_mappings[code_type] else []
        
        return []

    @staticmethod
    def get_all_child_areas(area_id):
        """
        递归获取指定地区的所有子地区ID（包括自身）
        
        :param area_id: 地区ID
        :return: 包含自身及所有子地区ID的列表
        """
        from app.models.zwh_areas import ZwhAreas
        
        # 如果没有指定地区ID，返回空列表
        if not area_id:
            return []
            
        # 初始化结果列表，包含当前地区ID
        result_ids = [area_id]
        
        # 获取直接子地区
        direct_children = db.session.query(ZwhAreas.aid).filter(
            ZwhAreas.afather == area_id
        ).all()
        
        # 递归获取每个子地区的所有子地区
        for child in direct_children:
            child_id = child.aid
            # 递归调用获取子地区的子地区
            sub_children = CollegeRepository.get_all_child_areas(child_id)
            # 添加到结果列表
            result_ids.extend(sub_children)
            
        return result_ids
    
    @staticmethod
    def get_complete_area_path(area_id):
        """
        获取地区的完整路径（从国家到当前地区）
        
        :param area_id: 地区ID
        :return: 地区路径字典列表，每个字典包含地区ID和名称
        """
        
        if not area_id:
            return []
            
        # 初始化结果列表
        path = []
        current_id = area_id
        
        # 循环查询直到找到顶级节点(afather=0)或找不到更多父级
        while current_id:
            # 查询当前地区信息
            area = db.session.query(ZwhAreas.aid, ZwhAreas.aname, ZwhAreas.afather).filter(
                ZwhAreas.aid == current_id
            ).first()
            
            # 如果找不到地区信息，跳出循环
            if not area:
                break
                
            # 添加地区信息到路径
            path.append({
                'aid': area.aid,
                'aname': area.aname
            })
            
            # 如果是顶级节点(afather=0)，跳出循环
            if area.afather == 0:
                break
                
            # 更新current_id为父级ID
            current_id = area.afather
            
        # 反转列表，使路径从顶级到当前
        path.reverse()
        
        return path

    @staticmethod
    def get_college_groups_by_category(student_score, subject_type, education_level, 
                                    category_id, group_id, student_subjects,
                                    area_ids=None, specialty_types=None, 
                                    mode='smart', tese_types=None, leixing_types=None, teshu_types=None):
        """
        根据类别和志愿段查询符合要求的院校专业组
        
        :param student_score: 学生分数
        :param subject_type: 科别（1-文科/历史组，2-理科/物理组）
        :param education_level: 学历层次（11-本科，12-专科）
        :param category_id: 类别ID（1-冲，2-稳，3-保）
        :param group_id: 志愿段ID（1-12，对应不同的志愿段）
        :param student_subjects: 学生选科情况，字典格式如{'wu': 1, 'hua': 1, 'sheng': 2, 'shi': 2, 'di': 2, 'zheng': 2}
        :param area_ids: 地区ID列表
        :param specialty_types: 专业类型ID列表
        :param mode: 分类模式（'smart','professional','free'）
        :param tese_types: 学校特色筛选列表
        :param leixing_types: 学校类型筛选列表
        :param teshu_types: 特殊类型筛选列表
        :return: 符合条件的专业组列表
        """

        
        # 参数预处理
        area_ids = area_ids or []
        specialty_types = specialty_types or []
        tese_types = tese_types or []
        leixing_types = leixing_types or []
        teshu_types = teshu_types or []
        
        # 获取分差范围
        score_diff_range = ScoreClassifier.get_score_diff_range(
            category_id, group_id, education_level, mode
        )
        
        # 如果没有找到对应的分差范围，返回空结果
        if not score_diff_range:
            return []
            
        min_diff, max_diff = score_diff_range
        
        # 基础查询 - 查询专业组投档线记录 (spid = 32767)
        query = db.session.query(
            ZwhXgkFenshuxian2025.cgid,         # 专业组ID
            ZwhXgkFenshuxian2025.cid,          # 学校ID
            ZwhXgkYuanxiao2025.cname,          # 学校名称
            ZwhXgkYuanxiao2025.uncode,         # 学校代码
            ZwhXgkYuanxiao2025.leixing,        # 学校类型
            ZwhXgkYuanxiao2025.xingzhi,        # 学校性质
            ZwhXgkYuanxiao2025.tese,           # 学校特色（新增）
            ZwhXgkYuanxiao2025.teshu,          # 特殊类型（新增）
            ZwhXgkFenzu2025.minxuefei,         # 最低学费
            ZwhXgkFenzu2025.maxxuefei,         # 最高学费
            ZwhAreas.aname.label('area_name'),  # 地区名称
            ZwhXgkFenzu2025.cgname,            # 专业组名称
            ZwhXgkFenzu2025.wu,                # 物理要求
            ZwhXgkFenzu2025.shi,               # 历史要求
            ZwhXgkFenzu2025.hua,               # 化学要求
            ZwhXgkFenzu2025.sheng,             # 生物要求
            ZwhXgkFenzu2025.di,                # 地理要求
            ZwhXgkFenzu2025.zheng,             # 政治要求
            ZwhXgkFenshuxian2025.yuce,         # 预测分数
            ZwhXgkFenshuxian2025.csbplannum,   # 计划人数
            (ZwhXgkFenshuxian2025.yuce - student_score).label('score_diff'),  # 分数差
            ZwhAreas.aid.label('area_id')      # 地区ID
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
        
        # 添加专业类型筛选 - 支持多个专业类型
        if specialty_types:
            # 子查询：查找包含任一指定专业类型的专业组
            subquery = db.session.query(ZwhXgkFenshuxian2025.cgid).filter(
                ZwhXgkFenshuxian2025.subclassid.in_(specialty_types),
                ZwhXgkFenshuxian2025.spid != 32767  # 排除投档线记录
            ).distinct().subquery()
            subquery_select = subquery.select()  # 显式转换为 select()
            query = query.filter(ZwhXgkFenshuxian2025.cgid.in_(subquery_select))
        
        # 添加学校特色筛选
        if tese_types:
            # 构建SQL条件以匹配任意一个特色类型
            tese_conditions = []
            for tese_type in tese_types:
                # 对于每个tese_type，检查数据库字段中是否含有这个值
                # 这里使用LIKE操作符，因为tese可能是以逗号分隔的多个值
                tese_conditions.append(ZwhXgkYuanxiao2025.tese.like(f'%{tese_type}%'))
            
            # 将所有条件用OR连接
            if tese_conditions:
                query = query.filter(db.or_(*tese_conditions))
        
        # 添加学校类型筛选
        if leixing_types:
            query = query.filter(ZwhXgkYuanxiao2025.leixing.in_(leixing_types))
        
        # 添加特殊类型筛选
        if teshu_types:
            # 与tese类似，构建SQL条件
            teshu_conditions = []
            for teshu_type in teshu_types:
                teshu_conditions.append(ZwhXgkYuanxiao2025.teshu.like(f'%{teshu_type}%'))
            
            if teshu_conditions:
                query = query.filter(db.or_(*teshu_conditions))
        
        # 添加选科匹配条件
        if student_subjects:
            # 遍历学生选科情况
            for subject_key, subject_value in student_subjects.items():
                # 如果学生选了该科目(值为1)，那么可以匹配专业的任何要求(1必选或2无要求)
                # 如果学生没选该科目(值为2)，那么只能匹配专业的无要求(值为2)
                if subject_value == 1:  # 学生选了该科目
                    continue  # 无需额外筛选，可以匹配所有专业
                elif subject_value == 2:  # 学生没选该科目
                    # 只能匹配专业对该科目无要求(值为2)的情况
                    query = query.filter(getattr(ZwhXgkFenzu2025, subject_key) == 2)
        
        # 执行查询
        results = query.all()
            
        enriched_results = []
        for result in results:
            # 创建结果对象副本（SQLAlchemy查询结果是只读的）
            enriched_result = result._asdict() if hasattr(result, '_asdict') else {
                column.name: getattr(result, column.name)
                for column in result._fields
            }
            
            # 获取地区完整路径
            area_path = CollegeRepository.get_complete_area_path(result.area_id)
            
            # 组合地区名称成一个完整字符串，跳过国家级（索引0）
            if len(area_path) > 1:
                # 从省级开始（索引1）
                path_names = [area['aname'] for area in area_path[1:]]
                enriched_result['area_name'] = ''.join(path_names)
            
            # 创建新的具名元组或类似的对象以保持原有接口
            from collections import namedtuple
            ResultType = namedtuple('Result', list(enriched_result.keys()))
            enriched_results.append(ResultType(**enriched_result))
        
        return enriched_results
    
    @staticmethod
    def get_specialties_by_group_ids(cgids, subject_type, education_level, student_subjects=None):
        """
        根据专业组ID列表获取所有专业信息
        
        :param cgids: 专业组ID列表
        :param subject_type: 科别
        :param education_level: 教育层次
        :param student_subjects: 学生选科情况
        :return: 专业信息列表
        """
        # 导入模型
        
        # 查询专业信息
        query = db.session.query(
            ZwhXgkFenshuxian2025.id,              # 专业ID
            ZwhXgkFenshuxian2025.cgid,           # 专业组ID
            ZwhXgkFenshuxian2025.spid,           # 专业ID
            ZwhXgkFenshuxian2025.spname,         # 专业名称
            ZwhXgkFenshuxian2025.spcode,         # 专业代码
            ZwhXgkFenshuxian2025.zyfx,           # 专业方向
            ZwhXgkFenshuxian2025.csbplannum,     # 专业计划人数 (添加这一行)
            ZwhXgkFenshuxian2025.tuitions,       # 学费
            ZwhXgkFenshuxian2025.yuce,           # 预测分数
            ZwhXgkFenshuxian2025.wu,             # 物理要求
            ZwhXgkFenshuxian2025.shi,            # 历史要求
            ZwhXgkFenshuxian2025.hua,            # 化学要求
            ZwhXgkFenshuxian2025.sheng,          # 生物要求
            ZwhXgkFenshuxian2025.di,             # 地理要求
            ZwhXgkFenshuxian2025.zheng,          # 政治要求
            ZwhXgkFenshuxian2025.subclassid,     # 专业类别ID
            ZwhXgkZhuanye2025.teacher,           # 教师
            ZwhXgkZhuanye2025.doctor,            # 医生
            ZwhXgkZhuanye2025.official,          # 公务员
            ZwhXgkZhuanye2025.content            # 专业介绍
        ).outerjoin(
            ZwhXgkZhuanye2025,
            ZwhXgkFenshuxian2025.spid == ZwhXgkZhuanye2025.spid
        ).filter(
            ZwhXgkFenshuxian2025.cgid.in_(cgids),
            ZwhXgkFenshuxian2025.spid != 32767,  # 排除投档线记录
            ZwhXgkFenshuxian2025.suid == subject_type,
            ZwhXgkFenshuxian2025.newbid == education_level
        )
        
        # 添加选科匹配条件
        if student_subjects:
            for subject_key, subject_value in student_subjects.items():
                if subject_value == 1:  # 学生选了该科目
                    continue  # 无需额外筛选
                elif subject_value == 2:  # 学生没选该科目
                    # 只能匹配专业对该科目无要求(值为2)的情况
                    query = query.filter(getattr(ZwhXgkFenshuxian2025, subject_key) == 2)
        
        return query.all()
    
    @staticmethod
    def count_specialties_by_group_id(cgid, subject_type, education_level, student_subjects=None):
        """
        统计专业组下符合条件的专业数量
        
        :param cgid: 专业组ID
        :param subject_type: 科别
        :param education_level: 教育层次
        :param student_subjects: 学生选科情况
        :return: 专业数量
        """
        
        query = db.session.query(func.count(ZwhXgkFenshuxian2025.id)).filter(
            ZwhXgkFenshuxian2025.cgid == cgid,
            ZwhXgkFenshuxian2025.spid != 32767,  # 排除投档线记录
            ZwhXgkFenshuxian2025.suid == subject_type,
            ZwhXgkFenshuxian2025.newbid == education_level
        )
        
        # 添加选科匹配条件
        if student_subjects:
            for subject_key, subject_value in student_subjects.items():
                if subject_value == 1:  # 学生选了该科目
                    continue  # 无需额外筛选
                elif subject_value == 2:  # 学生没选该科目
                    # 只能匹配专业对该科目无要求(值为2)的情况
                    query = query.filter(getattr(ZwhXgkFenshuxian2025, subject_key) == 2)
        
        return query.scalar()
    
    @staticmethod
    def get_specialties_by_group_id(college_group_id):
        """
        根据专业组ID获取该组下的所有专业信息，每个专业包含2021-2024年的历史数据及2025年数据
        
        :param college_group_id: 专业组ID
        :return: 专业信息列表
        """
        # 定义所有年份的表及其对应的年份
        tables = [
            (ZwhXgkFenshuxian2025, "2025"),
            (ZwhXgkFenshuxian2024, "2024"),
            (ZwhXgkFenshuxian2023, "2023"),
            (ZwhXgkFenshuxian2022, "2022"),
            (ZwhXgkFenshuxian2021, "2021")
        ]
        
        # 构建每个表的查询，只查必要字段
        queries = []
        for table, year in tables:
            query = db.session.query(
                table.spid.label("specialty_id"),       # 专业ID
                table.spname.label("specialty_name"),   # 专业名称
                table.spcode.label("specialty_code"),   # 专业代码
                table.csbplannum.label("plan_number"),  # 招生计划人数
                table.tuitions.label("tuition"),        # 学费（仅 2025 年需要）
                table.yuce.label("prediction_score"),   # 预测分数（仅 2025 年需要）
                table.csbscore.label("admission_score"),# 录取分数
                table.weici.label("rank"),              # 位次
                db.literal(year).label("year")          # 年份
            ).filter(
                table.cgid == college_group_id,
                table.spid != 32767  # 排除投档线记录
            )
            queries.append(query)
        
        # 使用 UNION 合并所有查询
        union_query = db.union(*queries)
        
        # 执行 UNION 查询并获取结果
        results = db.session.execute(union_query).fetchall()
        
        # 按 specialty_id 组织数据
        specialty_dict = {}
        for row in results:
            spid = row.specialty_id
            if spid not in specialty_dict:
                specialty_dict[spid] = {
                    "specialty_id": spid,
                    "specialty_name": row.specialty_name,
                    "specialty_code": row.specialty_code,
                    "tuition": row.tuition if row.year == "2025" else None,  # 2025年的学费
                    "prediction_score": row.prediction_score if row.year == "2025" else None,  # 2025年的预测分数
                    "plan_number": row.plan_number if row.year == "2025" else None,  # 2025年的计划人数
                    "history": {}
                }
            
            # 填充历史数据（2021-2024）
            if row.year != "2025":
                specialty_dict[spid]["history"][row.year] = {
                    "plan_number": row.plan_number,
                    "admission_score": row.admission_score,
                    "rank": row.rank
                }
            else:
                # 确保 2025 年的数据覆盖初始值
                specialty_dict[spid]["plan_number"] = row.plan_number
                specialty_dict[spid]["tuition"] = row.tuition
                specialty_dict[spid]["prediction_score"] = row.prediction_score
        
        # 计算计划人数变化并生成最终结果
        specialties = []
        for specialty in specialty_dict.values():
            plan_2025 = specialty["plan_number"] or 0  # 如果 None，按 0 处理
            plan_2024 = specialty["history"].get("2024", {}).get("plan_number") or 0  # 如果无 2024 数据，按 0 处理
            specialty["plan_number_change"] = plan_2025 - plan_2024
            specialties.append(specialty)
        
        # 按 specialty_id 排序（可选）
        specialties.sort(key=lambda x: x["specialty_id"])
        
        return specialties