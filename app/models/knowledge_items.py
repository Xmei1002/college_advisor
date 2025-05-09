from app.extensions import db
from app.models.base import Base

class KnowledgeItem(Base):
    """知识条目表"""
    __tablename__ = 'knowledge_items'
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    title = db.Column(db.String(200), nullable=False, comment='条目标题')
    content = db.Column(db.Text, comment='纯文本内容')
    html_content = db.Column(db.Text, comment='HTML格式内容')
    directory_id = db.Column(db.Integer, db.ForeignKey('knowledge_directories.id'), nullable=False, comment='目录ID')
    is_directory_content = db.Column(db.Boolean, default=False, comment='是否为目录直接内容')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    
    # 额外字段 - 可能根据需求扩展
    views = db.Column(db.Integer, default=0, comment='浏览次数')
    tags = db.Column(db.String(500), comment='标签，逗号分隔')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-正常, 0-禁用')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'html_content': self.html_content,
            'directory_id': self.directory_id,
            'is_directory_content': self.is_directory_content,
            'sort_order': self.sort_order,
            'views': self.views,
            'tags': self.tags,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }