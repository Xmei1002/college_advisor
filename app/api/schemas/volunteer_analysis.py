from marshmallow import Schema, fields

class VolunteerCategorySchema(Schema):
    plan_id = fields.Int(required=True, description="志愿计划ID")
    category_id = fields.Int(required=True, description="类别ID，例如1.冲, 2.稳, 3.保")
    
class QueryAnalysisResultSchema(Schema):
    """查询分析结果参数Schema"""
    plan_id = fields.Integer(required=True, description="志愿方案ID")
    category_id = fields.Integer(required=True, description="类别ID")

class CollegeAnalysisSchema(Schema):
    """院校分析请求Schema"""
    volunteer_college_id = fields.Integer(required=True, description="志愿院校ID")

class SpecialtyAnalysisSchema(Schema):
    """专业分析请求Schema"""
    specialty_id = fields.Integer(required=True, description="志愿专业ID")