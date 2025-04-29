# app/api/endpoints/job.py
from flask import request, current_app, send_file
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from flask_smorest import Blueprint
from app.models.ceping_job_answer import CepingJobAnswer
from app.models.ceping_job_timu import CepingJobTimu
from app.models.ceping_job_leixing import CepingJobLeixing
from app.models.ceping_job_zhuanye import CepingJobZhuanye
from app.extensions import db

from app.services.ceping.pdf_service import PdfService
from app.api.schemas.ceping import (
    JobQuestionSchema, 
    JobAnswerSubmitSchema, 
    JobAnswerResponseSchema
)
import json
import time

job_bp = Blueprint(
    'job', 
    'job',
    description='职业兴趣测评相关接口',
)

@job_bp.route('/questions', methods=['GET'])
@job_bp.response(200, JobQuestionSchema(many=True))
@api_error_handler
def get_questions():
    """获取职业兴趣测评题目
    """
    # 不需要student_id也可以获取题目
    questions = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
    questions_data = [
        {
            'id': q.id,
            'tid': q.tid,
            'wid': q.wid,
            'title': q.title,
            'content': q.content,
            'nums': q.nums,
            'timu': q.timu
        } for q in questions
    ]
    
    return APIResponse.success(
        data=questions_data,
        message="获取题目成功"
    )

@job_bp.route('/submit', methods=['POST'])
@job_bp.arguments(JobAnswerSubmitSchema)
@job_bp.response(200, JobAnswerResponseSchema)
@api_error_handler
def submit_answer(args):
    """提交职业兴趣测评答案"""
    # 从请求参数获取student_id和answer
    student_id = args.get('student_id')
    answer_data = args.get('answer', {})
    
    # 获取题目信息
    timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
    timu_dict = {str(q.tid): {"tid": q.tid, "wid": q.wid} for q in timu}
    
    # 计算结果
    count = {
        "S": {'count': 0},
        "R": {'count': 0},
        "C": {'count': 0},
        "E": {'count': 0},
        "I": {'count': 0},
        "A": {'count': 0}
    }
    
    # 统计各维度得分
    for question_id, answer_value in answer_data.items():
        if question_id in timu_dict and answer_value == "A":
            wid = timu_dict[question_id]["wid"]
            count[wid]['count'] += 1
    
    # 按分数排序
    sorted_count = sorted(count.items(), key=lambda x: x[1]['count'], reverse=True)
    
    # 取前三种类型
    jieguo = ""
    for key, _ in sorted_count[:3]:
        jieguo += key
    
    # 检查是否冲突
    chongtu = CepingJobLeixing.query.filter_by(title=jieguo, chongtu=1).first()
    if chongtu:
        return APIResponse.error("职业类型冲突", code=400)
    
    # 检查是否已存在该学生的测评记录
    existing_answer = CepingJobAnswer.query.filter_by(student_id=student_id).first()
    
    if existing_answer:
        # 更新现有记录
        existing_answer.answer = json.dumps(answer_data)
        existing_answer.jieguo = jieguo
        existing_answer.addtime = int(time.time())
        db.session.commit()
        
        return APIResponse.success(
            data={
                'id': existing_answer.id,
            },
            message="更新成功"
        )
    else:
        # 创建新记录
        new_answer = CepingJobAnswer(
            student_id=student_id,
            answer=json.dumps(answer_data),
            jieguo=jieguo,
            addtime=int(time.time())
        )
        
        db.session.add(new_answer)
        db.session.commit()
        
        return APIResponse.success(
            data={
                'id': new_answer.id,
            },
            message="提交成功"
        )

@job_bp.route('/result/<int:student_id>', methods=['GET'])
@job_bp.response(200, JobAnswerResponseSchema)
@api_error_handler
def get_result(student_id):
    """获取职业兴趣测评结果

    """
    # 查询答案记录
    answer = CepingJobAnswer.query.filter_by(student_id=student_id).first()
    if not answer:
        return APIResponse.success(message="记录不存在", code=200)
    
    # 重新计算各维度得分
    timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
    timu_dict = {str(q.tid): {"tid": q.tid, "wid": q.wid} for q in timu}
    
    answer_data = json.loads(answer.answer)
    
    count = {
        "S": {'count': 0, 'color': 'green'},
        "R": {'count': 0, 'color': 'green'},
        "C": {'count': 0, 'color': 'green'},
        "E": {'count': 0, 'color': 'green'},
        "I": {'count': 0, 'color': 'green'},
        "A": {'count': 0, 'color': 'green'}
    }
    
    # 统计各维度得分
    for question_id, answer_value in answer_data.items():
        if question_id in timu_dict and answer_value == "A":
            wid = timu_dict[question_id]["wid"]
            count[wid]['count'] += 1
    
    # 设置颜色
    for key in count:
        if key in answer.jieguo:
            count[key]['color'] = 'orange'
        else:
            # 如果不在结果中且分数大于0，则减1
            if count[key]['count'] > 0:
                count[key]['count'] -= 1
    
    # 获取类型详情
    type_info = CepingJobLeixing.query.filter_by(title=answer.jieguo).first()
    type_detail = None
    if type_info:
        type_detail = {
            'title': type_info.title,
            'zyxqqx': type_info.zyxqqx,
            'xgqx': type_info.xgqx,
            'zyly': type_info.zyly,
            'dxzy': type_info.dxzy
        }
    
    # 获取推荐专业
    recommended_majors = CepingJobZhuanye.query.filter_by(title=answer.jieguo).all()
    majors = [major.zymc for major in recommended_majors]
    
    return APIResponse.success(
        data={
            'id': answer.id,
            'job_type': answer.jieguo,
            'type_detail': type_detail,
            'recommended_majors': majors,
            'scores': {k: v['count'] for k, v in count.items()},
            'addtime': answer.addtime
        },
        message="获取结果成功"
    )

@job_bp.route('/report/<int:student_id>', methods=['GET'])
@api_error_handler
def generate_report(student_id):
    """
        生成职业兴趣测评报告
    """
    # 查询答案记录
    answer = CepingJobAnswer.query.filter_by(student_id=student_id).first()
    if not answer:
        return APIResponse.error("记录不存在", code=404)
    
    # 获取学生信息
    from app.models.studentProfile import Student
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        return APIResponse.error("学生信息不存在", code=404)
    
    # 生成PDF报告
    pdf_service = PdfService()
    pdf_path = pdf_service.generate_job_report(answer, student)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"职业兴趣_{student.name}.pdf"
    )