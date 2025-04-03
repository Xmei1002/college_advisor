from marshmallow import Schema, fields, validate

# 定义请求和响应 Schema
class AssignStudentSchema(Schema):
    """分配学生请求Schema"""
    student_id = fields.Integer(required=True, description="学生ID")

class StudentListSchema(Schema):
    """学生列表响应Schema"""
    data = fields.List(fields.Nested(lambda: UserSchema_2()), description="学生列表")
    success = fields.Boolean(default=True, description="是否成功")
    message = fields.String(description="响应消息")
    code = fields.Integer(description="状态码")

class PlannerResponseSchema(Schema):
    """规划师响应Schema"""
    data = fields.Nested(lambda: UserSchema_2(), description="规划师信息")
    success = fields.Boolean(default=True, description="是否成功")
    message = fields.String(description="响应消息")
    code = fields.Integer(description="状态码")

# 导入或创建 UserSchema_2
class UserSchema_2(Schema):
    """用户信息Schema"""
    id = fields.Integer(description="用户ID")
    username = fields.String(description="用户名")
    user_type = fields.String(description="用户类型")
    status = fields.String(description="用户状态")
    created_at = fields.DateTime(description="创建时间")
    last_login_at = fields.DateTime(description="最后登录时间")
    planner = fields.Nested(lambda: UserSchema_2(only=("id", "username")), dump_only=True, description="规划师信息")
    student_count = fields.Integer(dump_only=True, description="学生数量")