# app/services/sms/aliyun_sms.py
from flask import current_app
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
import os
class AliyunSmsService:
    """阿里云短信服务封装类"""
    
    @classmethod
    def create_client(cls):
        """创建阿里云短信客户端"""
        # 从配置中读取敏感信息
        access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
        access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        
        # 创建配置
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        # 指定接入点
        config.endpoint = 'dysmsapi.aliyuncs.com'
        
        # 创建并返回客户端
        return Dysmsapi20170525Client(config)
    
    @classmethod
    def send_verification_code(cls, phone, code):
        """发送验证码短信
        
        Args:
            phone (str): 手机号码
            code (str): 验证码
            
        Returns:
            bool: 发送是否成功
            str: 错误信息，成功时为空
        """
        try:
            client = cls.create_client()
            
            # 从配置中读取签名和模板
            sign_name = os.getenv('ALIYUN_SMS_SIGN_NAME')
            template_code = os.getenv('ALIYUN_SMS_TEMPLATE_CODE')
            
            # 构造请求参数
            send_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=sign_name,
                template_code=template_code,
                template_param=f'{{"code":"{code}"}}'
            )
            
            # 调用API发送短信
            response = client.send_sms(send_request)
            
            # 记录发送日志
            current_app.logger.info(f"向手机号 {phone} 发送验证码: {code}, 响应: {response.body}")
            
            # 验证发送是否成功
            if response.body.code == "OK":
                return True, ""
            else:
                error_msg = f"短信发送失败: {response.body.message}"
                current_app.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"短信发送异常: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    @classmethod
    def send_notification(cls, phone, template_code, template_params):
        """发送通知类短信
        
        Args:
            phone (str): 手机号码
            template_code (str): 模板编码
            template_params (dict): 模板参数，如{"name":"张三", "time":"2023-01-01"}
            
        Returns:
            bool: 发送是否成功
            str: 错误信息，成功时为空
        """
        try:
            client = cls.create_client()
            
            # 从配置中读取签名
            sign_name = current_app.config.get('ALIYUN_SMS_SIGN_NAME', '启明星高考')
            
            # 将参数字典转为JSON字符串
            import json
            template_param = json.dumps(template_params)
            
            # 构造请求参数
            send_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=sign_name,
                template_code=template_code,
                template_param=template_param
            )
            
            # 调用API发送短信
            response = client.send_sms(send_request)
            
            # 记录发送日志
            current_app.logger.info(f"向手机号 {phone} 发送通知短信, 响应: {response.body}")
            
            # 验证发送是否成功
            if response.body.code == "OK":
                return True, ""
            else:
                error_msg = f"短信发送失败: {response.body.message}"
                current_app.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"短信发送异常: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg