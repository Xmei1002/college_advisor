from flask import Flask, g, request
from app.config import Config
from app.extensions import db, migrate, jwt, socketio, cors, api_spec
from app.utils.logger import setup_logger
import logging
from app.utils.response import APIResponse
from app.extensions import init_celery, init_extensions
import os

def create_app(config_name=None):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')
    app.config.from_object(Config)
    Config.init_app(app)
    
    # 配置日志
    logger = setup_logger(app, log_level=logging.INFO)
    app.logger = logger
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    cors.init_app(app)
    socketio.init_app(app)
    api_spec.init_app(app)
    init_celery(app)
    init_extensions(app)  # 初始化缓存等其他扩展

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return APIResponse.error("认证已过期", code=401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return APIResponse.error("无效的认证令牌", code=401)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return APIResponse.error("缺少认证令牌", code=401)
    
    # 注册蓝图
    from app.api import api_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    # 注册错误处理
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 错误: {request.path}")
        return APIResponse.error("Not Found", code=404)
    
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 错误: {str(e)}", exc_info=True)
        return APIResponse.error("Internal Server Error", code=500)