# app/services/institution/institution_service.py
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.institution import Institution
from app.services.storage.file_service import FileService

class InstitutionService:
    """机构服务类"""
    
    @staticmethod
    def create_institution(data, logo_file=None, qrcode_file=None):
        """
        创建机构
        
        :param data: 机构数据
        :param logo_file: 上传的logo文件
        :param qrcode_file: 上传的二维码文件
        :return: 创建的机构
        """
        try:
            # 处理上传文件
            logo_path = FileService.save_file(logo_file, 'institution/logo') if logo_file else None
            qrcode_path = FileService.save_file(qrcode_file, 'institution/qrcode') if qrcode_file else None
            
            # 创建机构
            institution = Institution(
                name=data.get('name'),
                address=data.get('address'),
                logo_path=logo_path,
                qrcode_path=qrcode_path,
                contact_phone=data.get('contact_phone'),
                contact_email=data.get('contact_email'),
                description=data.get('description'),
                status=data.get('status', 1)
            )
            
            db.session.add(institution)
            db.session.commit()
            
            return institution
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"创建机构失败: {str(e)}")
            raise
    
    @staticmethod
    def update_institution(institution_id, data, logo_file=None, qrcode_file=None):
        """
        更新机构信息
        
        :param institution_id: 机构ID
        :param data: 更新数据
        :param logo_file: 新上传的logo文件
        :param qrcode_file: 新上传的二维码文件
        :return: 更新后的机构
        """
        try:
            institution = Institution.query.get_or_404(institution_id)
            
            # 处理上传文件
            if logo_file:
                # 删除旧文件
                if institution.logo_path:
                    FileService.delete_file(institution.logo_path)
                
                # 保存新文件
                institution.logo_path = FileService.save_file(logo_file, 'institution/logo')
                
            if qrcode_file:
                # 删除旧文件
                if institution.qrcode_path:
                    FileService.delete_file(institution.qrcode_path)
                
                # 保存新文件
                institution.qrcode_path = FileService.save_file(qrcode_file, 'institution/qrcode')
            
            # 更新其他字段
            for key, value in data.items():
                if hasattr(institution, key) and key not in ['id', 'created_at', 'updated_at']:
                    setattr(institution, key, value)
            
            db.session.commit()
            
            return institution
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新机构失败: {str(e)}")
            raise
    
    @staticmethod
    def get_institution(institution_id):
        """
        获取机构详情
        
        :param institution_id: 机构ID
        :return: 机构详情
        """
        return Institution.query.get_or_404(institution_id)
    
    @staticmethod
    def list_institutions(page=1, per_page=20, **filters):
        """
        获取机构列表
        
        :param page: 页码
        :param per_page: 每页数量
        :param filters: 过滤条件
        :return: 机构列表和分页信息
        """
        query = Institution.query
        
        # 应用过滤条件
        if 'name' in filters and filters['name']:
            query = query.filter(Institution.name.like(f"%{filters['name']}%"))
            
        if 'status' in filters and filters['status'] is not None:
            query = query.filter(Institution.status == filters['status'])
        
        # 分页
        pagination = query.order_by(Institution.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return pagination.items, {
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def delete_institution(institution_id):
        """
        删除机构
        
        :param institution_id: 机构ID
        :return: 是否删除成功
        """
        try:
            institution = Institution.query.get_or_404(institution_id)
            
            # 删除相关文件
            if institution.logo_path:
                FileService.delete_file(institution.logo_path)
                
            if institution.qrcode_path:
                FileService.delete_file(institution.qrcode_path)
            
            # 删除机构
            db.session.delete(institution)
            db.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"删除机构失败: {str(e)}")
            raise