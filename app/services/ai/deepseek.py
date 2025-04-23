from openai import OpenAI
import os
from app.models.prompt_template import PromptTemplate
from flask import current_app
from .prompt import (
    FILTER_COLLEGE_PROMPT,
    ANALYZING_SPECIALTY_PROMPT,
    ANALYZING_STRATEGY_PROMPT,
    ANALYZING_SNAPSHOT_PROMPT,
    CHANGE_STU_CP_PROMPT,
    COMMON_PROMPT,
    GENERATE_CONVERSATION_TITLE_PROMPT,
    ANALYZING_EXPLAIN_INFO_PROMPT,
)

class DeepSeekAI:
    # 类变量
    _client = None

    @classmethod
    def _get_client(cls):
        """初始化并返回客户端"""
        if cls._client is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            cls._client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        return cls._client
    
    @classmethod
    def _get_prompt_by_type(cls, prompt_type):
        """从数据库获取提示词模板"""
        template = PromptTemplate.get_prompt_by_type(prompt_type)
        if template:
            return template.content
        # 如果没有找到模板，记录错误并返回空字符串
        current_app.logger.error(f"未找到类型为 {prompt_type} 的提示词模板")
        return ""

    @classmethod
    def _call_api(
        cls,
        user_input,
        system=None,
        history_msg=None,
        temperature=1.1,
        response_format=None,
        stream=False,
    ):
        """处理API调用的通用方法"""
        client = cls._get_client()

        if history_msg:
            messages = history_msg
            messages.append({"role": "user", "content": user_input})
        else:
            messages = [{"role": "user", "content": user_input}]

        if system:
            messages.insert(0, {"role": "system", "content": system})
        current_app.logger.info(f"AI_messages内容: {messages}")

        # 构造API调用参数
        params = {
            "model": "deepseek-chat",
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
    def analyzing_strategy(cls, user_info):
        user_input = ANALYZING_STRATEGY_PROMPT.format(user_info=user_info)
        return cls._call_api(user_input=user_input)

    @classmethod
    def filter_colleges(cls, user_info, simplified_colleges_json):
        system = FILTER_COLLEGE_PROMPT
        user_input = f"""这是我的个人档案：
            ```
            {user_info}
            ```
            这是我的备选院校信息：
            ```
            {simplified_colleges_json}
            ```"""
        response_format = {"type": "json_object"}  # 指定响应格式为JSON对象
        return cls._call_api(
            user_input=user_input,
            system=system,
            response_format=response_format,
        )

    @classmethod
    def analyzing_full_plan(cls, user_info, volunteer_plan):
        """整体志愿方案解读"""
        system = cls._get_prompt_by_type(PromptTemplate.TYPE_ANALYZING_FULL_PLAN)
        user_input = f"""我的个人档案如下：
            {user_info}
            我的完整志愿方案如下：
            {volunteer_plan}
        """
        return cls._call_api(user_input=user_input, system=system)

    @classmethod
    def analyzing_category(
        cls, user_info, simplified_colleges_json, category
    ):
        """分层志愿解读"""
        system = cls._get_prompt_by_type(PromptTemplate.TYPE_ANALYZING_CATEGORY)
        user_input = f"""请对我的【{category}】进行全面而专业的解读分析。当前需要解读的是：【{category}】

            我的个人档案如下：
            ```
            {user_info}
            ```
            我的【{category}】包含以下院校和专业：
            ```
            {simplified_colleges_json}
            ```"""
        return cls._call_api(user_input=user_input, system=system)

    @classmethod
    def analyzing_college(cls, user_info, college_json):
        """院校分析"""
        system = cls._get_prompt_by_type(PromptTemplate.TYPE_ANALYZING_COLLEGE)
        user_input = f"""
            ## 学生信息
            {user_info}
            ## 院校信息
            {college_json}
            """
        return cls._call_api(user_input=user_input, system=system)

    @classmethod
    def analyzing_specialty(cls, user_info, specialty_json):
        user_input = ANALYZING_SPECIALTY_PROMPT.format(
            user_info=user_info, specialty_json=specialty_json
        )
        return cls._call_api(user_input=user_input)

    @classmethod
    def analyzing_student_snapshots(
        cls, current_snapshot, previous_snapshot
    ):
        user_input = ANALYZING_SNAPSHOT_PROMPT.format(
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot
        )
        return cls._call_api(user_input=user_input)

    @classmethod
    def change_student_college_preferences(cls, user_input, stu_cp):
        """
        修改报考策略，支持流式输出
        """
        system = CHANGE_STU_CP_PROMPT.format(stu_cp=stu_cp)
        # 获取流式响应
        return cls._call_api(
            user_input=user_input,
            system=system,
            response_format={"type": "json_object"},
            stream=False,
        )

    @classmethod
    def analyzing_plan(cls, user_input, history_msg, plan):
        system = COMMON_PROMPT
        stream_response = cls._call_api(
            user_input=user_input,
            system=system,
            history_msg=history_msg,
            stream=True,
        )
        # 逐块生成内容
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            # 获取生成的块
            if delta.content:
                yield delta.content

    @classmethod
    def analyzing_explain_info(cls, user_input, history_msg):
        system = ANALYZING_EXPLAIN_INFO_PROMPT
        stream_response = cls._call_api(
            user_input=user_input,
            system=system,
            history_msg=history_msg,
            stream=True,
        )
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            # 获取生成的块
            if delta.content:
                yield delta.content

    @classmethod
    def generate_conversation_title(cls, user_message):
        """
        根据用户的第一条消息生成对话标题

        :param user_message: 用户的第一条消息
        :return: 生成的对话标题
        """
        user_input = GENERATE_CONVERSATION_TITLE_PROMPT.format(
            user_message=user_message
        )
        return cls._call_api(user_input=user_input)
