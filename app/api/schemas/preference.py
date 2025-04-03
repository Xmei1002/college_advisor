# app/api/schemas/preference.py
from marshmallow import Schema, fields, validate

class CollegePreferenceBaseSchema(Schema):
    """学生填报志愿意向基础Schema"""
    preferred_locations = fields.String(description="意向地域，多个地区以逗号分隔")
    tuition_range = fields.String(description="学费范围，如'1万以内'、'1-2万'等")
    preferred_majors = fields.String(description="意向专业，多个专业以逗号分隔")
    school_types = fields.String(description="学校类型，如985,211,双一流等")
    preferred_schools = fields.String(description="意向学校，多个学校以逗号分隔")
    strategy = fields.String(description="填报策略：院校优先 or 专业优先")
    application_preference = fields.String(description="报考倾向：家庭背景资源、意向院校以及专业等情况的详细描述")  

class CollegePreferenceStrategySchema(Schema):
    """填报策略Schema"""
    strategy = fields.String(required=True, description="填报策略")

class CollegePreferenceFullSchema(CollegePreferenceBaseSchema):
    """完整的学生填报志愿意向Schema"""
    strategy = fields.String(description="填报策略")

class CareerPreferenceSchema(Schema):
    """学生就业倾向信息Schema"""
    career_direction = fields.String(description="就业发展方向，如金融,教师,医生等")
    academic_preference = fields.String(description="学术学位偏好，如985,211等")
    civil_service_preference = fields.String(description="公务员意向")
    employment_location = fields.String(description="就业地区")
    income_expectation = fields.String(description="职业稳定性与收入平衡")
    work_stability = fields.String(description="工作稳定性")

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
    application_preference = fields.String()  # 添加报考倾向字段
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class CareerPreferenceResponseSchema(Schema):
    """学生就业倾向信息响应Schema"""
    id = fields.Integer()
    student_id = fields.Integer()
    career_direction = fields.String()
    academic_preference = fields.String()
    civil_service_preference = fields.String()
    employment_location = fields.String()
    income_expectation = fields.String()
    work_stability = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()