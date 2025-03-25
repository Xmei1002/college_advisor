from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import Base

class User(Base):
    """用户认证模型"""
    __tablename__ = 'users'
    
    # 认证字段
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    _password_hash = db.Column(db.String(256), nullable=False)
    
    # 用户类型
    USER_TYPE_STUDENT = 'student'
    USER_TYPE_PLANNER = 'planner'
    
    user_type = db.Column(db.String(20), nullable=False)
    
    # 用户状态
    USER_STATUS_ACTIVE = 'active'
    USER_STATUS_INACTIVE = 'inactive'
    
    status = db.Column(db.String(20), default=USER_STATUS_ACTIVE)
    
    # 简单的登录记录
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(50), nullable=True)
    
    @property
    def password(self):
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)
    
    def is_student(self):
        return self.user_type == self.USER_TYPE_STUDENT
    
    def is_planner(self):
        return self.user_type == self.USER_TYPE_PLANNER
    
    def update_login_info(self, ip):
        self.last_login_at = datetime.now(timezone.utc)
        self.last_login_ip = ip
        db.session.commit()
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'status': self.status,
            'created_at': self.created_at,
            'last_login_at': self.last_login_at
        }
