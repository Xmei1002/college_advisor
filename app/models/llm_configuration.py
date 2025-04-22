# app/models/llm_configuration.py
from app.extensions import db
from app.models.base import Base

class LLMConfiguration(Base):
    """LLM配置模型"""
    __tablename__ = 'llm_configurations'
    
    # 提供者常量
    PROVIDER_MOONSHOT = 'moonshot'
    PROVIDER_DEEPSEEK = 'deepseek'
    PROVIDER_ZHIPU = 'zhipu'
    
    # 所有支持的提供者列表
    PROVIDERS = [PROVIDER_MOONSHOT, PROVIDER_DEEPSEEK, PROVIDER_ZHIPU]
    
    # 默认提供者
    DEFAULT_PROVIDER = PROVIDER_MOONSHOT
    
    provider = db.Column(db.String(50), nullable=False, comment='提供者名称(moonshot/deepseek/zhipu等)')
    is_active = db.Column(db.Boolean, default=False, comment='是否激活')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'provider': self.provider,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def get_active_provider(cls):
        """获取当前活跃的提供者名称"""
        config = cls.query.filter_by(is_active=True).first()
        return config.provider if config else cls.DEFAULT_PROVIDER
    
    @classmethod
    def set_active_provider(cls, provider):
        """设置活跃的提供者"""
        if provider not in cls.PROVIDERS:
            raise ValueError(f"不支持的提供者: {provider}")
        
        # 取消所有活跃配置
        cls.query.filter_by(is_active=True).update({'is_active': False})
        
        # 查找或创建新的配置
        config = cls.query.filter_by(provider=provider).first()
        if not config:
            config = cls(provider=provider)
            db.session.add(config)
        
        # 设置为活跃
        config.is_active = True
        db.session.commit()
        
        return config