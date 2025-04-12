from app.extensions import db
from app.models.base import Base

class Message(Base):
    """消息表"""
    __tablename__ = 'messages'
    
    # 消息角色常量
    ROLE_STUDENT = 'student'     # 学生消息
    ROLE_PLANNER = 'planner'     # 规划师消息
    ROLE_AI = 'ai'               # AI消息
    ROLE_SYSTEM = 'system'       # 系统消息
    
    # 消息类型常量
    TYPE_TEXT = 'text'           # 文本消息
    TYPE_IMAGE = 'image'         # 图片消息
    TYPE_FILE = 'file'           # 文件消息
    TYPE_CARD = 'card'           # 卡片消息(如院校卡片、专业卡片)
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, comment='会话ID')
    sender_id = db.Column(db.Integer, nullable=True, comment='发送者ID，系统或AI消息为空')
    role = db.Column(db.String(20), nullable=False, comment='消息角色')
    message_type = db.Column(db.String(20), default=TYPE_TEXT, comment='消息类型')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    
    # 索引
    __table_args__ = (
        db.Index('idx_conversation', 'conversation_id'),
        db.Index('idx_sender', 'sender_id'),
        db.Index('idx_conversation_created', 'conversation_id', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典表示"""
        result = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'role': self.role,
            'message_type': self.message_type,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        return result