from app.extensions import db
from sqlalchemy.dialects.mysql import TINYINT

# 省定线表模型
class ZwhDivisions(db.Model):
    """省定线表"""
    __tablename__ = 'zwh_divisions'
    __table_args__ = {'comment': '省定线表'}

    id = db.Column(db.Integer, primary_key=True)
    suid = db.Column(db.SmallInteger, comment='科别')
    bid = db.Column(db.SmallInteger, comment='批次')
    dyear = db.Column(db.Integer, comment='年份')
    dscore = db.Column(db.DECIMAL(11, 0), comment='省定分数线')
    aid = db.Column(db.SmallInteger, comment='省份')
    status = db.Column(TINYINT, comment='状态')
    remarks = db.Column(db.String(250), comment='备注')
    numplan = db.Column(db.Integer, comment='计划人数')
    numabove = db.Column(db.Integer, comment='达线人数')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'suid': self.suid,
            'bid': self.bid,
            'dyear': self.dyear,
            'dscore': float(self.dscore) if self.dscore else None,
            'aid': self.aid,
            'status': self.status,
            'remarks': self.remarks,
            'numplan': self.numplan,
            'numabove': self.numabove
        }
