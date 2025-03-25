from flask import Blueprint, current_app
from flask_smorest import Blueprint
from datetime import datetime
import os

from app.api.schemas import HealthSchema
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler

# 创建蓝图
health_bp = Blueprint(
    'health', 
    'health',
    description='健康检查接口',
)

@health_bp.route('/check', methods=['GET'])
@health_bp.response(200, HealthSchema)
@api_error_handler
def health_check():
    """ 
    健康检查接口
    
    返回服务器状态、版本和时间信息，用于验证API是否正常运行
    """
    health_data = {
        "status": "online",
        "version": current_app.config.get('API_VERSION', 'v1'),
        "timestamp": datetime.now(),
        "environment": os.environ.get('FLASK_ENV', 'development')
    }
    # raise Exception("模拟的服务器错误")
    return APIResponse.success(
        data=health_data,
        message="服务器运行正常"
    )