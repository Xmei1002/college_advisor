from app.extensions import db

class CepingMbtiTimu(db.Model):
    """MBTI测评题目表"""
    __tablename__ = 'ceping_mbti_timu'
    
    id = db.Column(db.Integer, primary_key=True)
    t_id = db.Column(db.Integer, comment='题目编号')
    title = db.Column(db.String(250), comment='题目内容')
    content = db.Column(db.Text, comment='备注描述')
    a = db.Column(db.String(250), comment='A选项内容')
    aa = db.Column(db.String(250), comment='A选项类型')
    b = db.Column(db.String(250), comment='B选项内容')
    bb = db.Column(db.String(250), comment='B选项类型')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            't_id': self.t_id,
            'title': self.title,
            'content': self.content,
            'a': self.a,
            'aa': self.aa,
            'b': self.b,
            'bb': self.bb
        }