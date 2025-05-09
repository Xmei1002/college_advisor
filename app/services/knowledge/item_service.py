# app/services/knowledge/item_service.py
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.knowledge_items import KnowledgeItem
from app.models.knowledge_directories import KnowledgeDirectory

class ItemService:
    """知识库条目服务类"""
    
    @staticmethod
    def get_items(directory_id=None, keyword=None, page=1, per_page=20):
        """
        获取知识条目列表
        
        :param directory_id: 目录ID筛选
        :param keyword: 关键字搜索
        :param page: 页码
        :param per_page: 每页条数
        :return: 条目列表和分页信息
        """
        query = KnowledgeItem.query.filter(KnowledgeItem.is_directory_content == False)
        
        # 应用筛选条件
        if directory_id:
            query = query.filter(KnowledgeItem.directory_id == directory_id)
            
        if keyword:
            query = query.filter(
                db.or_(
                    KnowledgeItem.title.ilike(f'%{keyword}%'),
                    KnowledgeItem.content.ilike(f'%{keyword}%')
                )
            )
        
        # 排序
        query = query.order_by(KnowledgeItem.sort_order, KnowledgeItem.updated_at.desc())
        
        # 分页
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # 转换为字典列表
        items_dict = [item.to_dict() for item in items]
        
        # 构建分页信息
        pagination = {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
        return items_dict, pagination
    
    @staticmethod
    def get_item_by_id(item_id):
        """
        根据ID获取条目
        
        :param item_id: 条目ID
        :return: 条目信息
        """
        item = KnowledgeItem.query.get_or_404(item_id)
        return item.to_dict()
    
    @staticmethod
    def increment_views(item_id):
        """
        增加浏览次数
        
        :param item_id: 条目ID
        :return: 是否成功
        """
        try:
            # 使用SQL直接更新，避免竞态条件
            db.session.execute(
                "UPDATE knowledge_items SET views = views + 1 WHERE id = :id",
                {"id": item_id}
            )
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
    
    @staticmethod
    def create_item(data, creator_id):
        """
        创建新知识条目
        
        :param data: 条目数据
        :param creator_id: 创建者ID
        :return: 创建的条目
        """
        try:
            # 验证目录存在
            directory = KnowledgeDirectory.query.get_or_404(data['directory_id'])
            
            # 创建条目
            item = KnowledgeItem(
                title=data['title'],
                content=data.get('content', ''),
                html_content=data.get('html_content', ''),
                directory_id=data['directory_id'],
                is_directory_content=data.get('is_directory_content', False),
                sort_order=data.get('sort_order', 0),
                tags=data.get('tags', '')
            )
            
            db.session.add(item)
            
            # 如果是目录直接内容，更新目录的has_direct_content标记
            if data.get('is_directory_content', False):
                directory.has_direct_content = True
            
            db.session.commit()
            
            return item.to_dict()
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"创建知识条目失败: {str(e)}")
            raise
    
    @staticmethod
    def update_item(item_id, data, updater_id):
        """
        更新知识条目
        
        :param item_id: 条目ID
        :param data: 更新数据
        :param updater_id: 更新者ID
        :return: 更新后的条目
        """
        try:
            item = KnowledgeItem.query.get_or_404(item_id)
            
            # 如果要更改目录，需要检查
            old_directory_id = item.directory_id
            if 'directory_id' in data and data['directory_id'] != old_directory_id:
                # 确保新目录存在
                new_directory = KnowledgeDirectory.query.get_or_404(data['directory_id'])
                
                # 如果是目录直接内容，需要特殊处理
                if item.is_directory_content:
                    # 不允许更改目录
                    raise ValueError("目录直接内容不能更改所属目录")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(item, key) and key not in ['id', 'created_at', 'updated_at']:
                    setattr(item, key, value)
            
            db.session.commit()
            
            return item.to_dict()
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新知识条目失败: {str(e)}")
            raise
    
    @staticmethod
    def delete_item(item_id):
        """
        删除知识条目
        
        :param item_id: 条目ID
        :return: 是否成功
        """
        try:
            item = KnowledgeItem.query.get_or_404(item_id)
            
            # 如果是目录直接内容，更新目录的has_direct_content标记
            if item.is_directory_content:
                directory = KnowledgeDirectory.query.get(item.directory_id)
                if directory:
                    directory.has_direct_content = False
            
            db.session.delete(item)
            db.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"删除知识条目失败: {str(e)}")
            raise
    
    @staticmethod
    def get_directory_content(directory_id):
        """
        获取目录直接内容
        
        :param directory_id: 目录ID
        :return: 目录直接内容
        """
        # 验证目录存在
        directory = KnowledgeDirectory.query.get_or_404(directory_id)
        
        # 查询目录直接内容
        item = KnowledgeItem.query.filter(
            KnowledgeItem.directory_id == directory_id,
            KnowledgeItem.is_directory_content == True
        ).first()
        
        if item:
            return item.to_dict()
        else:
            return None
    
    @staticmethod
    def create_directory_content(data, creator_id):
        """
        创建目录直接内容
        
        :param data: 条目数据
        :param creator_id: 创建者ID
        :return: 创建的条目
        """
        try:
            # 验证目录存在
            directory = KnowledgeDirectory.query.get_or_404(data['directory_id'])
            
            # 检查是否已有直接内容
            existing = KnowledgeItem.query.filter(
                KnowledgeItem.directory_id == data['directory_id'],
                KnowledgeItem.is_directory_content == True
            ).first()
            
            if existing:
                # 如果已有直接内容，则更新
                for key, value in data.items():
                    if hasattr(existing, key) and key not in ['id', 'created_at', 'updated_at', 'directory_id', 'is_directory_content']:
                        setattr(existing, key, value)
                
                db.session.commit()
                return existing.to_dict()
            
            # 创建新的直接内容
            item = KnowledgeItem(
                title=data.get('title', directory.title),  # 默认使用目录名
                content=data.get('content', ''),
                html_content=data.get('html_content', ''),
                directory_id=data['directory_id'],
                is_directory_content=True,
                sort_order=0,  # 直接内容始终排在最前面
                tags=data.get('tags', '')
            )
            
            db.session.add(item)
            
            # 更新目录标记
            directory.has_direct_content = True
            
            db.session.commit()
            
            return item.to_dict()
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"创建目录直接内容失败: {str(e)}")
            raise