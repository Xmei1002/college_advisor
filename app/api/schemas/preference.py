# app/api/schemas/preference.py
from marshmallow import Schema, fields, pre_load

class CollegePreferenceBaseSchema(Schema):
    """学生填报志愿意向基础Schema"""
    preferred_locations = fields.String(description="意向地域，多个地区以逗号分隔")
    tuition_range = fields.String(description="学费范围，如'1万以内'、'1-2万'等")
    preferred_majors = fields.String(description="意向专业，多个专业以逗号分隔")
    school_types = fields.String(description="学校类型，如985,211,双一流等")
    preferred_schools = fields.String(description="意向学校，多个学校以逗号分隔")
    strategy = fields.String(description="填报策略：院校优先 or 专业优先")
    application_preference = fields.String(description="其他意向")
    
    # 新增字段
    volunteer_gradient_strategy = fields.String(description="志愿梯度策略：稳妥类型/激进类型/保底类型/自由设置")
    custom_gradient_counts = fields.Dict(description="自定义志愿梯度数量，JSON格式：{'chasing': 10, 'stable': 15, 'safe': 23}")
    application_batch = fields.String(description="报考批次：本科批/专科批，多选")
    
    # 报考限制字段
    accept_nonchangeable_major = fields.Boolean(allow_none=True, description="是否接受不可转专业中外合办专业")
    has_art_foundation = fields.Boolean(allow_none=True, description="是否具备美术基础")
    accept_overseas_study = fields.Boolean(allow_none=True, description="是否接受大学期间需出国就读")
    accept_high_fee_increase = fields.Boolean(allow_none=True, description="是否接受学费刺客专业")
    accept_dual_city_arrangement = fields.Boolean(allow_none=True, description="是否接受在两个城市上学安排")
    
    # 合并就业倾向字段
    career_direction = fields.String(description="就业发展方向，如金融,教师,医生等")

    # 家庭背景
    family_background = fields.String(description="家庭背景，如农村家庭、城市家庭等")

class CollegePreferenceStrategySchema(Schema):
    """填报策略Schema"""
    strategy = fields.String(required=True, description="填报策略")


class CollegePreferenceFullSchema(CollegePreferenceBaseSchema):
    """完整的学生填报志愿意向Schema"""
    strategy = fields.String(description="填报策略")


class CollegePreferenceResponseSchema(Schema):
    """学生填报志愿意向响应Schema"""
    id = fields.Integer()
    student_id = fields.Integer()
    preferred_locations = fields.String()
    tuition_range = fields.String()
    preferred_majors = fields.String()
    school_types = fields.String()
    preferred_schools = fields.String()
    strategy = fields.String()
    application_preference = fields.String()
    
    # 新增字段
    volunteer_gradient_strategy = fields.String()
    custom_gradient_counts = fields.Dict()
    application_batch = fields.String()
    gradient_counts = fields.Dict()
    
    # 报考限制字段
    accept_nonchangeable_major = fields.Boolean()
    has_art_foundation = fields.Boolean()
    accept_overseas_study = fields.Boolean()
    accept_overseas_study = fields.Boolean()
    accept_high_fee_increase = fields.Boolean()
    accept_dual_city_arrangement = fields.Boolean()
    
    family_background = fields.String()
    # 合并就业倾向字段
    career_direction = fields.String()
    
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
