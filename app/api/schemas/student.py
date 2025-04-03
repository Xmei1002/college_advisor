# app/api/schemas/student.py
from marshmallow import Schema, fields, validate
from marshmallow import ValidationError, validates

class StudentProfileSchema(Schema):
    """学生基本信息提交验证Schema"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=50), description="学生姓名")
    gender = fields.String(required=True, validate=validate.OneOf(["男", "女"]), description="性别")
    ethnicity = fields.String(description="民族")
    phone = fields.String(required=True, description="联系电话")
    wechat_qq = fields.String(description="微信/QQ")
    school = fields.String(description="毕业学校")
    address = fields.String(description="家庭住址")
    candidate_number = fields.String(description="准考证号")
    id_card_number = fields.String(description="身份证号")  # 新增字段
    household_type = fields.String(required=True, validate=validate.OneOf(["农村户口", "城市户口"]), description="户籍类型")
    student_type = fields.String(validate=validate.OneOf(["应届生", "复读生"]), description="考生类型")
    
    guardian1_name = fields.String(description="第一联系人姓名")
    guardian1_phone = fields.String(description="第一联系人电话")
    guardian2_name = fields.String(description="第二联系人姓名")
    guardian2_phone = fields.String(description="第二联系人电话")
    
    left_eye_vision = fields.String(description="左眼视力情况")
    right_eye_vision = fields.String(description="右眼视力情况")
    color_vision = fields.String(description="色觉情况")
    height = fields.String(description="身高(CM)")
    weight = fields.String(description="体重(KG)")
    
    foreign_language = fields.String(description="外语语种")
    
    is_discredited = fields.Boolean(description="是否失信考生")
    discredit_reason = fields.String(description="失信原因")  # 新增字段
    strong_subjects = fields.String(description="优势科目")
    weak_subjects = fields.String(description="劣势科目")


class AcademicRecordSchema(Schema):
    """学生学业记录提交验证Schema"""
    selected_subjects = fields.String(required=True, description="高考选科")
    @validates('selected_subjects')
    def validate_selected_subjects(self, value):
        """验证选科是否符合要求：必须选择历史或物理其一，再从化学、生物、地理、政治中选择两科"""
        if not value:
            raise ValidationError("请选择科目")
        
        subjects = value.split(',')
        subjects = [s.strip() for s in subjects]
        
        # 验证科目总数是否为3
        if len(subjects) != 3:
            raise ValidationError("必须选择3门科目")
        
        # 验证是否包含历史或物理
        first_subjects = ["历史", "物理"]
        has_first_subject = any(subject in first_subjects for subject in subjects)
        if not has_first_subject:
            raise ValidationError("必须选择历史或物理作为首选科目")
        
        # 验证是否从化学、生物、地理、政治中选择了2科
        other_subjects = ["化学", "生物", "地理", "政治"]
        other_selected = [subject for subject in subjects if subject in other_subjects]
        
        if len(other_selected) != 2:
            raise ValidationError("必须从化学、生物、地理、政治中选择2门科目")
        
    
    gaokao_total_score = fields.String(description="高考总分")
    gaokao_ranking = fields.String(description="高考位次")
    standard_score = fields.String(description="标准分数")
    bonus_type = fields.String(description="加分类型")
    
    chinese_score = fields.String(description="语文成绩")
    math_score = fields.String(description="数学成绩")
    foreign_lang_score = fields.String(description="外语成绩")
    physics_score = fields.String(description="物理成绩")
    history_score = fields.String(description="历史成绩")
    chemistry_score = fields.String(description="化学成绩")
    biology_score = fields.String(description="生物成绩")
    geography_score = fields.String(description="地理成绩")
    politics_score = fields.String(description="政治成绩")
    
    mock_exam1_score = fields.String(description="第一次模考成绩")
    mock_exam2_score = fields.String(description="第二次模考成绩")
    mock_exam3_score = fields.String(description="第三次模考成绩")

class StudentResponseSchema(Schema):
    """学生信息响应Schema"""
    id = fields.Integer()
    user_id = fields.Integer()
    name = fields.String()
    gender = fields.String()
    ethnicity = fields.String()
    phone = fields.String()
    wechat_qq = fields.String()
    school = fields.String()
    address = fields.String()
    candidate_number = fields.String()
    id_card_number = fields.String()  # 新增字段
    household_type = fields.String()
    student_type = fields.String()

    guardian1_name = fields.String()
    guardian1_phone = fields.String()
    guardian2_name = fields.String()
    guardian2_phone = fields.String()

    left_eye_vision = fields.String()
    right_eye_vision = fields.String()
    color_vision = fields.String()
    height = fields.Float()
    weight = fields.Float()

    foreign_language = fields.String()

    is_discredited = fields.Boolean()
    discredit_reason = fields.String()  # 新增字段
    strong_subjects = fields.String()
    weak_subjects = fields.String()



class AcademicRecordResponseSchema(Schema):
    """学业记录响应Schema"""
    id = fields.Integer()
    student_id = fields.Integer()
    selected_subjects = fields.String()
    gaokao_total_score = fields.String()
    gaokao_ranking = fields.String()
    standard_score = fields.String()
    bonus_type = fields.String()

    chinese_score = fields.String()
    math_score = fields.String()
    foreign_lang_score = fields.String()
    physics_score = fields.String()
    history_score = fields.String()

    chemistry_score = fields.String()
    biology_score = fields.String()
    geography_score = fields.String()
    politics_score = fields.String()

    mock_exam1_score = fields.String()
    mock_exam2_score = fields.String()
    mock_exam3_score = fields.String()

