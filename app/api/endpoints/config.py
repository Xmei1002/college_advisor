from flask import request
from app.models.prompt_template import PromptTemplate
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import api_error_handler
from app.utils.response import APIResponse
from app.models.user import User
from app.models.llm_configuration import LLMConfiguration
from app.api.schemas.config import (
    PromptTemplateSchema,
    UpdatePromptTemplateSchema,
    PromptTemplateResponseSchema,
    PromptTemplateListResponseSchema,
    LLMConfigurationListResponseSchema,
    LLMConfigurationResponseSchema,
    UpdateLLMConfigurationSchema
)
from flask_smorest import Blueprint

config_bp = Blueprint(
    'config_bp', 
    'config_bp',
    description='配置项接口',
)

@config_bp.route('/prompt-templates', methods=['GET'])
@config_bp.response(200, PromptTemplateListResponseSchema)
@jwt_required()
@api_error_handler
def get_all_prompt_templates():
    """获取所有提示词模板"""
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
        
    templates = PromptTemplate.query.all()
    return APIResponse.success(
        data=[template.to_dict() for template in templates],
        message="获取提示词模板列表成功"
    )

@config_bp.route('/prompt-templates/<int:template_id>', methods=['GET'])
@config_bp.response(200, PromptTemplateResponseSchema)
@jwt_required()
@api_error_handler
def get_prompt_template(template_id):
    """获取单个提示词模板"""
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
        
    template = PromptTemplate.query.get_or_404(template_id)
    return APIResponse.success(
        data=template.to_dict(),
        message="获取提示词模板成功"
    )

@config_bp.route('/prompt-templates/<int:template_id>', methods=['PUT'])
@config_bp.arguments(UpdatePromptTemplateSchema)
@config_bp.response(200, PromptTemplateResponseSchema)
@jwt_required()
@api_error_handler
def update_prompt_template(data, template_id):
    """更新提示词模板内容"""
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
        
    template = PromptTemplate.query.get_or_404(template_id)
    
    # 更新content字段
    template.content = data['content']
    
    # 保存到数据库
    db.session.commit()
    
    return APIResponse.success(
        data=template.to_dict(),
        message="更新提示词模板成功"
    )

@config_bp.route('/llm-configurations', methods=['GET'])
@config_bp.response(200, LLMConfigurationListResponseSchema)
@jwt_required()
@api_error_handler
def get_llm_configurations():
    """获取所有大模型提供商配置列表"""
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    llm_list = LLMConfiguration.query.all()
    return APIResponse.success(
        data=[llm.to_dict() for llm in llm_list],
        message="获取大模型提供商列表成功"
    )

@config_bp.route('/llm-configurations/activate', methods=['POST'])
@config_bp.arguments(UpdateLLMConfigurationSchema)
@config_bp.response(200, LLMConfigurationResponseSchema)
@jwt_required()
@api_error_handler
def activate_llm_configuration(data):
    """激活特定的大模型提供商"""
    # 检查权限
    user_id = get_jwt_identity()
    user = User.query.get_or_404(int(user_id))
    if user.user_type != User.USER_TYPE_ADMIN:
        return APIResponse.error(message="没有权限访问该接口", code=403)
    
    provider = data['provider']
    
    try:
        # 设置激活的提供商
        config = LLMConfiguration.set_active_provider(provider)
        
        return APIResponse.success(
            data=config.to_dict(),
            message=f"已成功激活 {provider} 提供商"
        )
    except ValueError as e:
        return APIResponse.error(message=str(e), code=400)
