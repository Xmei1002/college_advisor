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
import json
import time

job_bp = Blueprint(
    'job', 
    'job',
    description='职业兴趣测评相关接口',
)

@job_bp.route('/questions', methods=['GET'])
@api_error_handler
def get_questions():
    """获取职业兴趣测评题目"""
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
@api_error_handler
def submit_answer():
    """提交职业兴趣测评答案"""
    # 从请求体获取student_id
    student_id = request.json.get('student_id')
    if not student_id:
        return APIResponse.error("缺少学生ID", code=400)
        
    answer_data = request.json.get('answer', {})
    
    # 获取题目信息
    timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
    timu_dict = {str(q.id): {"tid": q.tid, "wid": q.wid} for q in timu}
    
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
    
    # 保存答案和结果
    new_answer = CepingJobAnswer(
        student_id=student_id,
        answer=json.dumps(answer_data),
        jieguo=jieguo,
        addtime=int(time.time())
    )
    
    db.session.add(new_answer)
    db.session.commit()
    
    # 获取类型详情
    type_info = CepingJobLeixing.query.filter_by(title=jieguo).first()
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
    recommended_majors = CepingJobZhuanye.query.filter_by(title=jieguo).all()
    majors = [major.zymc for major in recommended_majors]
    
    return APIResponse.success(
        data={
            'id': new_answer.id,
            'job_type': jieguo,
            'type_detail': type_detail,
            'recommended_majors': majors,
            'scores': {k: v['count'] for k, v in count.items()}
        },
        message="提交成功"
    )

@job_bp.route('/result/<int:answer_id>', methods=['GET'])
@api_error_handler
def get_result(answer_id):
    """获取职业兴趣测评结果"""
    # 查询答案记录
    answer = CepingJobAnswer.query.filter_by(id=answer_id).first()
    if not answer:
        return APIResponse.error("记录不存在", code=404)
    
    # 重新计算各维度得分
    timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
    timu_dict = {str(q.id): {"tid": q.tid, "wid": q.wid} for q in timu}
    
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

@job_bp.route('/report/<int:answer_id>', methods=['GET'])
@api_error_handler
def generate_report(answer_id):
    """生成职业兴趣测评报告"""
    student_id = request.args.get('student_id')
    if not student_id:
        return APIResponse.error("缺少学生ID", code=400)
    
    # 查询答案记录
    answer = CepingJobAnswer.query.filter_by(id=answer_id, student_id=student_id).first()
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
        download_name=f"职业兴趣_{student.name}_{answer_id}.pdf"
    )