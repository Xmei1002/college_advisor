from marshmallow import Schema, fields, validate

class SpecialtySchema(Schema):
    """专业信息"""
    spid = fields.Integer(description="专业ID")
    spname = fields.String(description="专业名称")
    spcode = fields.String(description="专业代码")
    specialty_direction = fields.String(description="专业方向")
    tuition = fields.Integer(description="学费")
    prediction_score = fields.Integer(description="预测分数")
    plan_number = fields.Integer(description="专业计划招生人数")
    teacher = fields.String(description="是否为师范类")
    doctor = fields.String(description="是否为医学类")
    official = fields.String(description="是否为公务员类")
    content = fields.String(description="专业介绍")

class SubjectRequirementsSchema(Schema):
    """选科要求"""
    wu = fields.Integer(description="物理要求")
    shi = fields.Integer(description="历史要求")
    hua = fields.Integer(description="化学要求")
    sheng = fields.Integer(description="生物要求")
    di = fields.Integer(description="地理要求")
    zheng = fields.Integer(description="政治要求")

class CollegeGroupSchema(Schema):
    """带专业列表的学校专业组信息"""
    cgid = fields.Integer(description="专业组ID")
    cid = fields.Integer(description="学校ID")
    cname = fields.String(description="学校名称")
    uncode = fields.String(description="学校代码")
    school_type = fields.String(description="学校类型")
    school_nature = fields.Integer(description="学校性质")
    area_name = fields.String(description="地区名称")
    group_name = fields.String(description="专业组名称")
    min_score = fields.Integer(description="最低分数")
    score_diff = fields.Integer(description="分差")
    min_tuition = fields.Integer(description="最低学费")
    max_tuition = fields.Integer(description="最高学费")
    plan_number = fields.Integer(description="计划人数")
    specialty_count = fields.Integer(description="专业数量")
    recommendation_level = fields.String(description="推荐等级")
    recommendation_group = fields.String(description="推荐分组")
    subject_requirements = fields.Nested(SubjectRequirementsSchema, description="选科要求")
    specialties = fields.List(fields.Nested(SpecialtySchema), description="专业列表")
    tese = fields.String(description="特色类型")
    tese_text = fields.List(fields.String(), description="特色类型文本")
    teshu = fields.String(description="特殊类型")
    teshu_text = fields.List(fields.String(), description="特殊类型文本")
    school_type_text = fields.String(description="学校类型文本")

class CategoryFilterSchema(Schema):
    """按类别和志愿段筛选请求参数"""
    score = fields.Integer(required=True, validate=validate.Range(min=0, max=750), description="学生分数")
    subject_type = fields.Integer(required=True, validate=validate.OneOf([1, 2]), description="科别：1-文科，2-理科")
    education_level = fields.Integer(required=True, validate=validate.OneOf([11, 12]), description="学历层次：11-本科，12-专科")
    category_id = fields.Integer(required=True, validate=validate.OneOf([1, 2, 3]), description="类别ID：1-冲，2-稳，3-保")
    group_id = fields.Integer(required=True, validate=validate.Range(min=1, max=12), description="志愿段ID：1-12，对应不同志愿段")
    student_subjects = fields.Dict(required=True, description="学生选科情况，例如：{'wu': 1, 'hua': 1, 'sheng': 2, 'shi': 2, 'di': 2, 'zheng': 2}")
    area_ids = fields.List(fields.Integer(), required=False, description="地区ID列表，支持多选")  # 修改为列表
    specialty_types = fields.List(fields.Integer(), required=False, description="专业类型ID列表，支持多选")  # 修改为列表
    mode = fields.String(required=False, validate=validate.OneOf(['smart', 'professional', 'free']), description="模式：智能、专业、自由")
    page = fields.Integer(required=False, validate=validate.Range(min=1), default=1, description="页码")
    per_page = fields.Integer(required=False, validate=validate.Range(min=1, max=100), default=20, description="每页记录数")
    tese_types = fields.List(fields.Integer(), required=False, description="特色类型ID列表，支持多选")  # 修改为列表
    leixing_types = fields.List(fields.Integer(), required=False, description="类型ID列表，支持多选")  # 修改为列表
    teshu_types = fields.List(fields.Integer(), required=False, description="特殊类型ID列表，支持多选")  # 修改为列表

class CollegeCategoryResponseSchema(Schema):
    """按类别查询院校响应"""
    data = fields.List(fields.Nested(CollegeGroupSchema), description="院校专业组列表")
    pagination = fields.Dict(description="分页信息")

class CategoryFilterSchemaByStuedntID(Schema):
    """类别筛选参数"""
    student_id = fields.Integer(required=True, description="学生ID")
    category_id = fields.Integer(validate=validate.Range(min=1, max=3), description="类别ID：1-冲刺，2-稳妥，3-保底")
    group_id = fields.Integer(validate=validate.Range(min=1, max=12), description="志愿段ID：1-12")
    mode = fields.String(validate=validate.OneOf(['smart', 'professional', 'free']), description="分类模式：smart-智能，professional-专业，free-自由")
    page = fields.Integer(validate=validate.Range(min=1), description="页码，从1开始")
    per_page = fields.Integer(validate=validate.Range(min=1, max=100), description="每页记录数")