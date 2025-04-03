from app.extensions import db
from sqlalchemy.dialects.mysql import TINYINT

# 2025年分数线模型
class ZwhXgkFenshuxian2025(db.Model):
    """历史分数线管理"""
    __tablename__ = 'zwh_xgk_fenshuxian_2025'
    __table_args__ = (
        db.Index('default', 'cid', 'spid', 'bid', 'csbscore', 'csbplannum', 'suid', 'status', 'tuitions', 'year'),
        db.Index('yuce', 'yuce'),
        {'comment': '历史分数线管理'}
    )

    id = db.Column(db.Integer, primary_key=True, comment='编号')
    cid = db.Column(db.SmallInteger, comment='学校')
    spid = db.Column(db.SmallInteger, comment='专业:新专业id：用于和最新专业名称对齐')
    bid = db.Column(db.SmallInteger, comment='批次')
    csbscore = db.Column(db.Integer, comment='实际分数')
    csbplannum = db.Column(db.Integer, comment='计划人数')
    suid = db.Column(db.SmallInteger, server_default=db.text("'1'"), comment='科别')
    status = db.Column(TINYINT, comment='状态')
    tuitions = db.Column(db.Integer, comment='学费')
    year = db.Column(db.Integer, comment='年份')
    spcode = db.Column(db.String(250), comment='专业代码')
    zyfx = db.Column(db.String(250), comment='专业方向')
    bhzy = db.Column(db.String(250), comment='包含专业')
    tslx = db.Column(db.String(250), comment='特殊类型')
    yuce = db.Column(db.Integer, server_default=db.text("'0'"), comment='预测分数')
    rengong = db.Column(db.Integer, comment='人工修正分数')
    wu = db.Column(db.Integer, comment='物理：1、必选；2无要求')
    shi = db.Column(db.Integer, comment='历史：1、必选；2无要求')
    hua = db.Column(db.Integer, comment='化学：1、必选；2无要求')
    sheng = db.Column(db.Integer, comment='生物：1、必选；2无要求')
    di = db.Column(db.Integer, comment='地理：1、必选；2无要求')
    zheng = db.Column(db.Integer, comment='政治：1、必选；2无要求')
    fenzu = db.Column(db.Integer, comment='根据选课要求重建的分组')
    cgid = db.Column(db.Integer, comment='院校专业组ID')
    newcid = db.Column(db.Integer, comment='新院校ID对应zwh_college_groups_2024表')
    newbid = db.Column(db.Integer, comment='对应新批次：11、本科；12、专科')
    xuezhi = db.Column(db.Integer, comment='学制：对应几年制')
    spid_init = db.Column(db.SmallInteger, comment='专业原始id:存储原始专业名称')
    shuoming = db.Column(db.String(2500), comment='专业特殊说明')
    cgname = db.Column(db.String(2500), comment='分组名称')
    spname = db.Column(db.String(2500), comment='对应spid的专业名称')
    subclassid = db.Column(db.Integer, comment='专业类ID')
    weici = db.Column(db.Integer, comment='位次')
    baoyan = db.Column(db.String(255), comment='保研')
    teacher = db.Column(db.String(255), comment='教师')
    doctor = db.Column(db.String(255), comment='医生')
    official = db.Column(db.String(255), comment='公务员')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'cid': self.cid,
            'spid': self.spid,
            'bid': self.bid,
            'csbscore': self.csbscore,
            'csbplannum': self.csbplannum,
            'suid': self.suid,
            'status': self.status,
            'tuitions': self.tuitions,
            'year': self.year,
            'spcode': self.spcode,
            'zyfx': self.zyfx,
            'bhzy': self.bhzy,
            'tslx': self.tslx,
            'yuce': self.yuce,
            'rengong': self.rengong,
            'wu': self.wu,
            'shi': self.shi,
            'hua': self.hua,
            'sheng': self.sheng,
            'di': self.di,
            'zheng': self.zheng,
            'fenzu': self.fenzu,
            'cgid': self.cgid,
            'newcid': self.newcid,
            'newbid': self.newbid,
            'xuezhi': self.xuezhi,
            'spid_init': self.spid_init,
            'shuoming': self.shuoming,
            'cgname': self.cgname,
            'spname': self.spname,
            'subclassid': self.subclassid,
            'weici': self.weici,
            'baoyan': self.baoyan,
            'teacher': self.teacher,
            'doctor': self.doctor,
            'official': self.official
        }