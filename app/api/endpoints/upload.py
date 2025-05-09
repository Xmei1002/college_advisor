# app/api/endpoints/upload.py
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.storage.file_service import FileService
from flask_smorest import Blueprint

# 创建上传蓝图
upload_bp = Blueprint(
    'upload', 
    'upload',
    description='文件上传相关接口',
)

@upload_bp.route('/image', methods=['POST'])
@jwt_required()
@api_error_handler
def upload_image():
    """
    上传图片
    
    上传图片文件到服务器
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 检查是否有文件上传
    if 'file' not in request.files:
        return APIResponse.error("未找到上传文件", code=400)
    
    file = request.files['file']
    
    # 如果用户没有选择文件，浏览器也会提交一个空的文件部分
    if file.filename == '':
        return APIResponse.error("未选择文件", code=400)
    
    # 获取分类参数（可选）
    category = request.form.get('category', 'general')
    
    # 构建存储目录，格式: users/{user_id}/{category}
    folder = f"{category}"
    
    # 保存图片
    result = FileService.save_image(file, folder=folder)
    
    if not result['success']:
        return APIResponse.error(result['message'], code=400)
    
    return APIResponse.success(
        data=result['data'],
        message=result['message']
    )

@upload_bp.route('/images', methods=['POST'])
@jwt_required()
@api_error_handler
def upload_multiple_images():
    """
    批量上传图片
    
    一次上传多张图片到服务器
    """
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 检查是否有文件上传
    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return APIResponse.error("未找到上传文件", code=400)
    
    # 获取分类参数（可选）
    category = request.form.get('category', 'general')
    
    # 构建存储目录，格式: users/{user_id}/{category}
    folder = f"{category}"
    
    # 保存文件
    results = []
    for file in files:
        # 跳过空文件名
        if file.filename == '':
            continue
            
        result = FileService.save_image(file, folder=folder)
        if result['success']:
            results.append(result['data'])
    
    if not results:
        return APIResponse.error("所有文件上传失败", code=400)
    
    return APIResponse.success(
        data=results,
        message=f"成功上传 {len(results)} 个文件"
    )