from flask import Blueprint
from app.extensions import api_spec
# 导入健康检查蓝图
from app.api.endpoints.health import health_bp
from app.api.endpoints.auth import auth_bp

# 创建主API蓝图
api_bp = Blueprint('api', __name__)
def register_blueprint(blueprint, url_prefix):
    """
    同时注册蓝图到API文档和主API蓝图
    
    :param blueprint: 要注册的蓝图
    :param url_prefix: URL前缀
    """
    # 注册到API文档
    api_spec.register_blueprint(blueprint, url_prefix=url_prefix)
    
    # 注册到主API蓝图
    api_bp.register_blueprint(blueprint, url_prefix=url_prefix)
    
    return blueprint

# 注册蓝图
register_blueprint(health_bp, '/health')
register_blueprint(auth_bp, '/auth')