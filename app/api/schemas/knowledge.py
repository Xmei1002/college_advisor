# app/api/schemas.py
from marshmallow import Schema, fields, validate

# 目录相关Schema

# app/api/schemas.py

# 知识条目简略响应Schema（用于目录树中）
class ItemBriefResponseSchema(Schema):
    """知识条目简略响应Schema"""
    id = fields.Integer(description="条目ID")
    title = fields.String(description="条目标题")
    is_directory_content = fields.Boolean(description="是否为目录直接内容")
    sort_order = fields.Integer(description="排序顺序")
    views = fields.Integer(description="浏览次数")
    tags = fields.String(description="标签，逗号分隔")
    updated_at = fields.DateTime(description="更新时间")
    # 根据include_content参数决定是否包含内容字段
    content = fields.String(description="纯文本内容")
    html_content = fields.String(description="HTML格式内容")

# 递归的目录树响应Schema
class DirectoryTreeItemSchema(Schema):
    """目录树中的目录项Schema"""
    id = fields.Integer(description="目录ID")
    title = fields.String(description="目录标题")
    level = fields.Integer(description="目录层级：1=顶级，2=子目录")
    has_direct_content = fields.Boolean(description="是否有直接内容")
    sort_order = fields.Integer(description="排序顺序")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")
    children = fields.List(fields.Nested(lambda: DirectoryTreeItemSchema()), description="子目录列表")
    direct_content = fields.Nested(ItemBriefResponseSchema, allow_none=True, description="目录直接内容")
    items = fields.List(fields.Nested(ItemBriefResponseSchema), description="目录下的知识条目列表")

# 目录树响应Schema
class DirectoryTreeResponseSchema(Schema):
    """目录树响应Schema"""
    data = fields.List(fields.Nested(DirectoryTreeItemSchema), description="目录树列表")
    
class DirectoryCreateSchema(Schema):
    """创建目录请求Schema"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=100), description="目录标题")
    parent_id = fields.Integer(allow_none=True, description="父目录ID，不提供则创建顶级目录")
    sort_order = fields.Integer(default=0, description="排序顺序")

class DirectoryUpdateSchema(Schema):
    """更新目录请求Schema"""
    title = fields.String(validate=validate.Length(min=1, max=100), description="目录标题")
    parent_id = fields.Integer(allow_none=True, description="父目录ID，为null则变为顶级目录")
    sort_order = fields.Integer(description="排序顺序")

class DirectoryResponseSchema(Schema):
    """目录响应Schema"""
    id = fields.Integer(description="目录ID")
    title = fields.String(description="目录标题")
    level = fields.Integer(description="目录层级：1=顶级，2=子目录")
    parent_id = fields.Integer(allow_none=True, description="父目录ID")
    has_direct_content = fields.Boolean(description="是否有直接内容")
    sort_order = fields.Integer(description="排序顺序")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")
    children = fields.List(fields.Nested(lambda: DirectoryResponseSchema(exclude=("children",))), description="子目录列表")

class DirectoryListResponseSchema(Schema):
    """目录列表响应Schema"""
    data = fields.List(fields.Nested(DirectoryResponseSchema(exclude=("children",))), description="目录列表")

# 知识条目相关Schema
class ItemCreateSchema(Schema):
    """创建知识条目请求Schema"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=200), description="条目标题")
    content = fields.String(allow_none=True, description="纯文本内容")
    html_content = fields.String(allow_none=True, description="HTML格式内容")
    directory_id = fields.Integer(required=True, description="所属目录ID")
    is_directory_content = fields.Boolean(default=False, description="是否为目录直接内容")
    sort_order = fields.Integer(default=0, description="排序顺序")
    tags = fields.String(allow_none=True, description="标签，逗号分隔")

class ItemUpdateSchema(Schema):
    """更新知识条目请求Schema"""
    title = fields.String(validate=validate.Length(min=1, max=200), description="条目标题")
    content = fields.String(allow_none=True, description="纯文本内容")
    html_content = fields.String(allow_none=True, description="HTML格式内容")
    directory_id = fields.Integer(description="所属目录ID")
    sort_order = fields.Integer(description="排序顺序")
    tags = fields.String(allow_none=True, description="标签，逗号分隔")

class ItemResponseSchema(Schema):
    """知识条目响应Schema"""
    id = fields.Integer(description="条目ID")
    title = fields.String(description="条目标题")
    content = fields.String(description="纯文本内容")
    html_content = fields.String(description="HTML格式内容")
    directory_id = fields.Integer(description="所属目录ID")
    is_directory_content = fields.Boolean(description="是否为目录直接内容")
    sort_order = fields.Integer(description="排序顺序")
    views = fields.Integer(description="浏览次数")
    tags = fields.String(description="标签，逗号分隔")
    status = fields.Integer(description="状态: 1-正常, 0-禁用")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")

class ItemListResponseSchema(Schema):
    """知识条目列表响应Schema"""
    data = fields.List(fields.Nested(ItemResponseSchema), description="条目列表")

class ItemQuerySchema(Schema):
    """知识条目查询参数Schema"""
    directory_id = fields.Integer(description="目录ID筛选")
    keyword = fields.String(description="关键词搜索")
    page = fields.Integer(default=1, validate=validate.Range(min=1), description="页码")
    per_page = fields.Integer(default=20, validate=validate.Range(min=1, max=100), description="每页条数")