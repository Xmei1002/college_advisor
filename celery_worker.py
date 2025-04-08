from app import create_app
from app.extensions import celery, init_celery
import app.tasks  # 导入所有任务

app = create_app()
print(f"Celery配置已完成，broker: {celery.conf.broker_url}")
