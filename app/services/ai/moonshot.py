from openai import OpenAI
import os
from .prompt import (FILTER_COLLEGE_PROMPT, ANALYZING_CATEGORY_PROMPT, 
                     ANALYZING_COLLEGE_PROMPT, ANALYZING_SPECIALTY_PROMPT,
                     ANALYZING_STRATEGY_PROMPT,ANALYZING_SNAPSHOT_PROMPT,CHANGE_STU_CP_PROMPT,
                     ANALYZING_PLAN_PROMPT,GENERATE_CONVERSATION_TITLE_PROMPT)
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
    def _call_api(cls, user_input, system=None, history_msg=None, temperature=0.3, response_format=None, stream=False):
        """处理API调用的通用方法"""
        client = cls._get_client()
        
        if history_msg:
            messages = history_msg
            messages.append({"role": "user", "content": user_input})
        else:
            messages = [
                {"role": "user", "content": user_input}
            ]
        
        if system:
            messages.insert(0, {"role": "system", "content": system})
        current_app.logger.info(f'AI_messages内容: {messages}')

        # 构造API调用参数
        params = {
            "model": "moonshot-v1-auto",
            "messages": messages,
            "temperature": temperature,
        }
        
        # 如果提供了response_format，添加到参数中
        if response_format:
            params["response_format"] = response_format
        
        # 设置是否使用流式输出
        params["stream"] = stream
        # 调用API获取响应
        completion = client.chat.completions.create(**params)
        
        if stream:
            # 对于流式输出，直接返回流对象，让调用者处理
            return completion
        else:
            # 非流式输出，返回完整内容
            content = completion.choices[0].message.content
            current_app.logger.info(f"AI response: {content}")
            return content
        
    @classmethod
    def analyzing_strategy(cls, user_info, temperature=0.3):
        user_input = ANALYZING_STRATEGY_PROMPT.format(user_info=user_info)
        return cls._call_api(user_input=user_input, temperature=temperature)
    
    @classmethod
    def filter_colleges(cls, user_info, simplified_colleges_json, temperature=0.3):
        user_input = FILTER_COLLEGE_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json)
        response_format = {"type": "json_object"}  # 指定响应格式为JSON对象
        return cls._call_api(user_input=user_input, temperature=temperature, response_format=response_format)
    
    @classmethod
    def analyzing_category(cls, user_info, simplified_colleges_json, category, temperature=0.3):
        user_input = ANALYZING_CATEGORY_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json, category=category)
        return cls._call_api(user_input=user_input, temperature=temperature)
    
    @classmethod
    def analyzing_college(cls, user_info, college_json, temperature=0.3):
        user_input = ANALYZING_COLLEGE_PROMPT.format(user_info=user_info, college_json=college_json)
        return cls._call_api(user_input=user_input, temperature=temperature)
        
    @classmethod
    def analyzing_specialty(cls, user_info, specialty_json, temperature=0.3):
        user_input = ANALYZING_SPECIALTY_PROMPT.format(user_info=user_info, specialty_json=specialty_json)
        return cls._call_api(user_input=user_input, temperature=temperature)
    
    @classmethod
    def analyzing_student_snapshots(cls, current_snapshot, previous_snapshot, temperature=0.3):
        user_input = ANALYZING_SNAPSHOT_PROMPT.format(current_snapshot=current_snapshot, previous_snapshot=previous_snapshot)
        return cls._call_api(user_input=user_input, temperature=temperature)
    
    @classmethod
    def change_student_college_preferences(cls, user_input, stu_cp, temperature=0.3):
        """
        修改报考策略，支持流式输出
        """
        system = CHANGE_STU_CP_PROMPT.format(stu_cp=stu_cp)
        
        # 获取流式响应
        return cls._call_api(user_input=user_input, system=system, temperature=temperature, response_format={"type": "json_object"}, stream=False)

    @classmethod
    def analyzing_plan(cls, user_input, history_msg, plan, temperature=0.3):
        system = ANALYZING_PLAN_PROMPT

        stream_response =  cls._call_api(user_input=user_input, system=system, history_msg=history_msg,  temperature=temperature, stream=True)
        # 逐块生成内容
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    
    @classmethod
    def generate_conversation_title(cls, user_message, temperature=0.3):
        """
        根据用户的第一条消息生成对话标题
        
        :param user_message: 用户的第一条消息
        :param temperature: 温度参数，控制生成的随机性
        :return: 生成的对话标题
        """
        user_input = GENERATE_CONVERSATION_TITLE_PROMPT.format(user_message=user_message)
        return cls._call_api(user_input=user_input, temperature=temperature)