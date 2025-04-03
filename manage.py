import os
from flask_migrate import Migrate
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
cli = FlaskGroup(app)

@cli.command('create_db')
def create_db():
    """创建数据库表"""
    db.create_all()
    print('数据库表已创建')

@cli.command('celery_worker')
def celery_worker():
    """启动Celery worker"""
    os.system('celery -A celery.celery worker --loglevel=info')

if __name__ == '__main__':
    cli()
