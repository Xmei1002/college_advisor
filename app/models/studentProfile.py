# models/student.py

from app.extensions import db
from app.models.base import Base
from app.models.zwh_scorerank import ZwhScorerank
from app.models.zwh_xgk_picixian import ZwhXgkPicixian

class Student(Base):
    """学生信息模型"""
    __tablename__ = 'students'
    
    # 关联到用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    
    # 基本信息 (基本信息部分)
    name = db.Column(db.String(50), nullable=False, comment='学生姓名')
    gender = db.Column(db.String(10), nullable=False, comment='性别')
    ethnicity = db.Column(db.String(50), comment='民族')
    phone = db.Column(db.String(20), comment='联系电话')
    wechat_qq = db.Column(db.String(50), comment='微信/QQ')
    school = db.Column(db.String(100), comment='毕业学校')
    address = db.Column(db.String(200), comment='家庭住址')
    candidate_number = db.Column(db.String(50), comment='准考证号')
    id_card_number = db.Column(db.String(18), comment='身份证号')
    household_type = db.Column(db.String(20), comment='户籍类型') # 农村户口/城市户口
    student_type = db.Column(db.String(20), comment='考生类型') # a应届生/复读生
    # 新增政治面貌字段
    political_status = db.Column(db.String(20), comment='政治面貌') # 团员/党员
    # 新增出生日期字段
    birth_date = db.Column(db.Date, comment='出生日期')
    
    # 家长信息 (家长信息部分)
    # 新增关系字段
    guardian1_relation = db.Column(db.String(20), comment='第一联系人关系')
    guardian1_name = db.Column(db.String(50), comment='第一联系人姓名')
    guardian1_phone = db.Column(db.String(20), comment='第一联系人电话')
    # 新增关系字段
    guardian2_relation = db.Column(db.String(20), comment='第二联系人关系')
    guardian2_name = db.Column(db.String(50), comment='第二联系人姓名')
    guardian2_phone = db.Column(db.String(20), comment='第二联系人电话')
    
    # 身体情况 (身体情况部分)
    left_eye_vision = db.Column(db.String(20), comment='左眼视力情况')
    right_eye_vision = db.Column(db.String(20), comment='右眼视力情况')
    color_vision = db.Column(db.String(20), comment='色觉情况') # 色盲/色弱/单色异常/正常
    # 新增嗅觉情况字段
    smell_condition = db.Column(db.String(20), comment='嗅觉情况') # 异常/正常
    height = db.Column(db.String(10), comment='身高(CM)')
    weight = db.Column(db.String(10), comment='体重(KG)')
    # 其他情况
    other_condition = db.Column(db.String(500), comment='其他情况')
    
    # 外语语种
    foreign_language = db.Column(db.String(100), comment='外语语种')
    
    # 学科情况
    is_discredited = db.Column(db.Boolean, default=False, comment='是否失信考生')
    discredit_reason = db.Column(db.String(500), comment='失信原因')
    strong_subjects = db.Column(db.String(200), comment='优势科目')
    weak_subjects = db.Column(db.String(200), comment='劣势科目')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'gender': self.gender,
            'ethnicity': self.ethnicity,
            'phone': self.phone,
            'wechat_qq': self.wechat_qq,
            'school': self.school,
            'address': self.address,
            'candidate_number': self.candidate_number,
            'id_card_number': self.id_card_number,
            'household_type': self.household_type,
            'student_type': self.student_type,
            'political_status': self.political_status,
            'birth_date': self.birth_date,
            'guardian1_relation': self.guardian1_relation,
            'guardian1_name': self.guardian1_name,
            'guardian1_phone': self.guardian1_phone,
            'guardian2_relation': self.guardian2_relation,
            'guardian2_name': self.guardian2_name,
            'guardian2_phone': self.guardian2_phone,
            'left_eye_vision': self.left_eye_vision,
            'right_eye_vision': self.right_eye_vision,
            'color_vision': self.color_vision,
            'smell_condition': self.smell_condition,
            'height': self.height,
            'weight': self.weight,
            'other_condition': self.other_condition,
            'foreign_language': self.foreign_language,
            'is_discredited': self.is_discredited,
            'discredit_reason': self.discredit_reason,
            'strong_subjects': self.strong_subjects,
            'weak_subjects': self.weak_subjects,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    

class AcademicRecord(Base):
    """学生学业记录模型"""
    __tablename__ = 'academic_records'
    
    # 关联到学生表
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', backref=db.backref('academic_record', uselist=False))
    
    # 高考选科情况
    selected_subjects = db.Column(db.String(100), comment='高考选科') # 存储多选科目，以逗号分隔
    
    # 高考成绩
    gaokao_total_score = db.Column(db.String(20), comment='高考总分')
    gaokao_ranking = db.Column(db.String(20), comment='高考位次')
    standard_score = db.Column(db.String(20), comment='标准分数')
    # 拆分加分信息
    bonus_type = db.Column(db.String(50), comment='加分类型')
    bonus_detail = db.Column(db.String(200), comment='加分情况')
    
    # 分科目成绩
    chinese_score = db.Column(db.String(20), comment='语文成绩')
    math_score = db.Column(db.String(20), comment='数学成绩')
    foreign_lang_score = db.Column(db.String(20), comment='外语成绩')
    physics_score = db.Column(db.String(20), comment='物理成绩')
    history_score = db.Column(db.String(20), comment='历史成绩')
    chemistry_score = db.Column(db.String(20), comment='化学成绩')
    biology_score = db.Column(db.String(20), comment='生物成绩')
    geography_score = db.Column(db.String(20), comment='地理成绩')
    politics_score = db.Column(db.String(20), comment='政治成绩')
    
    # 模考成绩
    mock_exam_score = db.Column(db.String(20), comment='模考成绩')
    
    def to_dict(self):
        """转换为字典表示"""
        result = {
            'id': self.id,
            'student_id': self.student_id,
            'selected_subjects': self.selected_subjects,
            'gaokao_total_score': self.gaokao_total_score,
            'gaokao_ranking': self.gaokao_ranking,
            'standard_score': self.standard_score,
            'bonus_type': self.bonus_type,
            'bonus_detail': self.bonus_detail,
            'chinese_score': self.chinese_score,
            'math_score': self.math_score,
            'foreign_lang_score': self.foreign_lang_score,
            'physics_score': self.physics_score,
            'history_score': self.history_score,
            'chemistry_score': self.chemistry_score,
            'biology_score': self.biology_score,
            'geography_score': self.geography_score,
            'politics_score': self.politics_score,
            'mock_exam_score': self.mock_exam_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 添加排名信息（从ZwhScorerank表获取）
        ranking = None
        subject_type = None
        
        # 确定科别
        if self.selected_subjects:
            subjects = self.selected_subjects.split(',')
            if '物理' in subjects:
                subject_type = 2  # 物理组
            elif '历史' in subjects:
                subject_type = 1  # 历史组
                
        # 如果存在高考成绩且大于0 ，则使用高考成绩，否则使用模考成绩
        score = int(self.gaokao_total_score) if self.gaokao_total_score and int(self.gaokao_total_score) > 0 else int(self.mock_exam_score)
                
        # 获取排名
        if self.gaokao_ranking:
            ranking = self.gaokao_ranking
        elif score and subject_type:
            try:
                latest_year = 2025  # 最新年份
                
                # 查找最接近的分数记录
                rank_record = ZwhScorerank.query.filter(
                    ZwhScorerank.year == latest_year,
                    ZwhScorerank.suid == subject_type,
                    ZwhScorerank.scores <= score
                ).order_by(ZwhScorerank.scores.desc()).first()
                
                if rank_record:
                    ranking = rank_record.nums
                else:
                    ranking = self.gaokao_ranking
            except (ValueError, TypeError, Exception):
                ranking = self.gaokao_ranking
            
        result['ranking'] = ranking
        
        # 添加批次信息（本科/专科）
        education_level = None
        if score and subject_type:
            try:
                latest_year = 2025  # 最新年份
                
                # 查询本科批次线
                batch_record = ZwhXgkPicixian.query.filter(
                    ZwhXgkPicixian.dyear == latest_year,
                    ZwhXgkPicixian.suid == subject_type,
                    ZwhXgkPicixian.newbid == 11  # 本科批次
                ).first()
                
                if batch_record and batch_record.dscore:
                    # 比较分数和批次线
                    if score >= int(batch_record.dscore):
                        education_level = "本科"
                    else:
                        education_level = "专科"
            except (ValueError, TypeError, Exception):
                pass
                
        result['education_level'] = education_level
        
        return result