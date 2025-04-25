# app/services/storage/file_service.py
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, url_for

# 硬编码的上传目录路径
UPLOAD_DIR = 'app/static/uploads'  # 应用根目录下的静态文件夹

class FileService:
    """文件存储服务"""
    
    @staticmethod
    def save_file(file, folder='uploads'):
        """
        保存上传的文件
        
        :param file: 上传的文件对象
        :param folder: 存储目录
        :return: 文件存储路径
        """
        if not file:
            return None
            
        # 确保目录存在
        upload_dir = os.path.join(UPLOAD_DIR, folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        new_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 保存文件
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)
        
        # 返回相对路径
        return os.path.join(folder, new_filename).replace('\\', '/')
    
    @staticmethod
    def delete_file(file_path):
        """
        删除文件
        
        :param file_path: 文件相对路径
        :return: 是否删除成功
        """
        if not file_path:
            return False
            
        try:
            full_path = os.path.join(UPLOAD_DIR, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            current_app.logger.error(f"删除文件失败: {str(e)}")
            
        return False
        
    @staticmethod
    def get_file_url(file_path):
        """
        获取文件的完整URL
        
        :param file_path: 文件相对路径
        :return: 文件的完整URL
        """
        if not file_path:
            return None
            
        # 处理路径，确保以static/uploads开头
        if not file_path.startswith('static/'):
            # 将文件路径转换为static下的URL格式
            url_path = f"uploads/{file_path}"
        else:
            url_path = file_path.replace('static/', '', 1)
            
        try:
            # 使用Flask的url_for生成静态文件URL
            url = url_for('static', filename=url_path, _external=True)
            return url
        except Exception as e:
            current_app.logger.error(f"获取文件URL失败: {str(e)}")
            # 如果url_for失败，回退到简单拼接
            base_url = current_app.config.get('BASE_URL', '')
            return f"{base_url}/static/{url_path}"