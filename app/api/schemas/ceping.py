from marshmallow import Schema, fields, validate

# MBTI测评相关Schema
class MbtiQuestionSchema(Schema):
    """MBTI测评题目"""
    id = fields.Integer(description="题目ID")
    t_id = fields.Integer(description="题目序号")
    title = fields.String(description="题目标题")
    content = fields.String(description="题目内容")
    a = fields.String(description="选项A")
    aa = fields.String(description="选项A对应维度")
    b = fields.String(description="选项B")
    bb = fields.String(description="选项B对应维度")

class MbtiAnswerSubmitSchema(Schema):
    """MBTI测评答案提交"""
    student_id = fields.Integer(required=True, description="学生ID")
    answer = fields.Dict(
        keys=fields.String(description="题目ID/序号"), 
        values=fields.String(validate=validate.OneOf(['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']), description="答案值"),
        required=True,
        description="答案数据，格式为{题目ID: 答案值}"
    )

class MbtiTypeDetailSchema(Schema):
    """MBTI类型详情"""
    name = fields.String(description="类型代码")
    xingge = fields.String(description="性格特质")
    youshi = fields.String(description="优势分析")
    lueshi = fields.String(description="劣势分析")
    zhiye = fields.String(description="职业领域")
    dianxing = fields.String(description="典型职业")

class MbtiScoreSchema(Schema):
    """MBTI分数"""
    count = fields.Integer(description="得分")

class MbtiAnswerResponseSchema(Schema):
    """MBTI测评结果响应"""
    id = fields.Integer(description="答案记录ID")
    personality_type = fields.String(description="人格类型")
    type_detail = fields.Nested(MbtiTypeDetailSchema, description="类型详情")
    scores = fields.Dict(keys=fields.String(), values=fields.Nested(MbtiScoreSchema), description="各维度得分")
    addtime = fields.Integer(description="提交时间戳")

# 职业兴趣测评相关Schema
class JobQuestionSchema(Schema):
    """职业兴趣测评题目"""
    id = fields.Integer(description="题目ID")
    tid = fields.Integer(description="题目序号")
    wid = fields.String(description="题目对应类型")
    title = fields.String(description="题目标题")
    content = fields.String(description="题目内容")
    nums = fields.Integer(description="题目数量")
    timu = fields.String(description="题目详情")

class JobAnswerSubmitSchema(Schema):
    """职业兴趣测评答案提交"""
    student_id = fields.Integer(required=True, description="学生ID")
    answer = fields.Dict(
        keys=fields.String(description="题目ID"), 
        values=fields.String(validate=validate.OneOf(['A', 'B']), description="答案值，A表示选择，B表示不选择"),
        required=True,
        description="答案数据，格式为{题目ID: 答案值}"
    )

class JobTypeDetailSchema(Schema):
    """职业兴趣类型详情"""
    title = fields.String(description="类型代码")
    zyxqqx = fields.String(description="职业兴趣倾向")
    xgqx = fields.String(description="性格倾向")
    zyly = fields.String(description="职业领域")
    dxzy = fields.String(description="典型职业")

class JobAnswerResponseSchema(Schema):
    """职业兴趣测评结果响应"""
    id = fields.Integer(description="答案记录ID")
    job_type = fields.String(description="职业兴趣类型")
    type_detail = fields.Nested(JobTypeDetailSchema, description="类型详情")
    recommended_majors = fields.List(fields.String(), description="推荐专业")
    scores = fields.Dict(keys=fields.String(), values=fields.Integer(), description="各类型得分")
    addtime = fields.Integer(description="提交时间戳") 