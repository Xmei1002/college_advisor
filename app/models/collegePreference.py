from app.extensions import db
from app.models.base import Base

class CollegePreference(Base):
    """学生填报志愿意向信息模型"""
    __tablename__ = 'college_preferences'
    
    # 关联到学生表
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    student = db.relationship('Student', backref=db.backref('college_preference', uselist=False))
    
    # 意向地域
    preferred_locations = db.Column(db.String(500), comment='意向地域，多个地区以逗号分隔')
    
    # 意向学费范围（改为单一字符串字段）
    tuition_range = db.Column(db.String(50), comment='学费范围，如"1万以内"、"1-2万"等')
    
    # 意向专业
    preferred_majors = db.Column(db.String(1000), comment='意向专业，多个专业以逗号分隔')
    
    # 意向学校
    school_types = db.Column(db.String(100), comment='学校类型，如985,211,双一流等')
    preferred_schools = db.Column(db.String(1000), comment='意向学校，多个学校以逗号分隔')
    
    # 填报策略选择
    strategy = db.Column(db.String(20), comment='填报策略：院校优先 or 专业优先')
    
    # 报考倾向
    application_preference = db.Column(db.Text, comment='报考倾向：家庭背景资源、意向院校以及专业等情况的详细描述')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'preferred_locations': self.preferred_locations,
            'tuition_range': self.tuition_range,
            'preferred_majors': self.preferred_majors,
            'school_types': self.school_types,
            'preferred_schools': self.preferred_schools,
            'strategy': self.strategy,
            'application_preference': self.application_preference,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }