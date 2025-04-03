from app.extensions import db

class ZwhAreas(db.Model):
    """地区地域表"""
    __tablename__ = 'zwh_areas'
    __table_args__ = (
        db.Index('idx_shudi_aid', 'aid'),
    )
    
    aid = db.Column(db.Integer, primary_key=True, comment='编号')
    aname = db.Column(db.String(250), comment='名称')
    afather = db.Column(db.Integer, comment='上级ID')
    pid = db.Column(db.SmallInteger, comment='类别')
    sort = db.Column(db.Integer, comment='排序')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'aid': self.aid,
            'aname': self.aname,
            'afather': self.afather,
            'pid': self.pid,
            'sort': self.sort,
        }