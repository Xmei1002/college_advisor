from app.extensions import db

class CepingMbtiLeixing(db.Model):
    """MBTI类型表"""
    __tablename__ = 'ceping_mbti_leixing'
    
    id = db.Column(db.Integer, primary_key=True)
    l_id = db.Column(db.String(250), comment='类型编号')
    name = db.Column(db.String(250), comment='类型组合名称')
    xingge = db.Column(db.Text, comment='性格分析')
    youshi = db.Column(db.Text, comment='优势分析')
    lueshi = db.Column(db.Text, comment='劣势分析')
    zhiye = db.Column(db.Text, comment='职业领域')
    dianxing = db.Column(db.Text, comment='典型职业')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'l_id': self.l_id,
            'name': self.name,
            'xingge': self.xingge,
            'youshi': self.youshi,
            'lueshi': self.lueshi,
            'zhiye': self.zhiye,
            'dianxing': self.dianxing
        }