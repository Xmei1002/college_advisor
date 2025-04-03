from app import create_app
from app.extensions import celery, init_celery
import app.tasks  # 导入所有任务

app = create_app()