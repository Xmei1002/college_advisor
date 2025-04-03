# app/tasks/test_tasks.py
from app.extensions import celery
import time

@celery.task
def test_task():
    try:
        print("测试任务开始")
        time.sleep(5)
        print("测试任务结束")
        return {"status": "success"}
    except Exception as e:
        print(f"任务执行错误: {e}")
        raise