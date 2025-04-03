from openai import OpenAI
import os
from .prompt import FILTER_COLLEGE_PROMPT, ANALYZING_CATEGORY_PROMPT
from flask import current_app
class MoonshotAI:
    # 类变量
    _client = None

    @classmethod
    def _get_client(cls):
        """初始化并返回客户端"""
        if cls._client is None:
            api_key = os.getenv("MOONSHOT_API_KEY")
            cls._client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"
            )
        return cls._client

    @classmethod
    def filter_colleges(cls, user_info, simplified_colleges_json, temperature=0.3):
        """
        获取 AI 的响应（类方法）
        参数:
            user_input (str): 用户输入的问题或消息
            temperature (float): 控制输出的随机性，默认为0.3
        返回:
            str: AI 的响应内容
        """
        # 获取客户端
        client = cls._get_client()
        user_input = FILTER_COLLEGE_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json)
        # 构造消息列表
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        # 调用 API 获取响应
        completion = client.chat.completions.create(
            model="moonshot-v1-auto",
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}, # 指定响应格式为 JSON 对象
        )
        current_app.logger.info(f"AI response: {completion.choices[0].message.content}")
        # 返回响应内容
        return completion.choices[0].message.content
    
    @classmethod
    def analyzing_category(cls, user_info, simplified_colleges_json, category, temperature=0.3):
        """
        获取 AI 的响应（类方法）
        参数:
            user_input (str): 用户输入的问题或消息
            temperature (float): 控制输出的随机性，默认为0.3
        返回:
            str: AI 的响应内容
        """
        # 获取客户端
        client = cls._get_client()
        user_input = ANALYZING_CATEGORY_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json, category=category)
        # 构造消息列表
        messages = [
            {"role": "user", "content": user_input}
        ]

        # 调用 API 获取响应
        completion = client.chat.completions.create(
            model="moonshot-v1-auto",
            messages=messages,
            temperature=temperature,    
        )
        current_app.logger.info(f"AI response: {completion.choices[0].message.content}")
        # 返回响应内容
        return completion.choices[0].message.content