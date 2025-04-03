from app.extensions import db
from app.models.base import Base
from app.models.user import User  # 导入User模型

class PlannerInfo(Base):
    """咨询师详细信息表"""
    __tablename__ = 'planner_info'
    
    # 修改外键引用，使用User.__tablename__确保正确引用
    user_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'), unique=True, nullable=False, comment='关联的用户ID')
    phone = db.Column(db.String(20), comment='联系电话')
    address = db.Column(db.String(255), comment='地址')
    
    # 定义关系
    user = db.relationship('User', backref=db.backref('planner_info', uselist=False, lazy='joined'))
    
    def __repr__(self):
        return f'<PlannerInfo {self.user_id}>'
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }