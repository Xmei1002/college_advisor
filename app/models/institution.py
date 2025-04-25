# app/models/institution.py
from app.extensions import db
from app.models.base import Base
from app.services.storage.file_service import FileService

class Institution(Base):
    """机构信息模型"""
    __tablename__ = 'institutions'
    
    name = db.Column(db.String(100), nullable=False, comment='机构名称')
    address = db.Column(db.String(200), comment='机构地址')
    qrcode_path = db.Column(db.String(255), comment='机构二维码图片路径')
    logo_path = db.Column(db.String(255), comment='机构logo图片路径')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    contact_email = db.Column(db.String(100), comment='联系邮箱')
    description = db.Column(db.Text, comment='机构描述')
    status = db.Column(db.Integer, default=1, comment='状态：1-激活, 0-禁用')
    
    # 关联关系
    users = db.relationship('User', backref='institution', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'qrcode_path': self.qrcode_path,
            'logo_path': self.logo_path,
            'qrcode_url': FileService.get_file_url(self.qrcode_path) if self.qrcode_path else None,
            'logo_url': FileService.get_file_url(self.logo_path) if self.logo_path else None,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }