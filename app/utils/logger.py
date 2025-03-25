import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import request, has_request_context

# 确保日志目录存在
def ensure_log_dir(log_dir='logs'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# 请求信息格式化器
class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            if hasattr(request, 'authenticated_user'):
                record.user_id = request.authenticated_user.id
            else:
                record.user_id = 'anonymous'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.user_id = None
            
        return super().format(record)

def setup_logger(app, log_level=logging.INFO):
    """
    配置应用的日志系统
    
    参数:
        app: Flask应用实例
        log_level: 日志级别，默认为INFO
    """
    log_dir = ensure_log_dir()
    
    # 设置日志格式
    formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s: '
        'url: %(url)s | method: %(method)s | user: %(user_id)s | '
        'remote_addr: %(remote_addr)s | '
        '%(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 文件处理器 - 按大小轮转
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'  # 新增编码参数
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 错误日志处理器 - 按时间轮转
    error_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        when='D',  # 每天
        interval=1,
        backupCount=30,
        encoding='utf-8'  # 新增编码参数

    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    
    # 获取应用日志器
    app_logger = logging.getLogger(app.name)
    app_logger.setLevel(log_level)
    
    # 添加处理器
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(error_file_handler)
    
    # SQLAlchemy日志
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_handler = RotatingFileHandler(
        os.path.join(log_dir, 'sql.log'),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'  # 新增编码参数

    )
    sql_handler.setFormatter(formatter)
    sql_logger.addHandler(sql_handler)
    sql_logger.setLevel(logging.WARNING)  # 生产环境设为WARNING，开发环境可设为INFO
    
    # Celery日志
    celery_logger = logging.getLogger('celery')
    celery_handler = RotatingFileHandler(
        os.path.join(log_dir, 'celery.log'),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'  # 新增编码参数

    )
    celery_handler.setFormatter(formatter)
    celery_logger.addHandler(celery_handler)
    celery_logger.setLevel(log_level)
    
    return app_logger

# 获取自定义模块的日志器
def get_logger(name):
    """
    获取特定模块的日志器
    
    参数:
        name: 模块名称
    """
    logger = logging.getLogger(name)
    return logger