from app.extensions import db

# 排位管理模型
class ZwhScorerank(db.Model):
    """排位管理"""
    __tablename__ = 'zwh_scorerank'
    __table_args__ = {'comment': '排位管理'}

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, comment='年份')
    scores = db.Column(db.Integer, comment='分值')
    nums = db.Column(db.Integer, comment='排位')
    suid = db.Column(db.SmallInteger, comment='科别')
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'year': self.year,
            'scores': self.scores,
            'nums': self.nums,
            'suid': self.suid
        }