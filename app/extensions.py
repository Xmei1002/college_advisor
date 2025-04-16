from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from celery import Celery
from flask_smorest import Api as ApiSpec
from flask_caching import Cache

# 初始化扩展，但不绑定到特定应用
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
cors = CORS()
celery = Celery(__name__)
api_spec = ApiSpec()

# 初始化缓存
cache = Cache()

def init_celery(app=None):
    if app:
        celery.conf.update(
            broker_url=app.config["CELERY_BROKER_URL"],
            result_backend=app.config["CELERY_RESULT_BACKEND"],
            result_expires=app.config.get("CELERY_RESULT_EXPIRES", 60 * 60 * 24)  # 默认1天过期
        )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
                
    celery.Task = ContextTask
    return celery

def init_extensions(app):
    """初始化所有扩展"""
    # 初始化缓存
    cache.init_app(app, config={
        'CACHE_TYPE': 'redis',  # 使用Redis缓存
        'CACHE_REDIS_URL': app.config["CELERY_BROKER_URL"],  # 使用与Celery相同的Redis连接
        'CACHE_DEFAULT_TIMEOUT': 3600  # 默认缓存时间1小时
    })