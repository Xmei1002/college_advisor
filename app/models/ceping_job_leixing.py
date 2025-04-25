from app.extensions import db

class CepingJobLeixing(db.Model):
    """职业类型表"""
    __tablename__ = 'ceping_job_leixing'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), comment='类型组合名称')
    chongtu = db.Column(db.String(250), comment='是否冲突组合')
    zyxqqx = db.Column(db.Text, comment='职业兴趣倾向')
    xgqx = db.Column(db.Text, comment='性格倾向')
    zyly = db.Column(db.Text, comment='职业领域')
    dxzy = db.Column(db.Text, comment='典型职业')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'title': self.title,
            'chongtu': self.chongtu,
            'zyxqqx': self.zyxqqx,
            'xgqx': self.xgqx,
            'zyly': self.zyly,
            'dxzy': self.dxzy
        }