# app/api/schemas/institution.py

from marshmallow import Schema, fields, validate

class BaseInstitutionSchema(Schema):
    """机构基础数据模式"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100), description="机构名称")
    address = fields.Str(validate=validate.Length(max=200), description="机构地址")
    contact_phone = fields.Str(validate=validate.Length(max=20), description="联系电话")
    contact_email = fields.Str(validate=validate.Email(), description="联系邮箱")
    description = fields.Str(description="机构描述")
    status = fields.Int(validate=validate.OneOf([0, 1]), description="状态：1-激活, 0-禁用")

class CreateInstitutionSchema(BaseInstitutionSchema):
    """创建机构请求模式"""
    # 基础字段继承自BaseInstitutionSchema
    # 文件上传字段通过request.files处理，不在schema中定义

class UpdateInstitutionSchema(BaseInstitutionSchema):
    """更新机构请求模式"""
    name = fields.Str(validate=validate.Length(min=1, max=100), description="机构名称")
    # 其他字段继承自BaseInstitutionSchema并设为可选
    # 文件上传字段通过request.files处理

class InstitutionQuerySchema(Schema):
    """机构查询参数模式"""
    page = fields.Int(missing=1, validate=validate.Range(min=1), description="页码")
    per_page = fields.Int(missing=20, validate=validate.Range(min=1, max=100), description="每页数量")
    name = fields.Str(description="机构名称(模糊查询)")
    status = fields.Int(validate=validate.OneOf([0, 1]), description="状态筛选")

class InstitutionResponseSchema(BaseInstitutionSchema):
    """机构响应数据模式"""
    id = fields.Int(dump_only=True, description="机构ID")
    logo_path = fields.Str(dump_only=True, description="机构logo路径")
    qrcode_path = fields.Str(dump_only=True, description="机构二维码路径")
    created_at = fields.DateTime(dump_only=True, description="创建时间")
    updated_at = fields.DateTime(dump_only=True, description="更新时间")
    # 包含基础字段

class InstitutionListResponseSchema(Schema):
    """机构列表响应数据模式"""
    items = fields.List(fields.Nested(InstitutionResponseSchema), description="机构列表")
    pagination = fields.Dict(description="分页信息")