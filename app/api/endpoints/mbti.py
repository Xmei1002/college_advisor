# app/api/endpoints/mbti.py
from flask import request, current_app, send_file
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from flask_smorest import Blueprint
from app.models.ceping_mbti_answer import CepingMbtiAnswer
from app.models.ceping_mbti_timu import CepingMbtiTimu
from app.models.ceping_mbti_leixing import CepingMbtiLeixing
from app.services.ceping.pdf_service import PdfService
import json
import time
from app.extensions import db

mbti_bp = Blueprint(
    'mbti', 
    'mbti',
    description='MBTI测评相关接口',
)

@mbti_bp.route('/questions', methods=['GET'])
@api_error_handler
def get_questions():
    """获取MBTI测评题目"""
    # 不需要student_id也可以获取题目
    questions = CepingMbtiTimu.query.order_by(CepingMbtiTimu.t_id).all()
    questions_data = [
        {
            'id': q.id,
            't_id': q.t_id,
            'title': q.title,
            'content': q.content,
            'a': q.a,
            'aa': q.aa,
            'b': q.b,
            'bb': q.bb
        } for q in questions
    ]
    
    return APIResponse.success(
        data=questions_data,
        message="获取题目成功"
    )

@mbti_bp.route('/submit', methods=['POST'])
@api_error_handler
def submit_answer():
    """提交MBTI测评答案"""
    # 从请求体获取student_id
    student_id = request.json.get('student_id')
    if not student_id:
        return APIResponse.error("缺少学生ID", code=400)
        
    answer_data = request.json.get('answer', {})
    
    # 计算结果
    count = {
        "E": {'count': 0},
        "I": {'count': 0},
        "S": {'count': 0},
        "N": {'count': 0},
        "T": {'count': 0},
        "F": {'count': 0},
        "J": {'count': 0},
        "P": {'count': 0}
    }
    
    # 统计各维度得分
    for answer_key, answer_value in answer_data.items():
        if answer_value in count:
            count[answer_value]['count'] += 1
    
    # 计算人格类型
    personality_type = ""
    if count['I']['count'] >= count['E']['count']:
        personality_type += 'I'
    else:
        personality_type += 'E'
        
    if count['N']['count'] >= count['S']['count']:
        personality_type += 'N'
    else:
        personality_type += 'S'
        
    if count['F']['count'] >= count['T']['count']:
        personality_type += 'F'
    else:
        personality_type += 'T'
        
    if count['P']['count'] >= count['J']['count']:
        personality_type += 'P'
    else:
        personality_type += 'J'
    
    # 保存答案和结果
    new_answer = CepingMbtiAnswer(
        student_id=student_id,
        answer=json.dumps(answer_data),
        jieguo=json.dumps(count),
        addtime=int(time.time())
    )
    
    db.session.add(new_answer)
    db.session.commit()
    
    # 获取类型详情
    type_info = CepingMbtiLeixing.query.filter_by(name=personality_type).first()
    type_detail = None
    if type_info:
        type_detail = {
            'name': type_info.name,
            'xingge': type_info.xingge,
            'youshi': type_info.youshi,
            'lueshi': type_info.lueshi,
            'zhiye': type_info.zhiye,
            'dianxing': type_info.dianxing
        }
    
    return APIResponse.success(
        data={
            'id': new_answer.id,
            'personality_type': personality_type,
            'type_detail': type_detail,
            'scores': count
        },
        message="提交成功"
    )

@mbti_bp.route('/result/<int:answer_id>', methods=['GET'])
@api_error_handler
def get_result(answer_id):
    """获取MBTI测评结果"""
    # 从查询参数获取student_id
    student_id = request.args.get('student_id')
    if not student_id:
        return APIResponse.error("缺少学生ID", code=400)
    
    # 查询答案记录
    answer = CepingMbtiAnswer.query.filter_by(id=answer_id, student_id=student_id).first()
    if not answer:
        return APIResponse.error("记录不存在", code=404)
    
    # 解析结果
    jieguo = json.loads(answer.jieguo)
    
    # 计算人格类型
    personality_type = ""
    if jieguo['I']['count'] >= jieguo['E']['count']:
        personality_type += 'I'
    else:
        personality_type += 'E'
        
    if jieguo['N']['count'] >= jieguo['S']['count']:
        personality_type += 'N'
    else:
        personality_type += 'S'
        
    if jieguo['F']['count'] >= jieguo['T']['count']:
        personality_type += 'F'
    else:
        personality_type += 'T'
        
    if jieguo['P']['count'] >= jieguo['J']['count']:
        personality_type += 'P'
    else:
        personality_type += 'J'
    
    # 获取类型详情
    type_info = CepingMbtiLeixing.query.filter_by(name=personality_type).first()
    type_detail = None
    if type_info:
        type_detail = {
            'name': type_info.name,
            'xingge': type_info.xingge,
            'youshi': type_info.youshi,
            'lueshi': type_info.lueshi,
            'zhiye': type_info.zhiye,
            'dianxing': type_info.dianxing
        }
    
    return APIResponse.success(
        data={
            'id': answer.id,
            'personality_type': personality_type,
            'type_detail': type_detail,
            'scores': jieguo,
            'addtime': answer.addtime
        },
        message="获取结果成功"
    )

@mbti_bp.route('/report/<int:answer_id>', methods=['GET'])
@api_error_handler
def generate_report(answer_id):
    """生成MBTI测评报告"""
    student_id = request.args.get('student_id')
    if not student_id:
        return APIResponse.error("缺少学生ID", code=400)
    
    # 查询答案记录
    answer = CepingMbtiAnswer.query.filter_by(id=answer_id, student_id=student_id).first()
    if not answer:
        return APIResponse.error("记录不存在", code=404)
    
    # 获取学生信息
    from app.models.studentProfile import Student
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        return APIResponse.error("学生信息不存在", code=404)
    
    # 生成PDF报告
    pdf_service = PdfService()
    pdf_path = pdf_service.generate_mbti_report(answer, student)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"MBTI_{student.name}_{answer_id}.pdf"
    )