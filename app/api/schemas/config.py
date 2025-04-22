from marshmallow import Schema, fields, validate

class PromptTemplateSchema(Schema):
    """提示词模板基础模式"""
    id = fields.Integer(dump_only=True, description="模板ID")
    name = fields.String(required=True, description="提示词名称")
    type = fields.String(required=True, description="提示词类型")
    content = fields.String(required=True, description="提示词内容")
    description = fields.String(description="提示词描述")
    created_at = fields.DateTime(dump_only=True, description="创建时间")
    updated_at = fields.DateTime(dump_only=True, description="更新时间")

class UpdatePromptTemplateSchema(Schema):
    """更新提示词模板内容模式"""
    content = fields.String(required=True, description="提示词内容")

class PromptTemplateResponseSchema(Schema):
    """提示词模板响应模式"""
    message = fields.String(required=True, description="响应消息")
    success = fields.Boolean(required=True, description="是否成功")
    code = fields.Integer(required=True, description="状态码")
    data = fields.Nested(PromptTemplateSchema, description="提示词模板数据")

class PromptTemplateListResponseSchema(Schema):
    """提示词模板列表响应模式"""
    message = fields.String(required=True, description="响应消息")
    success = fields.Boolean(required=True, description="是否成功")
    code = fields.Integer(required=True, description="状态码")
    data = fields.List(fields.Nested(PromptTemplateSchema), description="提示词模板列表") 

class LLMConfigurationSchema(Schema):
    """LLM配置模式"""
    provider = fields.String(required=True, description="提供者名称")
    is_active = fields.Boolean(description="是否激活")

class UpdateLLMConfigurationSchema(Schema):
    """更新LLM配置模式"""
    provider = fields.String(required=True, description="提供者名称")

class LLMConfigurationResponseSchema(Schema):
    """LLM配置响应模式"""
    message = fields.String(required=True, description="响应消息")
    success = fields.Boolean(required=True, description="是否成功")
    code = fields.Integer(required=True, description="状态码")
    data = fields.Nested(LLMConfigurationSchema, description="LLM配置数据")

class LLMConfigurationListDataSchema(Schema):
    """LLM配置列表数据模式"""
    providers = fields.List(fields.String(), description="支持的提供商列表")
    active_provider = fields.String(description="当前激活的提供商")

class LLMConfigurationListResponseSchema(Schema):
    """LLM配置列表响应模式"""
    message = fields.String(required=True, description="响应消息")
    success = fields.Boolean(required=True, description="是否成功")
    code = fields.Integer(required=True, description="状态码")
    data = fields.Nested(LLMConfigurationListDataSchema, description="LLM配置列表数据") 

    