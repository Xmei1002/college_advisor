from app.extensions import db

class CepingJobTimu(db.Model):
    """职业测评题目表"""
    __tablename__ = 'ceping_job_timu'
    
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, comment='题目编号')
    wid = db.Column(db.String(250), comment='维度编号')
    title = db.Column(db.String(250), comment='题目内容')
    content = db.Column(db.String(250), comment='备注描述')
    nums = db.Column(db.String(250), comment='选项数量')
    timu = db.Column(db.String(250), comment='选项内容')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'tid': self.tid,
            'wid': self.wid,
            'title': self.title,
            'content': self.content,
            'nums': self.nums,
            'timu': self.timu
        }