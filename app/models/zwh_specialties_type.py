from app.extensions import db

class ZwhSpecialtiesType(db.Model):
    """专业类型表"""
    __tablename__ = 'zwh_specialties_type'

    id = db.Column(db.Integer, primary_key=True)
    sptfather = db.Column(db.String(250), comment='上级专业')
    sptname = db.Column(db.String(250), comment='名称')
    sort = db.Column(db.Integer, comment='sort')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'sptfather': self.sptfather,
            'sptname': self.sptname,
            'sort': self.sort
        }