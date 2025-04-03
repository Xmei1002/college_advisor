# app/services/college/recommendation_service.py
from app.core.recommendation.repository import CollegeRepository
from app.core.recommendation.score_classification import ScoreClassifier

class RecommendationService:
    """院校推荐服务，组合数据访问和业务逻辑"""
    
    @staticmethod
    def get_colleges_by_category_and_group(student_score, subject_type, education_level, 
                                          category_id, group_id, student_subjects,
                                          area_ids=None, specialty_types=None, 
                                          mode='smart', page=1, per_page=20,
                                          tese_types=None, leixing_types=None, teshu_types=None):
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
        :return: 查询结果和分页信息
        """
        # 参数预处理，确保area_ids和specialty_types为列表
        area_ids = area_ids or []
        specialty_types = specialty_types or []
        tese_types = tese_types or []
        leixing_types = leixing_types or []
        teshu_types = teshu_types or []
        
        if not education_level:
            education_level = 11  # 默认本科
            
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
            teshu_types=teshu_types
        )
        
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
        
        # 5. 根据专业组ID获取专业信息
        specialties = CollegeRepository.get_specialties_by_group_ids(
            group_ids, subject_type, education_level, student_subjects
        )
        
        # 6. 将专业信息按专业组分组
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
            
        # 7. 组织最终结果
        result = []
        for group in paginated_groups:
            # 对于每个专业组，构造完整信息
            group_specialty_count = CollegeRepository.count_specialties_by_group_id(
                group.cgid, subject_type, education_level, student_subjects
            )
            
            # 计算分类
            category, group_name = ScoreClassifier.classify_by_score_diff(
                group.score_diff, education_level, mode
            )
            
            # 获取并转换特色、类型和特殊类型的文本描述
            tese_text = CollegeRepository.convert_code_to_text(group.tese, 'tese')
            leixing_text = CollegeRepository.convert_code_to_text(group.leixing, 'leixing')
            teshu_text = CollegeRepository.convert_code_to_text(group.teshu, 'teshu')
            
            group_info = {
                'cgid': group.cgid,
                'cid': group.cid,
                'cname': group.cname,
                'uncode': group.uncode,
                'school_type': group.leixing,
                'school_type_text': leixing_text[0] if leixing_text else '',
                'school_nature': group.xingzhi,
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
                'specialties': specialties_by_group.get(group.cgid, [])
            }
            result.append(group_info)
                
        # 8. 返回结果和分页信息
        pagination = {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
        return result, pagination