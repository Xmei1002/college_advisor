# app/services/storage/file_service.py
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

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
        upload_dir = os.path.join(current_app.config['UPLOAD_DIR'], folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        new_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 保存文件
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)
        
        # 返回相对路径
        return os.path.join(folder, new_filename)
    
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
            full_path = os.path.join(current_app.config['UPLOAD_DIR'], file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            current_app.logger.error(f"删除文件失败: {str(e)}")
            
        return False