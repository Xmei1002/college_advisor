from app.extensions import db

class CepingMbtiAnswer(db.Model):
    """MBTI测评答案表"""
    __tablename__ = 'ceping_mbti_answer'
    
    id = db.Column(db.Integer, primary_key=True, comment='编号')
    answer = db.Column(db.Text, comment='答案')
    addtime = db.Column(db.Integer, comment='提交时间')
    jieguo = db.Column(db.Text, comment='结果类型')
    student_id = db.Column(db.Integer, comment='学生ID')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'answer': self.answer,
            'addtime': self.addtime,
            'jieguo': self.jieguo,
            'student_id': self.student_id
        }