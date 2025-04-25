from app.extensions import db

class CepingJobZhuanye(db.Model):
    """职业测评专业表"""
    __tablename__ = 'ceping_job_zhuanye'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), comment='特征名称')
    zymc = db.Column(db.String(250), comment='专业名称')
    tid = db.Column(db.String(250), comment='tid')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'title': self.title,
            'zymc': self.zymc,
            'tid': self.tid
        }