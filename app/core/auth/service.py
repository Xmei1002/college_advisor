from app.models.user import User
from app.extensions import db
from flask_jwt_extended import create_access_token, create_refresh_token

class AuthService:
    @staticmethod
    def register_student(username, password):
        """注册学生用户"""
        user = User(
            username=username,
            user_type=User.USER_TYPE_STUDENT
        )
        user.password = password
        user.save()
        return user
    
    @staticmethod
    def create_planner(username, password):
        """创建规划师用户（由管理员）"""
        user = User(
            username=username,
            user_type=User.USER_TYPE_PLANNER
        )
        user.password = password
        user.save()
        return user
    
    @staticmethod
    def authenticate(username, password):
        """验证用户"""
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            return user
        return None
    
    @staticmethod
    def generate_tokens(user):
        """生成JWT令牌"""
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }