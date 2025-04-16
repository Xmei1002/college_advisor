from app.extensions import db
from app.models.base import Base
from datetime import datetime

class Conversation(Base):
    """会话表"""
    __tablename__ = 'conversations'
    
    # 会话类型常量
    TYPE_CHANGEINFO = 'changeinfo'  # 信息修改
    TYPE_VOLUNTEER = 'volunteer'    # 志愿填报咨询
    TYPE_EXPLAININFO = 'explaininfo'
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    student_id = db.Column(db.Integer, nullable=False, comment='学生ID')
    planner_id = db.Column(db.Integer, nullable=False, comment='规划师ID')
    title = db.Column(db.String(100), nullable=False, comment='会话标题')
    conversation_type = db.Column(db.String(20), default=TYPE_VOLUNTEER, comment='会话类型')
    last_message_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='最后消息时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否活跃')
    is_archived = db.Column(db.Boolean, default=False, comment='是否归档')
    meta_data = db.Column(db.Text, comment='会话相关元数据，如关联专业、院校等信息')
    
    # 关系 - 保留级联删除
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        db.Index('idx_student_planner', 'student_id', 'planner_id'),
        db.Index('idx_last_message', 'last_message_time'),
    )
    
    def to_dict(self, include_messages=False):
        """转换为字典表示"""
        result = {
            'id': self.id,
            'student_id': self.student_id,
            'planner_id': self.planner_id,
            'title': self.title,
            'conversation_type': self.conversation_type,
            'last_message_time': self.last_message_time,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'meta_data': self.meta_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_messages:
            result['messages'] = [message.to_dict() for message in self.messages]
            
        return result