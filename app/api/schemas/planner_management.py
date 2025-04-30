from marshmallow import Schema, fields, validate
from app.models.user import User
from app.api.schemas import PaginationSchema

# 定义创建规划师的Schema
class CreatePlannerManagementSchema(Schema):
    """创建规划师Schema"""
    username = fields.String(required=True, description="用户名")
    password = fields.String(required=True, description="密码")
    name = fields.String(description="姓名")
    phone = fields.String(description="联系电话")
    address = fields.String(description="地址")
    institution_id = fields.Integer(description="所属机构ID")  # 添加机构ID字段

# 定义更新规划师的Schema
class UpdatePlannerManagementSchema(Schema):
    """更新规划师Schema"""
    username = fields.String(description="用户名")
    password = fields.String(description="密码")
    name = fields.String(description="姓名")
    phone = fields.String(description="联系电话")
    address = fields.String(description="地址")
    status = fields.String(description="账号状态", validate=validate.OneOf([User.USER_STATUS_ACTIVE, User.USER_STATUS_INACTIVE]))

# 定义规划师详细信息的Schema
class PlannerInfoSchema(Schema):
    """规划师详细信息Schema"""
    id = fields.Integer(description="信息ID")
    user_id = fields.Integer(description="用户ID")
    phone = fields.String(description="联系电话")
    name = fields.String(description="姓名")
    address = fields.String(description="地址")
    created_at = fields.DateTime(description="创建时间")
    updated_at = fields.DateTime(description="更新时间")

# 定义规划师响应的Schema
class PlannerResponseSchema(Schema):
    """规划师响应Schema"""
    id = fields.Integer(description="规划师ID")
    username = fields.String(description="用户名")
    phone = fields.String(description="联系电话")
    status = fields.String(description="账号状态")
    created_at = fields.DateTime(description="创建时间")
    last_login_at = fields.DateTime(description="最后登录时间")
    student_count = fields.Integer(description="学生数量")
    planner_info = fields.Nested(PlannerInfoSchema, description="规划师详细信息")

# 定义规划师列表响应的Schema
class PlannerListResponseSchema(Schema):
    """规划师列表响应Schema"""
    items = fields.List(fields.Nested(PlannerResponseSchema), description="规划师列表")
    pagination = fields.Nested(PaginationSchema, description="分页信息") 