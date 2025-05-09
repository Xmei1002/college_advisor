# app/api/endpoints/knowledge_directory.py
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.knowledge.directory_service import DirectoryService
from flask_smorest import Blueprint
from app.utils.decorators import api_error_handler

# 创建目录蓝图
knowledge_directory_bp = Blueprint(
    'knowledge_directory', 
    'knowledge_directory',
    description='知识库目录管理相关接口',
)

from app.api.schemas.knowledge import (
    DirectoryCreateSchema, DirectoryUpdateSchema, DirectoryResponseSchema, 
    DirectoryListResponseSchema,DirectoryTreeResponseSchema
)


@knowledge_directory_bp.route('/tree', methods=['GET'])
@knowledge_directory_bp.response(200, DirectoryTreeResponseSchema)
# @cache_response(timeout=300)  # 5分钟缓存，可根据需求调整
@api_error_handler
def get_directory_tree():
    """
    获取完整目录树与条目
    
    返回所有知识库目录和其下的所有条目，形成完整的树状结构
    """
    include_items = request.args.get('include_items', '1') == '1'
    include_content = request.args.get('include_content', '0') == '1'
    
    tree = DirectoryService.get_directory_tree(
        include_items=include_items,
        include_content=include_content
    )
    
    return APIResponse.success(
        data=tree,
        message="获取成功"
    )

@knowledge_directory_bp.route('', methods=['GET'])
@knowledge_directory_bp.response(200, DirectoryListResponseSchema)
@api_error_handler
def get_directories():
    """
    获取目录列表
    
    返回所有知识库目录，包括目录结构
    """
    directories = DirectoryService.get_all_directories()
    return APIResponse.success(
        data=directories,
        message="获取成功"
    )

@knowledge_directory_bp.route('/<int:directory_id>', methods=['GET'])
@knowledge_directory_bp.response(200, DirectoryResponseSchema)
@api_error_handler
def get_directory(directory_id):
    """
    获取单个目录详情
    
    根据目录ID获取详细信息
    """
    directory = DirectoryService.get_directory_by_id(directory_id)
    return APIResponse.success(
        data=directory,
        message="获取成功"
    )

@knowledge_directory_bp.route('', methods=['POST'])
@knowledge_directory_bp.arguments(DirectoryCreateSchema)
@knowledge_directory_bp.response(201, DirectoryResponseSchema)
@jwt_required()  # 需要认证
@api_error_handler
def create_directory(data):
    """
    创建新目录
    
    创建知识库新目录
    """
    creator_id = get_jwt_identity()
    directory = DirectoryService.create_directory(data, creator_id)
    return APIResponse.success(
        data=directory,
        message="创建成功",
        code=200
    )

@knowledge_directory_bp.route('/<int:directory_id>', methods=['PUT'])
@knowledge_directory_bp.arguments(DirectoryUpdateSchema)
@knowledge_directory_bp.response(200, DirectoryResponseSchema)
@jwt_required()
@api_error_handler
def update_directory(data, directory_id):
    """
    更新目录
    
    更新现有目录的信息
    """
    updater_id = get_jwt_identity()
    directory = DirectoryService.update_directory(directory_id, data, updater_id)
    return APIResponse.success(
        data=directory,
        message="更新成功"
    )

@knowledge_directory_bp.route('/<int:directory_id>', methods=['DELETE'])
@knowledge_directory_bp.response(200)
@jwt_required()
@api_error_handler
def delete_directory(directory_id):
    """
    删除目录
    
    删除指定的目录，只有空目录可删除
    """
    DirectoryService.delete_directory(directory_id)
    return APIResponse.success(
        message="删除成功"
    )