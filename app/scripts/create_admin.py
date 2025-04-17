#!/usr/bin/env python
# app/scripts/create_admin.py
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.core.auth.service import AuthService

def create_default_admin(username, password):
    """创建默认管理员账户"""
    app = create_app()
    with app.app_context():
        # 检查是否已存在管理员
        from app.models.user import User
        admin = User.query.filter_by(user_type=User.USER_TYPE_ADMIN).first()
        
        if admin:
            print(f"管理员账户已存在: {admin.username}")
            return
            
        try:
            admin = AuthService.create_admin(username, password)
            print(f"成功创建管理员账户: {admin.username}")
        except Exception as e:
            print(f"创建管理员账户失败: {str(e)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='创建默认管理员账户')
    parser.add_argument('--username', default='admin', help='管理员用户名')
    parser.add_argument('--password', default='admin123...', help='管理员密码')
    
    args = parser.parse_args()
    
    create_default_admin(args.username, args.password) 