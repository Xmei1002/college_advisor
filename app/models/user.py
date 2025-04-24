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
    USER_TYPE_ADMIN = 'admin'
    
    user_type = db.Column(db.String(20), nullable=False)
    
    # 用户状态
    USER_STATUS_ACTIVE = 'active'
    USER_STATUS_INACTIVE = 'inactive'

    CONSULTATION_STATUS_PENDING = '待咨询'  # 待咨询
    CONSULTATION_STATUS_IN_PROGRESS = '咨询中'  # 咨询中
    CONSULTATION_STATUS_COMPLETED = '已完成'  # 已完成咨询
    CONSULTATION_STATUS_FOLLOW_UP = '需跟进'  # 需要跟进

    status = db.Column(db.String(20), default=USER_STATUS_ACTIVE)
    
    # 简单的登录记录
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(50), nullable=True)
    planner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    consultation_status = db.Column(db.String(20), comment='学生用户咨询状态')
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True, comment='所属机构ID')

    students = db.relationship(
        'User', 
        backref=db.backref('planner', remote_side='User.id'),  # 使用字符串引用列
        foreign_keys=[planner_id]
    )

    @property
    def password(self):
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)
    
    def is_student(self):
        return self.user_type == self.USER_TYPE_STUDENT
    
    def is_planner(self):
        return self.user_type == self.USER_TYPE_PLANNER
    
    def is_admin(self):
        """判断用户是否为管理员"""
        return self.user_type == self.USER_TYPE_ADMIN
    
    # 更新登录信息
    def update_login_info(self, ip):
        self.last_login_at = datetime.now(timezone.utc)
        self.last_login_ip = ip
        db.session.commit()
    
    # 添加分配规划师的方法
    def assign_planner(self, planner):
        """为学生分配规划师"""
        if not self.is_student():
            raise ValueError("只有学生可以被分配规划师")
        
        if not planner.is_planner():
            raise ValueError("只有规划师可以被分配给学生")
            
        self.planner_id = planner.id
        db.session.commit()
        
    # 获取我的学生列表
    def get_students(self):
        """获取当前规划师的学生列表"""
        if not self.is_planner():
            raise ValueError("只有规划师可以查看学生列表")
            
        return User.query.filter_by(planner_id=self.id).all()
    
    def to_dict(self, include_student_profile=False):
        """转换为字典表示
        
        Args:
            include_student_profile: 是否包含学生详细信息
        """
        result = {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'planner_id': self.planner_id if self.planner_id else None,
            'status': self.status,
            'created_at': self.created_at,
            'last_login_at': self.last_login_at,
            'consultation_status': self.consultation_status,
            'planner_info': self.planner_info.to_dict() if hasattr(self, 'planner_info') and self.planner_info else None
        }
        
        # 如果是学生且有规划师，添加规划师信息
        if self.is_student() and self.planner:
            result['planner'] = {
                'id': self.planner.id,
                'username': self.planner.username
            }
            # 添加规划师详细信息（如果存在）
            if hasattr(self.planner, 'planner_info') and self.planner.planner_info:
                result['planner']['planner_info'] = self.planner.planner_info.to_dict()
            
        # 如果是规划师，可以添加学生数量信息
        if self.is_planner():
            result['student_count'] = User.query.filter_by(planner_id=self.id).count()
        
        # 如果是学生且需要包含详细信息
        if self.is_student() and include_student_profile:
            # 添加学生个人资料
            if hasattr(self, 'student_profile'):
                result['student_profile'] = self.student_profile.to_dict() if self.student_profile else None
            
            # 添加学业记录
            if hasattr(self, 'student_profile') and self.student_profile and hasattr(self.student_profile, 'academic_record'):
                result['academic_record'] = self.student_profile.academic_record.to_dict() if self.student_profile.academic_record else None
            
        return result