# app/services/knowledge/directory_service.py
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.knowledge_directories import KnowledgeDirectory
from app.models.knowledge_items import KnowledgeItem

class DirectoryService:
    """知识库目录服务类"""

    # app/services/knowledge/directory_service.py

    @staticmethod
    def get_directory_tree(include_items=True, include_content=False):
        """
        获取目录树及条目
        
        :param include_items: 是否包含条目信息
        :param include_content: 是否包含条目内容（内容较大，可选不包含）
        :return: 目录树
        """
        try:
            # 1. 获取所有顶级目录
            top_directories = KnowledgeDirectory.query.filter(
                KnowledgeDirectory.level == 1
            ).order_by(KnowledgeDirectory.sort_order, KnowledgeDirectory.id).all()
            
            # 2. 获取所有子目录 - 预加载以减少查询次数
            all_sub_directories = KnowledgeDirectory.query.filter(
                KnowledgeDirectory.level == 2
            ).order_by(KnowledgeDirectory.sort_order, KnowledgeDirectory.id).all()
            
            # 子目录按父目录ID分组
            sub_directories_map = {}
            for sub_dir in all_sub_directories:
                if sub_dir.parent_id not in sub_directories_map:
                    sub_directories_map[sub_dir.parent_id] = []
                sub_directories_map[sub_dir.parent_id].append(sub_dir)
            
            # 3. 如果需要包含条目，获取所有条目
            all_items_map = {}
            all_direct_content_map = {}
            
            if include_items:
                # 获取所有条目
                query = KnowledgeItem.query.filter(
                    KnowledgeItem.status == 1  # 只获取正常状态的条目
                ).order_by(KnowledgeItem.sort_order, KnowledgeItem.updated_at.desc())
                
                # 如果不包含内容，则不查询大字段
                if not include_content:
                    query = query.with_entities(
                        KnowledgeItem.id, 
                        KnowledgeItem.title,
                        KnowledgeItem.directory_id,
                        KnowledgeItem.is_directory_content,
                        KnowledgeItem.sort_order,
                        KnowledgeItem.views,
                        KnowledgeItem.tags,
                        KnowledgeItem.status,
                        KnowledgeItem.created_at,
                        KnowledgeItem.updated_at
                    )
                
                all_items = query.all()
                
                # 按目录ID和是否为目录直接内容分组
                for item in all_items:
                    if item.is_directory_content:
                        all_direct_content_map[item.directory_id] = item
                    else:
                        if item.directory_id not in all_items_map:
                            all_items_map[item.directory_id] = []
                        all_items_map[item.directory_id].append(item)
            
            # 4. 递归构建目录树
            def build_directory_tree(directories):
                result = []
                for directory in directories:
                    # 基本目录信息
                    dir_dict = {
                        'id': directory.id,
                        'title': directory.title,
                        'level': directory.level,
                        'has_direct_content': directory.has_direct_content,
                        'sort_order': directory.sort_order,
                        'created_at': directory.created_at,
                        'updated_at': directory.updated_at,
                        'children': [],
                        'direct_content': None,
                        'items': []
                    }
                    
                    # 添加子目录
                    if directory.id in sub_directories_map:
                        dir_dict['children'] = build_directory_tree(sub_directories_map[directory.id])
                    
                    # 添加目录直接内容
                    if include_items and directory.id in all_direct_content_map:
                        direct_content = all_direct_content_map[directory.id]
                        
                        if include_content:
                            dir_dict['direct_content'] = {
                                'id': direct_content.id,
                                'title': direct_content.title,
                                'is_directory_content': direct_content.is_directory_content,
                                'sort_order': direct_content.sort_order,
                                'views': direct_content.views,
                                'tags': direct_content.tags,
                                'updated_at': direct_content.updated_at,
                                'content': direct_content.content,
                                'html_content': direct_content.html_content
                            }
                        else:
                            dir_dict['direct_content'] = {
                                'id': direct_content.id,
                                'title': direct_content.title,
                                'is_directory_content': direct_content.is_directory_content,
                                'sort_order': direct_content.sort_order,
                                'views': direct_content.views,
                                'tags': direct_content.tags,
                                'updated_at': direct_content.updated_at
                            }
                    
                    # 添加目录下的条目
                    if include_items and directory.id in all_items_map:
                        items = all_items_map[directory.id]
                        
                        for item in items:
                            if include_content:
                                item_dict = {
                                    'id': item.id,
                                    'title': item.title,
                                    'is_directory_content': item.is_directory_content,
                                    'sort_order': item.sort_order,
                                    'views': item.views,
                                    'tags': item.tags,
                                    'updated_at': item.updated_at,
                                    'content': item.content,
                                    'html_content': item.html_content
                                }
                            else:
                                item_dict = {
                                    'id': item.id,
                                    'title': item.title,
                                    'is_directory_content': item.is_directory_content,
                                    'sort_order': item.sort_order,
                                    'views': item.views,
                                    'tags': item.tags,
                                    'updated_at': item.updated_at
                                }
                            dir_dict['items'].append(item_dict)
                    
                    result.append(dir_dict)
                return result
            
            # 构建树状结构
            tree = build_directory_tree(top_directories)
            
            return tree
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"获取目录树失败: {str(e)}")
            raise
    
    @staticmethod
    def get_all_directories():
        """
        获取所有目录
        
        :return: 目录列表
        """
        # 先获取所有一级目录
        top_directories = KnowledgeDirectory.query.filter(
            KnowledgeDirectory.level == 1
        ).order_by(KnowledgeDirectory.sort_order, KnowledgeDirectory.id).all()
        
        # 转换为前端需要的格式
        result = []
        for directory in top_directories:
            dir_dict = {
                'id': str(directory.id),  # 转为字符串
                'title': directory.title,
                'isExpanded': False,  # 默认不展开
                'level': directory.level,
                'hasDirectContent': directory.has_direct_content
            }
            
            # 获取子目录
            children = KnowledgeDirectory.query.filter(
                KnowledgeDirectory.parent_id == directory.id
            ).order_by(KnowledgeDirectory.sort_order, KnowledgeDirectory.id).all()
            
            # 如果有子目录，添加子目录信息
            if children:
                child_dirs = []
                for child in children:
                    child_dict = {
                        'id': str(child.id),
                        'title': child.title,
                        'isExpanded': False,
                        'level': child.level,
                        'parentId': str(child.parent_id),
                        'hasDirectContent': child.has_direct_content
                    }
                    child_dirs.append(child_dict)
                
                # 暂时不直接添加到结果，前端会通过ID关联
            
            result.append(dir_dict)
            
        return result
    
    @staticmethod
    def get_directory_by_id(directory_id):
        """
        根据ID获取目录
        
        :param directory_id: 目录ID
        :return: 目录信息
        """
        directory = KnowledgeDirectory.query.get_or_404(directory_id)
        return directory.to_dict(include_children=True)
    
    @staticmethod
    def create_directory(data, creator_id):
        """
        创建新目录
        
        :param data: 目录数据
        :param creator_id: 创建者ID
        :return: 创建的目录
        """
        try:
            # 确定目录层级
            level = 1
            if data.get('parent_id') and data.get('parent_id') != 0:  # 检查 parent_id 不为 0
                parent = KnowledgeDirectory.query.get_or_404(data['parent_id'])
                level = 2
            
            # 创建目录
            directory = KnowledgeDirectory(
                title=data['title'],
                level=level,
                parent_id=data.get('parent_id') if data.get('parent_id') and data.get('parent_id') != 0 else None,  # 确保 0 转换为 None
                sort_order=data.get('sort_order', 0),
                has_direct_content=False  # 初始没有直接内容
            )
            
            db.session.add(directory)
            db.session.commit()
            
            return directory.to_dict()
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"创建目录失败: {str(e)}")
            raise
    
    @staticmethod
    def update_directory(directory_id, data, updater_id):
        """
        更新目录
        
        :param directory_id: 目录ID
        :param data: 更新数据
        :param updater_id: 更新者ID
        :return: 更新后的目录
        """
        try:
            directory = KnowledgeDirectory.query.get_or_404(directory_id)
            
            # 更新字段
            if 'title' in data:
                directory.title = data['title']
            
            if 'sort_order' in data:
                directory.sort_order = data['sort_order']
            
            # 如果要更新父目录，需要检查是否合法
            if 'parent_id' in data:
                # 只允许一级目录或二级目录
                if data['parent_id'] is None:
                    directory.level = 1
                    directory.parent_id = None
                else:
                    # 确保父目录存在并且是一级目录
                    parent = KnowledgeDirectory.query.get_or_404(data['parent_id'])
                    if parent.level != 1:
                        raise ValueError("父目录必须是一级目录")
                    
                    directory.parent_id = data['parent_id']
                    directory.level = 2
            
            db.session.commit()
            
            return directory.to_dict()
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"更新目录失败: {str(e)}")
            raise
    
    @staticmethod
    def delete_directory(directory_id):
        """
        删除目录
        
        :param directory_id: 目录ID
        :return: 是否成功
        """
        try:
            directory = KnowledgeDirectory.query.get_or_404(directory_id)
            
            # 检查是否有子目录
            has_children = KnowledgeDirectory.query.filter(
                KnowledgeDirectory.parent_id == directory_id
            ).first() is not None
            
            if has_children:
                raise ValueError("无法删除有子目录的目录，请先删除子目录")
            
            # 检查是否有关联的条目（非直接内容）
            has_items = KnowledgeItem.query.filter(
                KnowledgeItem.directory_id == directory_id,
                KnowledgeItem.is_directory_content == False
            ).first() is not None
            
            if has_items:
                raise ValueError("无法删除有关联条目的目录，请先删除关联条目")
            
            # 删除目录的直接内容
            direct_content = KnowledgeItem.query.filter(
                KnowledgeItem.directory_id == directory_id,
                KnowledgeItem.is_directory_content == True
            ).first()
            
            if direct_content:
                db.session.delete(direct_content)
            
            # 删除目录
            db.session.delete(directory)
            db.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"删除目录失败: {str(e)}")
            raise