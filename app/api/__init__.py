from flask import Blueprint
from app.extensions import api_spec
# 导入健康检查蓝图
from app.api.endpoints.health import health_bp
from app.api.endpoints.auth import auth_bp
from app.api.endpoints.student import student_bp
from app.api.endpoints.preference import preference_bp  # 导入志愿填报意向蓝图
from app.api.endpoints.planner import planner_bp  # 导入规划师蓝图
from app.api.endpoints.planner_management import planner_management_bp  # 导入规划师管理蓝图
from app.api.endpoints.recommendation import recommendation_bp
from app.api.endpoints.base_data import base_data_bp
from app.api.endpoints.volunteer_plan import volunteer_plan_bp
from app.api.endpoints.volunteer_analysis import volunteer_analysis_bp  # 导入志愿分析蓝图
from app.api.endpoints.tasks import tasks_bp  # 导入任务蓝图
from app.api.endpoints.chat import chat_bp  # 导入聊天蓝图
from app.api.endpoints.config import config_bp  # 导入配置蓝图
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
register_blueprint(tasks_bp, '/tasks')
register_blueprint(auth_bp, '/auth')
register_blueprint(student_bp, '/students')  # 注册学生蓝图
register_blueprint(preference_bp, '/preference')  # 志愿填报意向接口
register_blueprint(planner_bp, '/planners')  # 规划师与学生关系接口
register_blueprint(planner_management_bp, '/planner-management')  # 规划师账号管理接口
register_blueprint(recommendation_bp, '/recommendation')
register_blueprint(base_data_bp, '/base-data')
register_blueprint(volunteer_plan_bp, '/volunteer-plans')
register_blueprint(volunteer_analysis_bp, '/volunteer-analysis')  # 注册志愿分析蓝图
register_blueprint(chat_bp, '/chat')  # 注册聊天蓝图
register_blueprint(config_bp, '/config')  # 注册配置蓝图


