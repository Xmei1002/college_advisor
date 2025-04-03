from app.extensions import db
# 专业模型
class ZwhXgkZhuanye2025(db.Model):
    """专业信息表"""
    __tablename__ = 'zwh_xgk_zhuanye_2025'

    spid = db.Column(db.Integer, primary_key=True, comment='编号')
    spname = db.Column(db.String(250), comment='专业名称')
    spfather = db.Column(db.SmallInteger, comment='上级专业')
    content = db.Column(db.TEXT, comment='专业介绍')
    subclassid = db.Column(db.String(250), comment='Subclassid')
    teacher = db.Column(db.String(6), server_default=db.text("'否'"), comment='教师')
    doctor = db.Column(db.String(6), server_default=db.text("'否'"), comment='医生')
    official = db.Column(db.String(6), server_default=db.text("'否'"), comment='公务员')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'spid': self.spid,
            'spname': self.spname,
            'spfather': self.spfather,
            'content': self.content,
            'subclassid': self.subclassid,
            'teacher': self.teacher,
            'doctor': self.doctor,
            'official': self.official
        }