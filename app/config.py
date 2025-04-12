# app/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载不同环境的.env文件
def load_env_file(env_name):
    """根据环境加载对应的环境变量文件"""
    if env_name == 'production':
        env_file = '.env.production'
    elif env_name == 'testing':
        env_file = '.env.testing'
    else:
        env_file = '.env.development'
    
    # 尝试加载指定环境的文件
    if os.path.exists(env_file):
        load_dotenv(env_file)
    # 始终加载默认的.env文件作为后备
    load_dotenv('.env')

# 获取当前环境
env = os.environ.get('FLASK_ENV', 'development')
# 加载对应环境的配置
load_env_file(env)

class Config:
    """应用配置"""
    # 应用基本配置
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    TESTING = os.environ.get('FLASK_TESTING', '0') == '1'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_DAYS', 15))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    )
    
    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # API文档配置
    API_TITLE = os.environ.get('API_TITLE', 'College Advisor API')
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    
    
    @staticmethod
    def init_app(app):
        pass
