# app/api/endpoints/tasks.py
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.extensions import celery
from celery.result import AsyncResult
from flask_smorest import Blueprint
from app.models.user import User
from datetime import datetime

# 创建任务蓝图
tasks_bp = Blueprint(
    'tasks', 
    'tasks',
    description='异步任务状态查询接口',
)

@tasks_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required()
@api_error_handler
def get_task_status(task_id):
    """
    获取异步任务状态
    
    根据任务ID查询任务状态和结果
    """
    
    # 获取任务结果
    task_result = AsyncResult(task_id, app=celery)
    response_data = {
        'task_id': task_result.id,
        'status': task_result.status,
        'result': task_result.result,
    }
        
    return APIResponse.success(
        data=response_data,
        message="任务状态查询成功"
    )

# @tasks_bp.route('/revoke/<task_id>', methods=['POST'])
# @jwt_required()
# @api_error_handler
# def revoke_task(task_id):
#     """
#     取消异步任务
    
#     根据任务ID取消正在执行或等待中的任务
#     """
#     # 获取当前用户并验证权限
#     current_user_id = get_jwt_identity()
#     current_user = User.query.get_or_404(current_user_id)
    
#     # 检查是否管理员或规划师
#     if current_user.user_type not in [User.USER_TYPE_ADMIN, User.USER_TYPE_PLANNER]:
#         return APIResponse.error("权限不足，只有管理员或规划师可以取消任务", code=403)
    
#     # 获取任务
#     task = AsyncResult(task_id, app=celery)
    
#     # 检查任务是否存在
#     if not task:
#         return APIResponse.error(f"任务ID {task_id} 不存在", code=404)
    
#     # 检查任务是否可以取消
#     if task.status in ['SUCCESS', 'FAILURE', 'REVOKED']:
#         return APIResponse.error(f"任务已经处于终态 ({task.status})，无法取消", code=400)
    
#     # 尝试取消任务
#     try:
#         task.revoke(terminate=True, signal='SIGTERM')
#         return APIResponse.success(message="任务已成功取消")
#     except Exception as e:
#         current_app.logger.error(f"取消任务失败: {str(e)}")
#         return APIResponse.error(f"取消任务失败: {str(e)}", code=500)

# @tasks_bp.route('/list', methods=['GET'])
# @jwt_required()
# @api_error_handler
# def list_active_tasks():
#     """
#     列出活跃任务
    
#     列出当前正在执行或等待中的任务(需要Celery Flower支持)
#     """
#     # 获取当前用户并验证权限
#     current_user_id = get_jwt_identity()
#     current_user = User.query.get_or_404(current_user_id)
    
#     # 检查是否管理员或规划师
#     if current_user.user_type not in [User.USER_TYPE_ADMIN, User.USER_TYPE_PLANNER]:
#         return APIResponse.error("权限不足，只有管理员或规划师可以查看任务列表", code=403)
    
#     try:
#         # 注意：这个功能需要安装和配置Celery Flower，或者使用celery的inspect功能
#         # 如果使用Flower，需要在启动时指定broker和API地址
#         # 这里提供一个简化实现，实际项目可能需要更复杂的实现
#         inspect = celery.control.inspect()
#         active_tasks = inspect.active() or {}
#         scheduled_tasks = inspect.scheduled() or {}
#         reserved_tasks = inspect.reserved() or {}
        
#         # 合并所有任务
#         all_tasks = []
        
#         # 处理活动任务
#         for worker_name, tasks in active_tasks.items():
#             for task in tasks:
#                 all_tasks.append({
#                     'id': task.get('id'),
#                     'name': task.get('name'),
#                     'args': task.get('args'),
#                     'kwargs': task.get('kwargs'),
#                     'type': 'active',
#                     'worker': worker_name,
#                     'time_start': task.get('time_start')
#                 })
        
#         # 处理计划任务
#         for worker_name, tasks in scheduled_tasks.items():
#             for task in tasks:
#                 request = task.get('request', {})
#                 all_tasks.append({
#                     'id': request.get('id'),
#                     'name': request.get('name'),
#                     'args': request.get('args'),
#                     'kwargs': request.get('kwargs'),
#                     'type': 'scheduled',
#                     'worker': worker_name,
#                     'eta': task.get('eta')
#                 })
        
#         # 处理保留任务
#         for worker_name, tasks in reserved_tasks.items():
#             for task in tasks:
#                 all_tasks.append({
#                     'id': task.get('id'),
#                     'name': task.get('name'),
#                     'args': task.get('args'),
#                     'kwargs': task.get('kwargs'),
#                     'type': 'reserved',
#                     'worker': worker_name
#                 })
        
#         return APIResponse.success(
#             data=all_tasks,
#             message=f"共找到 {len(all_tasks)} 个活跃任务"
#         )
#     except Exception as e:
#         current_app.logger.error(f"获取任务列表失败: {str(e)}")
#         return APIResponse.error(f"获取任务列表失败: {str(e)}", code=500)