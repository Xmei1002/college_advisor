# 定义参数验证架构
from marshmallow import Schema, fields, validate, EXCLUDE  

class GenerateAiPlanSchema(Schema):
    student_id = fields.Integer(required=True, description='学生ID')

class StudentVolunteerPlanSchema(Schema):
    """学生志愿方案模式"""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(required=True)
    planner_id = fields.Int(required=True)
    version = fields.Int(dump_only=True)
    is_current = fields.Bool(dump_only=True)
    remarks = fields.Str()
    generation_status = fields.Str(dump_only=True)
    generation_progress = fields.Int(dump_only=True)
    generation_message = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class PlanHistoryResponseSchema(Schema):
    """志愿方案历史响应模式"""
    success = fields.Bool()
    message = fields.Str()
    code = fields.Int()
    data = fields.List(fields.Nested(StudentVolunteerPlanSchema))
    pagination = fields.Dict()

class PlanDetailResponseSchema(Schema):
    """志愿方案详情响应模式"""
    success = fields.Bool()
    message = fields.Str()
    code = fields.Int()
    data = fields.Dict()

class PlanHistoryQueryParamsSchema(Schema):
    """查询历史志愿方案的参数模式"""
    page = fields.Int(missing=1, description="页码")
    per_page = fields.Int(missing=10, description="每页条数")

class PlanDetailQueryParamsSchema(Schema):
    """查询志愿方案详情的参数模式"""
    include_details = fields.Bool(missing=True, description="是否包含详细志愿信息")
    category_id = fields.Integer(required=False, description="按类别ID过滤(1:冲, 2:稳, 3:保)")
    group_id = fields.Integer(required=False, description="按志愿段ID过滤(1-12)")
    volunteer_index = fields.Integer(required=False, description="按志愿序号过滤(1-48)")


# 专业志愿Schema
class VolunteerSpecialtySchema(Schema):
    class Meta:
        unknown = EXCLUDE  # 允许忽略未知字段
    specialty_id = fields.Integer(required=True)
    specialty_code = fields.String(allow_none=True)
    specialty_name = fields.String(required=True)
    specialty_index = fields.Integer(required=True, validate=validate.Range(min=1, max=6))
    prediction_score = fields.Integer(allow_none=True)
    plan_number = fields.Integer(allow_none=True)
    tuition = fields.Integer(allow_none=True)
    remarks = fields.String(allow_none=True)
    ai_analysis = fields.String(allow_none=True)
    fenshuxian_id = fields.Integer(allow_none=True)

# 院校志愿Schema
class VolunteerCollegeSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # 允许忽略未知字段
    category_id = fields.Integer(required=True, validate=validate.Range(min=1, max=3))
    group_id = fields.Integer(required=True, validate=validate.Range(min=1, max=12))
    volunteer_index = fields.Integer(required=True, validate=validate.Range(min=1, max=48))
    college_id = fields.Integer(required=True)
    college_name = fields.String(required=True)
    college_group_id = fields.Integer(required=True)
    score_diff = fields.Integer(allow_none=True)
    prediction_score = fields.Integer(allow_none=True)
    recommend_type = fields.String(validate=validate.OneOf(['ai', 'planner']), default='ai')
    ai_analysis = fields.String(allow_none=True)
    area_name = fields.String(allow_none=True)
    group_name = fields.String(allow_none=True)
    min_tuition = fields.Integer(allow_none=True)
    max_tuition = fields.Integer(allow_none=True)
    min_score = fields.Integer(allow_none=True)
    plan_number = fields.Integer(allow_none=True)
    school_type_text = fields.String(allow_none=True)
    subject_requirements = fields.Dict(allow_none=True)
    tese_text = fields.List(fields.String(), allow_none=True)
    teshu_text = fields.List(fields.String(), allow_none=True)
    uncode = fields.String(allow_none=True)
    specialties = fields.List(fields.Nested(VolunteerSpecialtySchema), required=True)

# 志愿更新Schema
class UpdateVolunteerPlanSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # 允许忽略未知字段
    remarks = fields.String(allow_none=True)
    colleges = fields.List(fields.Nested(VolunteerCollegeSchema), required=True)

# 志愿类别分析Schema
class VolunteerCategoryAnalysisSchema(Schema):
    id = fields.Integer()
    plan_id = fields.Integer()
    category_id = fields.Integer()
    analysis_content = fields.String(allow_none=True)
    status = fields.String()
    error_message = fields.String(allow_none=True)
    analyzed_at = fields.String(allow_none=True)
    created_at = fields.String()
    updated_at = fields.String()

# 志愿方案响应Schema
class VolunteerPlanResponseSchema(Schema):
    id = fields.Integer()
    student_id = fields.Integer()
    planner_id = fields.Integer()
    version = fields.Integer()
    is_current = fields.Boolean()
    remarks = fields.String(allow_none=True)
    generation_status = fields.String()
    generation_progress = fields.Integer()
    generation_message = fields.String(allow_none=True)
    created_at = fields.String()
    updated_at = fields.String()
    colleges = fields.List(fields.Nested(VolunteerCollegeSchema), allow_none=True)
    category_analyses = fields.List(fields.Nested(VolunteerCategoryAnalysisSchema), allow_none=True)