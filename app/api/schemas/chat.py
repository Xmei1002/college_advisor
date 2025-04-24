# app/api/schemas/chat.py
from marshmallow import Schema, fields, validate
from app.api.schemas import PaginationSchema

class ConversationType:
    TYPE_0 = '普通对话'  
    TYPE_1 = '就业倾向' 
    TYPE_2 = '地域意向'
    TYPE_3 = '专业意向'
    TYPE_4 = '意向院校'
    TYPE_5 = '院校专业策略'
    TYPE_6 = '优势学科'
    TYPE_7 = '劣势学科'

# 查询参数Schema
class ConversationQuerySchema(Schema):
    """会话列表查询参数"""
    page = fields.Integer(load_default=1, description="页码")
    per_page = fields.Integer(load_default=20, description="每页记录数")
    student_id = fields.Integer(description="学生ID过滤")
    planner_id = fields.Integer(description="规划师ID过滤")
    conversation_type = fields.String(
        description="会话类型"
    )

class MessageQuerySchema(Schema):
    """消息列表查询参数"""
    page = fields.Integer(load_default=1, description="页码")
    per_page = fields.Integer(load_default=20, description="每页记录数")

# 请求体Schema
class StreamChatRequestSchema(Schema):
    """流式聊天请求"""
    student_id = fields.Integer(required=True, description="学生ID")
    planner_id = fields.Integer(required=True, description="规划师ID，如果是管理员发起的，则传入id为0")
    conversation_type = fields.String(
        required=True, 
        description="会话类型", 
        validate=validate.OneOf([
            ConversationType.TYPE_0, 
            ConversationType.TYPE_1,
            ConversationType.TYPE_2,
            ConversationType.TYPE_3,
            ConversationType.TYPE_4,
            ConversationType.TYPE_5,
            ConversationType.TYPE_6,
            ConversationType.TYPE_7
        ])
    )
    message = fields.String(required=True, description="消息内容")
    conversation_id = fields.Integer(allow_none=True, description="会话ID，新会话传0或不传")
    plan_id = fields.Integer(description="志愿方案ID，仅在志愿咨询时使用")

class UpdateTitleSchema(Schema):
    """更新会话标题请求"""
    title = fields.String(required=True, description="新标题")

# 响应Schema
class MessageSchema(Schema):
    """消息响应"""
    id = fields.Integer(dump_only=True, description="消息ID")
    conversation_id = fields.Integer(description="会话ID")
    sender_id = fields.Integer(description="发送者ID")
    role = fields.String(description="角色(student/planner/ai/system)")
    message_type = fields.String(description="消息类型(text/image/file/card)")
    content = fields.String(description="消息内容")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")

class ConversationSchema(Schema):
    """会话响应"""
    id = fields.Integer(dump_only=True, description="会话ID")
    student_id = fields.Integer(description="学生ID")
    planner_id = fields.Integer(description="规划师ID")
    title = fields.String(description="会话标题")
    conversation_type = fields.String(description="会话类型(changeinfo/volunteer)")
    last_message_time = fields.DateTime(description="最后消息时间")
    is_active = fields.Boolean(description="是否活跃")
    is_archived = fields.Boolean(description="是否归档")
    meta_data = fields.Raw(description="元数据")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")

class ConversationDetailSchema(ConversationSchema):
    """会话详情响应，包含消息列表"""
    messages = fields.List(fields.Nested(MessageSchema), description="消息列表")
    pagination = fields.Dict(description="分页信息")

class MessageListResponseSchema(Schema):
    """消息列表响应"""
    messages = fields.List(fields.Nested(MessageSchema), description="消息列表")
    pagination = fields.Nested(PaginationSchema, description="分页信息")

class ConversationListResponseSchema(Schema):
    """会话列表响应"""
    conversations = fields.List(fields.Nested(ConversationSchema), description="会话列表")
    pagination = fields.Nested(PaginationSchema, description="分页信息")

# API响应通用包装
class APISuccessSchema(Schema):
    """API成功响应"""
    success = fields.Boolean(dump_default=True, description="是否成功")
    message = fields.String(description="响应消息")
    code = fields.Integer(description="状态码")
    data = fields.Raw(description="响应数据")

class APIErrorSchema(Schema):
    """API错误响应"""
    success = fields.Boolean(dump_default=False, description="是否成功")
    message = fields.String(description="错误消息")
    code = fields.Integer(description="状态码")
    errors = fields.Raw(description="错误详情")

class APIPaginationSchema(Schema):
    """API分页响应"""
    success = fields.Boolean(dump_default=True, description="是否成功")
    message = fields.String(description="响应消息")
    code = fields.Integer(description="状态码")
    data = fields.List(fields.Raw(), description="数据列表")
    pagination = fields.Nested(PaginationSchema, description="分页信息")

# 在schemas.py文件中添加
class ChatQuestionQuerySchema(Schema):
    """聊天问题查询参数验证"""
    type = fields.String(description="问题类型", validate=validate.OneOf(["changeinfo", "volunteer"]))