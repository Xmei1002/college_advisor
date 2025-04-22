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
    
    # 意向学费范围
    tuition_range = db.Column(db.String(50), comment='学费范围，如"1万以内"、"1-2万"等')
    
    # 意向专业
    preferred_majors = db.Column(db.String(1000), comment='意向专业，多个专业以逗号分隔')
    
    # 意向学校
    school_types = db.Column(db.String(100), comment='学校类型，如985,211,双一流等')
    preferred_schools = db.Column(db.String(1000), comment='意向学校，多个学校以逗号分隔')
    
    # 填报策略选择
    strategy = db.Column(db.String(20), comment='填报策略：冲刺院校，兼顾专业 or 冲刺专业方向，院校其次')
    
    # 报考倾向(其他意向)
    application_preference = db.Column(db.Text, comment='其他意向')
    
    # 新增家庭背景字段
    family_background = db.Column(db.Text, comment='家庭背景详细描述，包括家庭经济状况、父母职业、教育背景等')
    
    # 志愿梯度策略
    volunteer_gradient_strategy = db.Column(db.String(20), comment='志愿梯度策略：稳妥类型/激进类型/保底类型/自由设置')
    
    # 自定义梯度数量字段
    custom_gradient_counts = db.Column(db.JSON, comment='自定义志愿梯度数量，JSON格式：{"chasing": 10, "stable": 15, "safe": 23}')
    
    # 报考批次
    application_batch = db.Column(db.String(50), comment='报考批次：本科批/专科批，多选')
    
    # ===== 从 ApplicationRestrictions 模型合并的字段 =====
    # 报考限制字段
    accept_nonchangeable_major = db.Column(db.Boolean, nullable=True, comment='是否接受不可转专业中外合办专业')
    has_art_foundation = db.Column(db.Boolean, nullable=True, comment='是否具备美术基础')
    accept_overseas_study = db.Column(db.Boolean, nullable=True, comment='是否接受大学期间需出国就读')
    accept_high_fee_increase = db.Column(db.Boolean, nullable=True, comment='是否接受学费刺客专业')
    accept_dual_city_arrangement = db.Column(db.Boolean, nullable=True, comment='是否接受在两个城市上学安排')
    
    # ===== 从 CareerPreference 模型合并的字段 =====
    career_direction = db.Column(db.String(100), comment='就业发展方向，如金融,教师,医生等')

    def set_custom_gradient(self, chasing_count, stable_count, safe_count):
        """设置自定义志愿梯度数量"""
        self.custom_gradient_counts = {
            "chasing": chasing_count,  # 冲刺志愿数量
            "stable": stable_count,    # 稳妥志愿数量
            "safe": safe_count         # 保底志愿数量
        }
    
    def get_gradient_counts(self):
        """获取志愿梯度数量"""
        # 如果是自定义设置且已有自定义数据
        if self.volunteer_gradient_strategy == "自由设置" and self.custom_gradient_counts:
            return self.custom_gradient_counts
            
        # 如果不是自定义设置或没有自定义数据，返回预设值
        if self.volunteer_gradient_strategy == "稳妥类型":
            return {"chasing": 16, "stable": 16, "safe": 16}
        elif self.volunteer_gradient_strategy == "激进类型":
            return {"chasing": 20, "stable": 12, "safe": 12}
        elif self.volunteer_gradient_strategy == "保底类型":
            return {"chasing": 0, "stable": 16, "safe": 32}
        else:
            # 默认为稳妥类型
            return {"chasing": 16, "stable": 16, "safe": 16}
    
    def to_dict(self, send_ai=False):
        """转换为字典表示"""
        base_dict = {
            'id': self.id,
            'student_id': self.student_id,
            'preferred_locations': self.preferred_locations,
            'tuition_range': self.tuition_range,
            'preferred_majors': self.preferred_majors,
            'school_types': self.school_types,
            'preferred_schools': self.preferred_schools,
            'strategy': self.strategy,
            'application_preference': self.application_preference,
            'volunteer_gradient_strategy': self.volunteer_gradient_strategy,
            'application_batch': self.application_batch,
            'gradient_counts': self.get_gradient_counts(),
            'accept_nonchangeable_major': self.accept_nonchangeable_major,
            'has_art_foundation': self.has_art_foundation,
            'accept_overseas_study': self.accept_overseas_study,
            'accept_high_fee_increase': self.accept_high_fee_increase,
            'accept_dual_city_arrangement': self.accept_dual_city_arrangement,
            'family_background': self.family_background,
            'career_direction': self.career_direction,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if send_ai:
            # 精简版本用于发送给AI
            return {
                'preferred_locations': self.preferred_locations,
                'tuition_range': self.tuition_range,
                'preferred_majors': self.preferred_majors,
                'preferred_schools': self.preferred_schools,
                'strategy': self.strategy,
                'application_preference': self.application_preference,
                'volunteer_gradient_strategy': self.volunteer_gradient_strategy,
                'application_batch': self.application_batch,
                'gradient_counts': self.get_gradient_counts(),
                'accept_nonchangeable_major': self.accept_nonchangeable_major,
                'has_art_foundation': self.has_art_foundation,
                'accept_overseas_study': self.accept_overseas_study,
                'family_background': self.family_background,
                'accept_high_fee_increase': self.accept_high_fee_increase,
                'accept_dual_city_arrangement': self.accept_dual_city_arrangement,
                'career_direction': self.career_direction,
            }
        else:
            return base_dict