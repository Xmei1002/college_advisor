from app.extensions import db
from app.models.base import Base

class PromptTemplate(Base):
    """存储系统中使用的各种提示词模板"""
    __tablename__ = 'prompt_templates'
    
    # 提示词类型常量
    TYPE_ANALYZING_FULL_PLAN = 'analyzing_full_plan'  # 整体志愿方案解读
    TYPE_ANALYZING_CATEGORY = 'analyzing_category'    # 分层志愿解读
    TYPE_ANALYZING_COLLEGE = 'analyzing_college'      # 院校分析
    TYPE_CAREER_ANALYZING_PROMPT = 'career_analyzing_prompt'    # 就业倾向解析提示词
    TYPE_CITY_ANALYZING_PROMPT = 'city_analyzing_prompt'        # 地域意向解析提示词
    TYPE_MAJOR_ANALYZING_PROMPT = 'major_analyzing_prompt'      # 专业意向解析提示词
    TYPE_COLLEGE_ANALYZING_PROMPT = 'college_analyzing_prompt'  # 意向院校解析提示词
    TYPE_STRATEGY_ANALYZING_PROMPT = 'strategy_analyzing_prompt'  # 院校专业策略解析提示词
    TYPE_S_SUBJECT_ANALYZING_PROMPT = 's_subject_analyzing_prompt'  # 优势学科解析提示词
    TYPE_W_SUBJECT_ANALYZING_PROMPT = 'w_subject_analyzing_prompt'  # 劣势学科解析提示词
    
    # 字段定义
    name = db.Column(db.String(100), nullable=False, comment='提示词名称')
    type = db.Column(db.String(50), nullable=False, comment='提示词类型')
    content = db.Column(db.Text, nullable=False, comment='提示词内容')
    description = db.Column(db.String(255), comment='提示词描述')

    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'content': self.content,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def get_prompt_by_type(cls, type):
        """获取指定类型的活跃提示词"""
        return cls.query.filter_by(type=type).first() 