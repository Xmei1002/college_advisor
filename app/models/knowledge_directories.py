from app.extensions import db
from app.models.base import Base

class KnowledgeDirectory(Base):
    """知识库目录表"""
    __tablename__ = 'knowledge_directories'
    
    # 基础字段继承自Base模型(id, created_at, updated_at)
    title = db.Column(db.String(100), nullable=False, comment='目录标题')
    level = db.Column(db.Integer, default=1, comment='目录层级：1=顶级目录，2=子目录')
    parent_id = db.Column(db.Integer, db.ForeignKey('knowledge_directories.id'), nullable=True, comment='父目录ID')
    has_direct_content = db.Column(db.Boolean, default=False, comment='是否有直接内容')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    
    # 关系
    parent = db.relationship('KnowledgeDirectory', 
                            remote_side="KnowledgeDirectory.id", 
                            backref=db.backref('children', lazy='dynamic'))
    items = db.relationship('KnowledgeItem', backref='directory', lazy='dynamic', 
                           primaryjoin="and_(KnowledgeItem.directory_id==KnowledgeDirectory.id, "
                                      "KnowledgeItem.is_directory_content==False)")
    direct_content = db.relationship('KnowledgeItem', uselist=False, 
                                     primaryjoin="and_(KnowledgeItem.directory_id==KnowledgeDirectory.id, "
                                               "KnowledgeItem.is_directory_content==True)",
                                     backref='direct_directory')
    
    def to_dict(self, include_children=False, include_items=False):
        """转换为字典表示"""
        result = {
            'id': self.id,
            'title': self.title,
            'level': self.level,
            'parent_id': self.parent_id,
            'has_direct_content': self.has_direct_content,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_children:
            result['children'] = [child.to_dict() for child in self.children]
            
        if include_items:
            result['items'] = [item.to_dict() for item in self.items]
            
        return result