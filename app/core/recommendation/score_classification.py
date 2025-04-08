# app/core/recommendation/score_classification.py
class ScoreClassifier:
    """分数分类器，用于根据分差将高校分类为冲、稳、保"""
    
    # Mode constants
    MODE_SMART = 'smart'
    MODE_PROFESSIONAL = 'professional'
    MODE_FREE = 'free'

    # Category constants
    CATEGORY_CHASING = 'chasing'  # 冲
    CATEGORY_STABLE = 'stable'    # 稳
    CATEGORY_SAFE = 'safe'        # 保

    # 大类映射
    CATEGORY_MAP = {
        1: CATEGORY_CHASING,
        2: CATEGORY_STABLE,
        3: CATEGORY_SAFE
    }

    # 志愿段映射
    GROUP_MAP = {
        1: "1-4",
        2: "5-8",
        3: "9-12",
        4: "13-16",
        5: "17-20",
        6: "21-24",
        7: "25-28",
        8: "29-32",
        9: "33-36",
        10: "37-40",
        11: "41-44",
        12: "45-48"
    }

    @staticmethod
    def classify_by_score_diff(score_diff, education_level, mode='smart'):
        """
        根据分差对高校进行分类
        
        :param score_diff: 分差（预测分 - 学生分）
        :param education_level: 教育层次（11-本科，12-专科）
        :param mode: 分类模式（'smart'智能模式，'professional'专业模式，'free'自由模式）
        :return: 类别、分组信息和推荐消息的元组
        """
        if education_level == 12:  # 专科
            if mode == ScoreClassifier.MODE_PROFESSIONAL:
                return ScoreClassifier._classify_vocational_professional(score_diff)
            elif mode == ScoreClassifier.MODE_FREE:
                return ScoreClassifier._classify_vocational_free(score_diff)
            else:  # 默认智能模式
                return ScoreClassifier._classify_vocational(score_diff)
        else:  # 本科
            if mode == ScoreClassifier.MODE_PROFESSIONAL:
                return ScoreClassifier._classify_undergraduate_professional(score_diff)
            elif mode == ScoreClassifier.MODE_FREE:
                return ScoreClassifier._classify_undergraduate_free(score_diff)
            else:  # 默认智能模式
                return ScoreClassifier._classify_undergraduate(score_diff)
            
    @staticmethod
    def get_score_diff_range(category_id, group_id, education_level, mode='smart'):
        """
        根据类别ID和志愿段ID获取对应的分差范围
        
        :param category_id: 类别ID (1:冲, 2:稳, 3:保)
        :param group_id: 志愿段ID (1-12，对应不同的志愿段)
        :param education_level: 教育层次 (11:本科, 12:专科)
        :param mode: 分类模式 ('smart', 'professional', 'free')
        :return: (min_diff, max_diff) 分差范围的元组，如果不存在则返回None
        """
        # 检查参数有效性
        if category_id not in ScoreClassifier.CATEGORY_MAP or group_id not in ScoreClassifier.GROUP_MAP:
            return None
        category = ScoreClassifier.CATEGORY_MAP[category_id]
        group_suffix = ScoreClassifier.GROUP_MAP[group_id]
        print('category:', category, 'group_suffix:', group_suffix)
        # 构建对应的志愿组名称，如 "冲-志愿1-4"
        # 注意: 冲1-4对应group_id=1, 稳17-20对应group_id=5,保33-36对应group_id=9
        if category == ScoreClassifier.CATEGORY_CHASING:
            group_name = f"冲-志愿{group_suffix}"
        elif category == ScoreClassifier.CATEGORY_STABLE:
            group_name = f"稳-志愿{group_suffix}"
        elif category == ScoreClassifier.CATEGORY_SAFE:
            group_name = f"保-志愿{group_suffix}"
        
        # 获取所有对应分差范围
        ranges = []
        
        # 确定使用哪个分类方法
        if education_level == 12:  # 专科
            if mode == ScoreClassifier.MODE_PROFESSIONAL:
                classify_func = ScoreClassifier._classify_vocational_professional
            elif mode == ScoreClassifier.MODE_FREE:
                classify_func = ScoreClassifier._classify_vocational_free
            else:  # 默认智能模式
                classify_func = ScoreClassifier._classify_vocational
        else:  # 本科
            if mode == ScoreClassifier.MODE_PROFESSIONAL:
                classify_func = ScoreClassifier._classify_undergraduate_professional
            elif mode == ScoreClassifier.MODE_FREE:
                classify_func = ScoreClassifier._classify_undergraduate_free
            else:  # 默认智能模式
                classify_func = ScoreClassifier._classify_undergraduate
        
        # 扫描所有可能的分差，找到对应的范围
        step = 1  # 扫描步长
        min_diff = None
        max_diff = None
        
        # 针对不同模式和教育层次设置扫描范围
        if education_level == 11:  # 本科
            if mode == ScoreClassifier.MODE_SMART:
                scan_range = range(-40, 13, step)
            elif mode == ScoreClassifier.MODE_PROFESSIONAL:
                scan_range = range(-60, 1, step)
            else:  # 自由模式
                scan_range = range(-80, 181, step)
        else:  # 专科
            if mode == ScoreClassifier.MODE_SMART:
                scan_range = range(-100, 21, step)
            elif mode == ScoreClassifier.MODE_PROFESSIONAL:
                scan_range = range(-110, -9, step)
            else:  # 自由模式
                scan_range = range(-120, 241, step)
        
        for diff in scan_range:
            cat, grp, _ = classify_func(diff)
            if cat == category and grp == group_name:
                if min_diff is None:
                    min_diff = diff
                max_diff = diff
        
        # 如果找到了范围
        if min_diff is not None and max_diff is not None:
            return min_diff, max_diff
        
        return None
    
    @staticmethod
    def _classify_undergraduate(score_diff):
        """智能模式-本科分类逻辑"""
        # 冲（12~0）
        if 0 < score_diff <= 12:
            category = "chasing"
            if 0 < score_diff <= 3:
                group = "冲-志愿13-16"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲，建议放在 13 ~ 16 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            elif 3 < score_diff <= 6:
                group = "冲-志愿9-12"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲,建议放在 9 ~ 12志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            elif 6 < score_diff <= 9:
                group = "冲-志愿5-8"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲，建议放在 5 ~ 8 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            else:
                group = "冲-志愿1-4"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲,建议放在 1 ~ 4 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
        # 稳（0~-20）
        elif -20 < score_diff <= 0:
            category = "stable"
            if -5 < score_diff <= 0:
                group = "稳-志愿17-20"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 17 ~ 20 志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            elif -10 < score_diff <= -5:
                group = "稳-志愿21-24"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 21 ~ 24志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            elif -15 < score_diff <= -10:
                group = "稳-志愿25-28"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 24 ~ 28 志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            else:
                group = "稳-志愿29-32"
                recommendation_msg = {
                    'msg': '很有希望，可以考虑稳一稳，建议放在 29 ~ 32志愿',
                    'msg2': '很有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
        # 保（-20~-40）
        elif -40 < score_diff <= -20:
            category = "safe"
            if -25 < score_diff <= -20:
                group = "保-志愿33-36"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 33 ~ 36 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            elif -30 < score_diff <= -25:
                group = "保-志愿37-40"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 37 ~ 40 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            elif -35 < score_diff <= -30:
                group = "保-志愿41-44"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 41 ~ 44 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            else:
                group = "保-志愿45-48"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 45 ~ 48 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
        else:
            return None, None, None  # 不在范围内
        
        return category, group, recommendation_msg

    @staticmethod
    def _classify_vocational(score_diff):
        """智能模式-专科分类逻辑"""
        # 冲（20~0）
        if 0 < score_diff <= 20:
            category = "chasing"
            if 0 < score_diff <= 5:
                group = "冲-志愿13-16"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲，建议放在 13 ~ 16 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            elif 5 < score_diff <= 10:
                group = "冲-志愿5-8"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲，建议放在 5 ~ 8 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            elif 10 < score_diff <= 15:
                group = "冲-志愿5-8"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲，建议放在 5 ~ 8 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
            else:
                group = "冲-志愿1-4"
                recommendation_msg = {
                    'msg': '比较冒险，可以考虑冲一冲,建议放在 1 ~ 4 志愿',
                    'msg2': '比较冒险，可以考虑冲一冲',
                    'jy': '冲'
                }
        # 稳（0~-40）
        elif -40 < score_diff <= 0:
            category = "stable"
            if -10 < score_diff <= 0:
                group = "稳-志愿17-20"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 17 ~ 20 志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            elif -20 < score_diff <= -10:
                group = "稳-志愿21-24"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 21 ~ 24志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            elif -30 < score_diff <= -20:
                group = "稳-志愿25-28"
                recommendation_msg = {
                    'msg': '有希望，可以考虑稳一稳，建议放在 24 ~ 28 志愿',
                    'msg2': '有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
            else:
                group = "稳-志愿29-32"
                recommendation_msg = {
                    'msg': '很有希望，可以考虑稳一稳，建议放在 29 ~ 32志愿',
                    'msg2': '很有希望，可以考虑稳一稳',
                    'jy': '稳'
                }
        # 保（-40~-100）
        elif -100 < score_diff <= -40:
            category = "safe"
            if -55 < score_diff <= -40:
                group = "保-志愿33-36"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 33 ~ 36 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            elif -70 < score_diff <= -55:
                group = "保-志愿37-40"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 37 ~ 40 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            elif -85 < score_diff <= -70:
                group = "保-志愿41-44"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 41 ~ 44 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
            else:
                group = "保-志愿45-48"
                recommendation_msg = {
                    'msg': '很有希望，可以保一保,建议放在 45 ~ 48 志愿',
                    'msg2': '很有希望，可以保一保',
                    'jy': '保'
                }
        else:
            return None, None, None  # 不在范围内
        
        return category, group, recommendation_msg
    
    @staticmethod
    def _classify_undergraduate_professional(score_diff):
        """专业模式-本科分类逻辑"""
        # 冲（0~-20）
        if -20 <= score_diff <= 0:
            category = "chasing"
            if -5 <= score_diff <= 0:
                group = "冲-志愿1-4"
            elif -10 <= score_diff < -5:
                group = "冲-志愿5-8"
            elif -15 <= score_diff < -10:
                group = "冲-志愿9-12"
            else:
                group = "冲-志愿13-16"
        # 稳（-20~-40）
        elif -40 <= score_diff < -20:
            category = "stable"
            if -25 <= score_diff < -20:
                group = "稳-志愿17-20"
            elif -30 <= score_diff < -25:
                group = "稳-志愿21-24"
            elif -35 <= score_diff < -30:
                group = "稳-志愿25-28"
            else:
                group = "稳-志愿29-32"
        # 保（-40~-60）
        elif -60 <= score_diff < -40:
            category = "safe"
            if -45 <= score_diff < -40:
                group = "保-志愿33-36"
            elif -50 <= score_diff < -45:
                group = "保-志愿37-40"
            elif -55 <= score_diff < -50:
                group = "保-志愿41-44"
            else:
                group = "保-志愿45-48"
        else:
            return None, None  # 不在范围内
        
        return category, group,
    
    @staticmethod
    def _classify_vocational_professional(score_diff):
        """专业模式-专科分类逻辑"""
        # 冲（-10~-30）
        if -30 <= score_diff <= -10:
            category = "chasing"
            if -15 <= score_diff <= -10:
                group = "冲-志愿1-4"
            elif -20 <= score_diff < -15:
                group = "冲-志愿5-8"
            elif -25 <= score_diff < -20:
                group = "冲-志愿9-12"
            else:
                group = "冲-志愿13-16"
        # 稳（-30~-70）
        elif -70 <= score_diff < -30:
            category = "stable"
            if -40 <= score_diff < -30:
                group = "稳-志愿17-20"
            elif -50 <= score_diff < -40:
                group = "稳-志愿21-24"
            elif -60 <= score_diff < -50:
                group = "稳-志愿25-28"
            else:
                group = "稳-志愿29-32"
        # 保（-70~-110）
        elif -110 <= score_diff < -70:
            category = "safe"
            if -80 <= score_diff < -70:
                group = "保-志愿33-36"
            elif -90 <= score_diff < -80:
                group = "保-志愿37-40"
            elif -100 <= score_diff < -90:
                group = "保-志愿41-44"
            else:
                group = "保-志愿45-48"
        else:
            return None, None  # 不在范围内
        
        return category, group
    
    @staticmethod
    def _classify_undergraduate_free(score_diff):
        """自由模式-本科分类逻辑"""
        # 冲（180~0）
        if 0 <= score_diff <= 180:
            category = "chasing"
            if 0 <= score_diff <= 40:
                group = "冲-志愿13-16"
            elif 40 < score_diff <= 80:
                group = "冲-志愿9-12"
            elif 80 < score_diff <= 120:
                group = "冲-志愿5-8"
            else:
                group = "冲-志愿1-4"
        # 稳（0~-40）
        elif -40 <= score_diff < 0:
            category = "stable"
            if -10 <= score_diff < 0:
                group = "稳-志愿17-20"
            elif -20 <= score_diff < -10:
                group = "稳-志愿21-24"
            elif -30 <= score_diff < -20:
                group = "稳-志愿25-28"
            else:
                group = "稳-志愿29-32"
        # 保（-40~-80）
        elif -80 <= score_diff < -40:
            category = "safe"
            if -50 <= score_diff < -40:
                group = "保-志愿33-36"
            elif -60 <= score_diff < -50:
                group = "保-志愿37-40"
            elif -70 <= score_diff < -60:
                group = "保-志愿41-44"
            else:
                group = "保-志愿45-48"
        else:
            return None, None  # 不在范围内
        
        return category, group
    
    @staticmethod
    def _classify_vocational_free(score_diff):
        """自由模式-专科分类逻辑"""
        # 冲（240~20）
        if 20 <= score_diff <= 240:
            category = "chasing"
            if 20 <= score_diff <= 60:
                group = "冲-志愿13-16"
            elif 60 < score_diff <= 100:
                group = "冲-志愿9-12"
            elif 100 < score_diff <= 160:
                group = "冲-志愿5-8"
            else:
                group = "冲-志愿1-4"
        # 稳（20~-60）
        elif -60 <= score_diff < 20:
            category = "stable"
            if 0 <= score_diff < 20:
                group = "稳-志愿17-20"
            elif -20 <= score_diff < 0:
                group = "稳-志愿21-24"
            elif -40 <= score_diff < -20:
                group = "稳-志愿25-28"
            else:
                group = "稳-志愿29-32"
        # 保（-60~-120）
        elif -120 <= score_diff < -60:
            category = "safe"
            if -75 <= score_diff < -60:
                group = "保-志愿33-36"
            elif -90 <= score_diff < -75:
                group = "保-志愿37-40"
            elif -105 <= score_diff < -90:
                group = "保-志愿41-44"
            else:
                group = "保-志愿45-48"
        else:
            return None, None  # 不在范围内
        
        return category, group