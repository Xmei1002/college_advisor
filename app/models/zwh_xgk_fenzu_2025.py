from app.extensions import db

# 分组模型
class ZwhXgkFenzu2025(db.Model):
    """院校专业分组表"""
    __tablename__ = 'zwh_xgk_fenzu_2025'

    cgid = db.Column(db.Integer, primary_key=True, comment='院校专业组的ID')
    newbid = db.Column(db.Integer, comment='对应新批次：11、本科；12、专科')
    newsuid = db.Column(db.Integer, comment='对应首选科目：1、历史；2、物理')
    oldcid = db.Column(db.Integer, comment='老的院校id')
    newcid = db.Column(db.Integer, comment='新的院校ID主要是统一uncode相同的院校')
    uncode = db.Column(db.String(255), comment='院校招生代码')
    wu = db.Column(db.Integer, comment='物理：1、必选；2无要求')
    shi = db.Column(db.Integer, comment='历史：1、必选；2无要求')
    hua = db.Column(db.Integer, comment='化学：1、必选；2无要求')
    sheng = db.Column(db.Integer, comment='生物：1、必选；2无要求')
    di = db.Column(db.Integer, comment='地理：1、必选；2无要求')
    zheng = db.Column(db.Integer, comment='政治：1、必选；2无要求')
    oldcgid = db.Column(db.Integer, comment='记录之前历年信息表中存储的分组id')
    minxuefei = db.Column(db.Integer, comment='最低学费')
    maxxuefei = db.Column(db.Integer, comment='最高学费')
    teshu = db.Column(db.SmallInteger, comment='特殊类型')
    cgname = db.Column(db.String(255), comment='专业组名称')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'cgid': self.cgid,
            'newbid': self.newbid,
            'newsuid': self.newsuid,
            'oldcid': self.oldcid,
            'newcid': self.newcid,
            'uncode': self.uncode,
            'wu': self.wu,
            'shi': self.shi,
            'hua': self.hua,
            'sheng': self.sheng,
            'di': self.di,
            'zheng': self.zheng,
            'oldcgid': self.oldcgid,
            'minxuefei': self.minxuefei,
            'maxxuefei': self.maxxuefei,
            'teshu': self.teshu,
            'cgname': self.cgname
        }
