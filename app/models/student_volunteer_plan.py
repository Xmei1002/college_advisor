from app.extensions import db
from app.models.base import Base

class StudentVolunteerPlan(Base):
    """学生志愿方案表"""
    __tablename__ = 'student_volunteer_plans'
    
    # 方案生成状态常量
    GENERATION_STATUS_PENDING = 'pending'       # 等待生成
    GENERATION_STATUS_PROCESSING = 'processing' # 正在生成
    GENERATION_STATUS_SUCCESS = 'success'       # 生成成功
    GENERATION_STATUS_FAILED = 'failed'         # 生成失败
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    planner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='规划师ID')
    version = db.Column(db.Integer, default=1, nullable=False, comment='版本号')
    is_current = db.Column(db.Boolean, default=True, nullable=False, comment='是否当前版本')
    remarks = db.Column(db.String(500), comment='备注说明')
    generation_status = db.Column(db.String(20), default=GENERATION_STATUS_PENDING, comment='AI生成状态')
    generation_progress = db.Column(db.Integer, default=0, comment='生成进度百分比(0-100)')
    generation_message = db.Column(db.String(255), comment='生成过程信息或错误信息')
    user_data_hash = db.Column(db.String(64), comment='用户数据哈希，用于检测用户数据是否变化')
    student_data_snapshot = db.Column(db.Text, comment='生成方案时的学生数据快照，JSON格式')
    data_changes = db.Column(db.Text, comment='与上一版方案相比的数据变化描述')

    # 关系
    volunteers = db.relationship('VolunteerCollege', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        db.Index('idx_student_current', 'student_id', 'is_current'),
        db.Index('idx_student_version', 'student_id', 'version'),
    )
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,  # 学生的id
            'student_id': self.student_id, 
            'planner_id': self.planner_id,
            'version': self.version,
            'is_current': self.is_current,
            'remarks': self.remarks,
            'generation_status': self.generation_status,
            'generation_progress': self.generation_progress,
            'generation_message': self.generation_message,
            'data_changes': self.data_changes,
            'student_data_snapshot': self.student_data_snapshot,
            'user_data_hash': self.user_data_hash,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
class VolunteerCollege(Base):
    """志愿详情表"""
    __tablename__ = 'volunteer_colleges'
    
    # 推荐类型常量
    RECOMMEND_AI = 'ai'             # AI推荐
    RECOMMEND_PLANNER = 'planner'   # 规划师调整
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    plan_id = db.Column(db.Integer, db.ForeignKey('student_volunteer_plans.id'), nullable=False, comment='志愿方案ID')
    category_id = db.Column(db.Integer, nullable=False, comment='类别ID(1:冲, 2:稳, 3:保)')
    group_id = db.Column(db.Integer, nullable=False, comment='志愿段ID(1-12)')
    volunteer_index = db.Column(db.Integer, nullable=False, comment='志愿在方案中的序号(1-48)')
    college_id = db.Column(db.Integer, nullable=False, comment='院校ID')
    college_name = db.Column(db.String(100), nullable=False, comment='院校名称')
    college_group_id = db.Column(db.Integer, nullable=False, comment='院校专业组ID')
    score_diff = db.Column(db.Integer, comment='分差')
    prediction_score = db.Column(db.Integer, comment='预测分数')
    recommend_type = db.Column(db.String(20), default=RECOMMEND_AI, nullable=False, comment='推荐类型(ai/planner)')
    ai_analysis = db.Column(db.Text, comment='AI解析结果，包含推荐理由等信息')
    area_name = db.Column(db.String(100), comment='地区名称，如"河南省郑州市"')
    group_name = db.Column(db.String(100), comment='专业组名称，如"第121组"')
    min_tuition = db.Column(db.Integer, comment='最低学费')
    max_tuition = db.Column(db.Integer, comment='最高学费')
    min_score = db.Column(db.Integer, comment='最低分数')
    plan_number = db.Column(db.Integer, comment='计划招生人数')
    school_type_text = db.Column(db.String(50), comment='学校类型文本，如"工科"')
    subject_requirements = db.Column(db.JSON, comment='选科要求，格式为JSON对象')
    tese_text = db.Column(db.JSON, comment='特色文本数组，如["省部共建", "硕博点"]')
    teshu_text = db.Column(db.JSON, comment='特殊类型文本数组')
    uncode = db.Column(db.String(20), comment='院校代码，如"6110"')
    nature = db.Column(db.String(20), comment='院校性质，如"公办"')
    # 关系
    specialties = db.relationship('VolunteerSpecialty', backref='volunteer', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        db.Index('idx_plan', 'plan_id'),
        db.Index('idx_category_group', 'plan_id', 'category_id', 'group_id'),
        db.UniqueConstraint('plan_id', 'volunteer_index', name='unique_volunteer_index'),
    )
    
    def to_dict(self, include_specialties=False):
        """转换为字典表示"""
        result = {
            'id': self.id,
            'plan_id': self.plan_id,
            'category_id': self.category_id,
            'group_id': self.group_id,
            'volunteer_index': self.volunteer_index,
            'college_id': self.college_id,
            'college_name': self.college_name,
            'college_group_id': self.college_group_id,
            'score_diff': self.score_diff,
            'prediction_score': self.prediction_score,
            'recommend_type': self.recommend_type,
            'ai_analysis': self.ai_analysis,
            'area_name': self.area_name,
            'group_name': self.group_name,
            'min_tuition': self.min_tuition,
            'max_tuition': self.max_tuition,
            'min_score': self.min_score,
            'plan_number': self.plan_number,
            'school_type_text': self.school_type_text,
            'subject_requirements': self.subject_requirements,
            'tese_text': self.tese_text,
            'teshu_text': self.teshu_text,
            'nature': self.nature,
            'uncode': self.uncode,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_specialties:
            result['specialties'] = [specialty.to_dict() for specialty in self.specialties]
            
        return result


class VolunteerSpecialty(Base):
    """专业选择表"""
    __tablename__ = 'volunteer_specialties'
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    volunteer_college_id = db.Column(db.Integer, db.ForeignKey('volunteer_colleges.id'), nullable=False, comment='志愿ID')
    specialty_id = db.Column(db.Integer, nullable=False, comment='专业ID')
    specialty_code = db.Column(db.String(50), comment='专业代码')
    specialty_name = db.Column(db.String(100), nullable=False, comment='专业名称')
    specialty_index = db.Column(db.Integer, nullable=False, comment='专业在志愿中的排序(1-6)')
    prediction_score = db.Column(db.Integer, comment='专业预测分数')
    plan_number = db.Column(db.Integer, comment='计划招生人数')
    tuition = db.Column(db.Integer, comment='学费')
    remarks = db.Column(db.String(500), comment='专业备注')
    ai_analysis = db.Column(db.Text, comment='AI对该专业的解析结果，包含适配度分析等信息')
    fenshuxian_id = db.Column(db.Integer, comment='关联到分数线表(zwh_xgk_fenshuxian_2025)的ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_volunteer', 'volunteer_college_id'),
        db.Index('idx_fenshuxian', 'fenshuxian_id'),  # 添加索引提高关联查询性能
        db.UniqueConstraint('volunteer_college_id', 'specialty_index', name='unique_specialty_index'),
    )
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'volunteer_college_id': self.volunteer_college_id,
            'specialty_id': self.specialty_id,
            'specialty_code': self.specialty_code,
            'specialty_name': self.specialty_name,
            'specialty_index': self.specialty_index,
            'prediction_score': self.prediction_score,
            'plan_number': self.plan_number,
            'tuition': self.tuition,
            'remarks': self.remarks,
            'ai_analysis': self.ai_analysis,
            'fenshuxian_id': self.fenshuxian_id,  # 添加到返回数据中
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    

class VolunteerCategoryAnalysis(Base):
    """志愿类别分析表"""
    __tablename__ = 'volunteer_category_analyses'
    
    # 状态常量
    STATUS_PENDING = 'pending'       # 等待分析
    STATUS_PROCESSING = 'processing' # 正在分析
    STATUS_COMPLETED = 'completed'   # 分析完成
    STATUS_FAILED = 'failed'         # 分析失败
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    plan_id = db.Column(db.Integer, db.ForeignKey('student_volunteer_plans.id'), nullable=False, comment='志愿方案ID')
    category_id = db.Column(db.Integer, nullable=False, comment='类别ID(1:冲, 2:稳, 3:保)')
    analysis_content = db.Column(db.Text, comment='AI分析内容')
    status = db.Column(db.String(20), default=STATUS_PENDING, comment='分析状态')
    analyzed_at = db.Column(db.DateTime, comment='分析完成时间')
    error_message = db.Column(db.Text, comment='错误信息，当状态为failed时有值')
    
    # 关系
    plan = db.relationship('StudentVolunteerPlan', backref=db.backref('category_analyses', lazy='dynamic'))
    
    # 索引与约束
    __table_args__ = (
        db.Index('idx_plan_category', 'plan_id', 'category_id'),
        db.UniqueConstraint('plan_id', 'category_id', name='unique_plan_category'),
    )
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'category_id': self.category_id,
            'analysis_content': self.analysis_content,
            'status': self.status,
            'error_message': self.error_message,
            'analyzed_at': self.analyzed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }