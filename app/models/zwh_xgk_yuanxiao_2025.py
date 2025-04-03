from app.extensions import db
from sqlalchemy.dialects.mysql import TINYINT

class ZwhXgkYuanxiao2025(db.Model):
    """院校信息表"""
    __tablename__ = 'zwh_xgk_yuanxiao_2025'
    
    cid = db.Column(db.Integer, primary_key=True, comment='编号')
    aid = db.Column(db.Integer)
    cname = db.Column(db.String(250), comment='高校名称')
    sort = db.Column(db.Integer, comment='热门高校排序')
    uncode = db.Column(db.String(250), comment='高校代码')
    status = db.Column(TINYINT, server_default=db.text("'1'"), comment='状态')
    tese = db.Column(db.String(250), comment='学校特色')
    leixing = db.Column(db.String(250), server_default=db.text("'1'"), comment='学校类型')
    xingzhi = db.Column(db.SmallInteger, server_default=db.text("'1'"), comment='学校性质')
    baoyan = db.Column(db.String(250), comment='保研')
    minxuefei = db.Column(db.Integer, comment='最低学费')
    maxxuefei = db.Column(db.Integer, comment='最高学费')
    teshu = db.Column(db.SmallInteger, comment='特殊类型')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'cid': self.cid,
            'aid': self.aid,
            'cname': self.cname,
            'sort': self.sort,
            'uncode': self.uncode,
            'status': self.status,
            'tese': self.tese,
            'leixing': self.leixing,
            'xingzhi': self.xingzhi,
            'baoyan': self.baoyan,
            'minxuefei': self.minxuefei,
            'maxxuefei': self.maxxuefei,
            'teshu': self.teshu
        }