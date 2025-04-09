from openai import OpenAI
import os
from .prompt import (FILTER_COLLEGE_PROMPT, ANALYZING_CATEGORY_PROMPT, 
                     ANALYZING_COLLEGE_PROMPT, ANALYZING_SPECIALTY_PROMPT,
                     ANALYZING_STRATEGY_PROMPT,ANALYZING_SNAPSHOT_PROMPT)
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
    def _call_api(cls, user_input, temperature=0.3, response_format=None):
        """处理API调用的通用方法"""
        client = cls._get_client()
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        # 构造API调用参数
        params = {
            "model": "moonshot-v1-auto",
            "messages": messages,
            "temperature": temperature,
        }
        
        # 如果提供了response_format，添加到参数中
        if response_format:
            params["response_format"] = response_format
            
        # 调用API获取响应
        completion = client.chat.completions.create(**params)
        current_app.logger.info(f"AI response: {completion.choices[0].message.content}")
        return completion.choices[0].message.content
    
    @classmethod
    def analyzing_strategy(cls, user_info, temperature=0.3):
        user_input = ANALYZING_STRATEGY_PROMPT.format(user_info=user_info)
        return cls._call_api(user_input, temperature)
    
    @classmethod
    def filter_colleges(cls, user_info, simplified_colleges_json, temperature=0.3):
        user_input = FILTER_COLLEGE_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json)
        response_format = {"type": "json_object"}  # 指定响应格式为JSON对象
        return cls._call_api(user_input, temperature, response_format)
    
    @classmethod
    def analyzing_category(cls, user_info, simplified_colleges_json, category, temperature=0.3):
        user_input = ANALYZING_CATEGORY_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json, category=category)
        return cls._call_api(user_input, temperature)
    
    @classmethod
    def analyzing_college(cls, user_info, college_json, temperature=0.3):
        user_input = ANALYZING_COLLEGE_PROMPT.format(user_info=user_info, college_json=college_json)
        return cls._call_api(user_input, temperature)
    
    @classmethod
    def analyzing_specialty(cls, user_info, specialty_json, temperature=0.3):
        user_input = ANALYZING_SPECIALTY_PROMPT.format(user_info=user_info, specialty_json=specialty_json)
        return cls._call_api(user_input, temperature)
    
    @classmethod
    def analyzing_student_snapshots(cls, current_snapshot, previous_snapshot, temperature=0.3):
        user_input = ANALYZING_SNAPSHOT_PROMPT.format(current_snapshot=current_snapshot, previous_snapshot=previous_snapshot)
        return cls._call_api(user_input, temperature)
    