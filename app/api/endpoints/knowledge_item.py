# app/api/endpoints/knowledge_item.py
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.knowledge.item_service import ItemService
from flask_smorest import Blueprint
from app.utils.decorators import api_error_handler

# 创建知识条目蓝图
knowledge_item_bp = Blueprint(
    'knowledge_item', 
    'knowledge_item',
    description='知识库条目管理相关接口',
)

from app.api.schemas.knowledge import (
    ItemCreateSchema, ItemUpdateSchema, ItemResponseSchema, 
    ItemListResponseSchema, ItemQuerySchema
)

@knowledge_item_bp.route('', methods=['GET'])
@knowledge_item_bp.arguments(ItemQuerySchema, location='query')
@knowledge_item_bp.response(200, ItemListResponseSchema)
@api_error_handler
def get_items(args):
    """
    获取知识条目列表
    
    根据查询条件返回知识条目列表
    """
    items, pagination = ItemService.get_items(
        directory_id=args.get('directory_id'),
        keyword=args.get('keyword'),
        page=args.get('page', 1),
        per_page=args.get('per_page', 20)
    )
    return APIResponse.pagination(
        items=items,
        total=pagination['total'],
        page=pagination['page'],
        per_page=pagination['per_page'],
        message="获取成功"
    )

@knowledge_item_bp.route('/<int:item_id>', methods=['GET'])
@knowledge_item_bp.response(200, ItemResponseSchema)
@api_error_handler
def get_item(item_id):
    """
    获取知识条目详情
    
    根据条目ID获取详细信息
    """
    item = ItemService.get_item_by_id(item_id)
    
    # 更新浏览次数
    ItemService.increment_views(item_id)
    
    return APIResponse.success(
        data=item,
        message="获取成功"
    )

@knowledge_item_bp.route('', methods=['POST'])
@knowledge_item_bp.arguments(ItemCreateSchema)
@knowledge_item_bp.response(201, ItemResponseSchema)
@jwt_required()  # 需要认证
@api_error_handler
def create_item(data):
    """
    创建新知识条目
    
    创建知识库新条目
    """
    creator_id = get_jwt_identity()
    item = ItemService.create_item(data, creator_id)
    return APIResponse.success(
        data=item,
        message="创建成功",
        code=200
    )

@knowledge_item_bp.route('/<int:item_id>', methods=['PUT'])
@knowledge_item_bp.arguments(ItemUpdateSchema)
@knowledge_item_bp.response(200, ItemResponseSchema)
@jwt_required()
@api_error_handler
def update_item(data, item_id):
    """
    更新知识条目
    
    更新现有条目的信息
    """
    updater_id = get_jwt_identity()
    item = ItemService.update_item(item_id, data, updater_id)
    return APIResponse.success(
        data=item,
        message="更新成功"
    )

@knowledge_item_bp.route('/<int:item_id>', methods=['DELETE'])
@knowledge_item_bp.response(200)
@jwt_required()
@api_error_handler
def delete_item(item_id):
    """
    删除知识条目
    
    删除指定的知识条目
    """
    ItemService.delete_item(item_id)
    return APIResponse.success(
        message="删除成功"
    )

@knowledge_item_bp.route('/directory-content/<int:directory_id>', methods=['GET'])
@knowledge_item_bp.response(200, ItemResponseSchema)
@api_error_handler
def get_directory_content(directory_id):
    """
    获取目录直接内容
    
    获取指定目录的直接内容
    """
    item = ItemService.get_directory_content(directory_id)
    if item:
        # 更新浏览次数
        ItemService.increment_views(item['id'])
        
    return APIResponse.success(
        data=item,
        message="获取成功"
    )

@knowledge_item_bp.route('/directory-content/<int:directory_id>', methods=['POST'])
@knowledge_item_bp.arguments(ItemCreateSchema)
@knowledge_item_bp.response(201, ItemResponseSchema)
@jwt_required()
@api_error_handler
def create_directory_content(data, directory_id):
    """
    创建目录直接内容
    
    为指定目录创建直接内容
    """
    creator_id = get_jwt_identity()
    
    # 覆盖目录ID和标记为目录内容
    data['directory_id'] = directory_id
    data['is_directory_content'] = True
    
    item = ItemService.create_directory_content(data, creator_id)
    return APIResponse.success(
        data=item,
        message="创建成功",
        code=200
    )