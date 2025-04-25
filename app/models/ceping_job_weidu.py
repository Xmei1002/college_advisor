from app.extensions import db

class CepingJobWeidu(db.Model):
    """职业测评维度表"""
    __tablename__ = 'ceping_job_weidu'
    
    id = db.Column(db.Integer, primary_key=True)
    wid = db.Column(db.String(250), comment='维度编号')
    title = db.Column(db.String(250), comment='维度中文名')
    en = db.Column(db.String(250), comment='英文简称')
    content = db.Column(db.Text, comment='维度介绍')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'wid': self.wid,
            'title': self.title,
            'en': self.en,
            'content': self.content
        }