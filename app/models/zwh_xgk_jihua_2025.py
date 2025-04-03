from app.extensions import db

# 计划2025模型
class ZwhXgkJihua2025(db.Model):
    """计划2025数据表"""
    __tablename__ = 'zwh_xgk_jihua_2025'

    id = db.Column(db.Integer, primary_key=True)
    json_data = db.Column(db.TEXT)
    fsx_id = db.Column(db.Integer, server_default=db.text("'0'"))
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'json_data': self.json_data,
            'fsx_id': self.fsx_id
        }