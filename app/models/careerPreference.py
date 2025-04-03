from app.extensions import db
from app.models.base import Base

class CareerPreference(Base):
    """学生就业倾向信息模型"""
    __tablename__ = 'career_preferences'
    
    # 关联到学生表
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    student = db.relationship('Student', backref=db.backref('career_preference', uselist=False))
    
    # 就业发展方向
    career_direction = db.Column(db.String(50), comment='就业发展方向，如金融,教师,医生等')
    
    # 学术学位偏好
    academic_preference = db.Column(db.String(100), comment='学术学位偏好，如985,211等')
    
    # 公务员意向
    civil_service_preference = db.Column(db.String(100), comment='公务员意向')
    
    # 就业区域
    employment_location = db.Column(db.String(100), comment='就业地区')
    
    # 职业综合性收入预期
    income_expectation = db.Column(db.String(100), comment='职业稳定性与收入平衡')
    
    # 其他考虑因素
    work_stability = db.Column(db.String(100), comment='工作稳定性')

    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'career_direction': self.career_direction,
            'academic_preference': self.academic_preference,
            'civil_service_preference': self.civil_service_preference,
            'employment_location': self.employment_location,
            'income_expectation': self.income_expectation,
            'work_stability': self.work_stability,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }