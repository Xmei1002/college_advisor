from marshmallow import Schema, fields, validate 

class HealthSchema(Schema):
    """健康检查响应模式"""
    status = fields.String(required=True, description="系统状态")
    version = fields.String(required=True, description="API版本")
    timestamp = fields.DateTime(required=True, description="当前服务器时间")
    environment = fields.String(required=True, description="运行环境")
    
class PaginationSchema(Schema):
    """分页信息"""
    total = fields.Integer(description="总记录数")
    pages = fields.Integer(description="总页数")
    page = fields.Integer(description="当前页")
    per_page = fields.Integer(description="每页记录数")
    has_next = fields.Boolean(description="是否有下一页")
    has_prev = fields.Boolean(description="是否有上一页")


# 发送验证码请求模式
class SendVerificationSchema(Schema):
    phone = fields.String(required=True, validate=validate.Regexp(r'^\d{11}$'), description="手机号码"),
    # planner_id = fields.Integer(required=True, description="规划师ID")

# 验证码校验模式
class VerifyCodeSchema(Schema):
    phone = fields.String(required=True, validate=validate.Regexp(r'^\d{11}$'), description="手机号码")
    code = fields.String(required=True, validate=validate.Regexp(r'^\d{6}$'), description="验证码")
    planner_id = fields.Integer(required=True, description="规划师ID")
    
# 学生注册模式
class StudentRegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Regexp(r'^\d{11}$'), description="手机号码作为用户名")
    password = fields.String(required=True, validate=validate.Length(min=6), description="密码")
    verification_code = fields.String(required=True, description="验证码")

# 登录请求模式
class LoginSchema(Schema):
    username = fields.String(required=True, description="用户名/手机号")
    password = fields.String(required=True, description="密码")

# 创建规划师账号模式
class CreatePlannerSchema(Schema):
    username = fields.String(required=True, description="规划师用户名")
    password = fields.String(required=True, validate=validate.Length(min=6), description="密码")

# 认证响应模式
class AuthResponseSchema(Schema):
    access_token = fields.String(required=True, description="访问令牌")
    refresh_token = fields.String(required=True, description="刷新令牌")
    user = fields.Dict(required=True, description="用户信息")

# 用户信息模式
class UserSchema(Schema):
    id = fields.Integer(required=True, description="用户ID")
    username = fields.String(required=True, description="用户名")
    user_type = fields.String(required=True, description="用户类型")
    status = fields.String(required=True, description="账号状态")
    created_at = fields.DateTime(required=True, description="创建时间")
    last_login_at = fields.DateTime(description="最后登录时间")


class PaginationQuerySchema(Schema):
    """分页查询参数"""
    page = fields.Integer(missing=1, validate=validate.Range(min=1), description="页码")
    per_page = fields.Integer(missing=10, validate=validate.Range(min=1, max=100), description="每页条数")
    keyword = fields.String(description="搜索关键词", missing=None)