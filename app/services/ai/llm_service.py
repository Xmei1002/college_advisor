# app/services/ai/llm_service.py
import os
import importlib
from flask import current_app
from app.models.prompt_template import PromptTemplate
from app.models.llm_configuration import LLMConfiguration
from app.services.ai.prompt import (
    ANALYZING_STRATEGY_PROMPT,
    ANALYZING_PLAN_PROMPT,
    CHANGE_STU_CP_PROMPT,
    ANALYZING_SNAPSHOT_PROMPT,
    ANALYZING_SPECIALTY_PROMPT,
    FILTER_COLLEGE_PROMPT,
    GENERATE_CONVERSATION_TITLE_PROMPT,
    ANALYZING_EXPLAIN_INFO_PROMPT,
)
import json
from app.core.recommendation.ai_function_call import get_college_detail_by_name

class LLMService:
    """统一的大语言模型服务类"""

    # 客户端缓存
    _clients = {}

    # 当前活跃的提供者名称
    _active_provider = None
    _last_check_time = None
    tool_map = {
        "get_college_detail_by_name": get_college_detail_by_name,
    }
    tools = [
        {
            "type": "function", 
            "function": { 
                "name": "get_college_detail_by_name",  
                "description": """ 
                    获取指定高校的详细信息。
			""", 
                "parameters": {  # 使用 parameters 字段来定义函数接收的参数
                    "type": "object",  # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                    "required": [
                        "school_full_name"
                    ],  # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                    "properties": {  # properties 中是具体的参数定义，你可以定义多个参数
                        "school_full_name": {  # 在这里，key 是参数名称，value 是参数的具体定义
                            "type": "string",  # 使用 type 定义参数类型
                            "description": """
							用户想要查询的高校全称。
						""",  # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                        }
                    },
                },
            },
        }
    ]
    # 支持的提供者配置
    PROVIDERS = {
        "moonshot": {
            "api_env_key": "MOONSHOT_API_KEY",
            "client_class": "openai.OpenAI",
            "base_url": "https://api.moonshot.cn/v1",
            "model_name": "moonshot-v1-auto",
        },
        "deepseek": {
            "api_env_key": "DEEPSEEK_API_KEY",
            "client_class": "openai.OpenAI",
            "base_url": "https://api.deepseek.com",
            "model_name": "deepseek-chat",
        },
        "zhipu": {
            "api_env_key": "ZHIPU_API_KEY",
            "client_class": "zhipuai.ZhipuAI",
            "base_url": None,  # zhipuai客户端不需要base_url
            "model_name": "GLM-4-Air-250414",
        },
    }

    @classmethod
    def get_active_provider(cls):
        """获取当前活跃的提供者名称"""

        try:
            # 从数据库获取当前激活的配置
            config = LLMConfiguration.query.filter_by(is_active=True).first()
            provider_name = config.provider if config else "moonshot"

            # 检查提供者是否受支持
            if provider_name not in cls.PROVIDERS:
                current_app.logger.warning(
                    f"不支持的提供者: {provider_name}，使用默认提供者moonshot"
                )
                provider_name = "moonshot"

            # 更新缓存
            cls._active_provider = provider_name

            return provider_name
        except Exception as e:
            current_app.logger.error(f"获取活跃提供者时出错: {str(e)}")
            return "moonshot"  # 默认使用moonshot

    @classmethod
    def _get_client(cls, provider_name=None):
        """获取或创建对应提供者的客户端"""
        if not provider_name:
            provider_name = cls.get_active_provider()

        # 如果客户端已经创建，直接返回
        if provider_name in cls._clients:
            return cls._clients[provider_name]

        try:
            provider_config = cls.PROVIDERS[provider_name]
            api_key = os.getenv(provider_config["api_env_key"])

            # 动态导入和实例化客户端类
            module_path, class_name = provider_config["client_class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            client_class = getattr(module, class_name)

            # 创建客户端实例
            if provider_config["base_url"]:
                client = client_class(
                    api_key=api_key, base_url=provider_config["base_url"]
                )
            else:
                client = client_class(api_key=api_key)

            # 缓存客户端
            cls._clients[provider_name] = client
            return client
        except Exception as e:
            current_app.logger.error(f"创建{provider_name}客户端时出错: {str(e)}")
            raise

    @classmethod
    def _get_prompt_by_type(cls, prompt_type):
        """从数据库获取提示词模板"""
        template = PromptTemplate.get_prompt_by_type(prompt_type)
        if template:
            return template.content
        current_app.logger.error(f"未找到类型为 {prompt_type} 的提示词模板")
        return ""

    @classmethod
    def _call_api(
        cls,
        user_input=None,
        system=None,
        history_msg=None,
        tools=None,
        temperature=0.75,
        response_format=None,
        stream=False,
        provider_name=None,
        tools_messages=None
    ):
        """处理API调用的通用方法"""
        if not provider_name:
            provider_name = cls.get_active_provider()

        client = cls._get_client(provider_name)
        provider_config = cls.PROVIDERS[provider_name]
        if tools_messages:
            messages = tools_messages

        else:
            if history_msg:
                messages = history_msg.copy()  # 创建副本以避免修改原始数据
                messages.append({"role": "user", "content": user_input})
            else:
                messages = [{"role": "user", "content": user_input}]

            if system:
                messages.insert(0, {"role": "system", "content": system})

        current_app.logger.info(f"当前AI大模型为: {provider_name}")
        current_app.logger.info(f"AI_messages内容: {messages}")

        # 构造API调用参数
        params = {
            "model": provider_config["model_name"],
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if tools:
            params["tools"] = tools
        
        # 如果提供了response_format，添加到参数中
        if response_format:
            params["response_format"] = response_format

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

    # 所有AI方法实现
    @classmethod
    def analyzing_strategy(cls, user_info, **kwargs):
        """分析策略"""
        user_input = ANALYZING_STRATEGY_PROMPT.format(user_info=user_info)
        return cls._call_api(user_input=user_input, **kwargs)

    @classmethod
    def filter_colleges(cls, user_info, simplified_colleges_json, **kwargs):
        """筛选院校"""
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
            **kwargs,
        )

    @classmethod
    def analyzing_full_plan(cls, user_info, volunteer_plan, **kwargs):
        """整体志愿方案解读"""
        system = cls._get_prompt_by_type(PromptTemplate.TYPE_ANALYZING_FULL_PLAN)
        user_input = f"""我的个人档案如下：
            {user_info}
            我的完整志愿方案如下：
            {volunteer_plan}
        """
        return cls._call_api(user_input=user_input, system=system, **kwargs)

    @classmethod
    def analyzing_category(
        cls, user_info, simplified_colleges_json, category, **kwargs
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
        return cls._call_api(user_input=user_input, system=system, **kwargs)

    @classmethod
    def analyzing_college(cls, user_info, college_json, **kwargs):
        """院校分析"""
        system = cls._get_prompt_by_type(PromptTemplate.TYPE_ANALYZING_COLLEGE)
        user_input = f"""
            ## 学生信息
            {user_info}
            ## 院校信息
            {college_json}
            """
        return cls._call_api(user_input=user_input, system=system, **kwargs)

    @classmethod
    def analyzing_specialty(cls, user_info, specialty_json, **kwargs):
        """专业分析"""
        user_input = ANALYZING_SPECIALTY_PROMPT.format(
            user_info=user_info, specialty_json=specialty_json
        )
        return cls._call_api(user_input=user_input, **kwargs)

    @classmethod
    def analyzing_student_snapshots(cls, current_snapshot, previous_snapshot, **kwargs):
        """分析学生快照"""
        user_input = ANALYZING_SNAPSHOT_PROMPT.format(
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
        )
        return cls._call_api(user_input=user_input, **kwargs)

    @classmethod
    def change_student_college_preferences(cls, user_input, stu_cp, **kwargs):
        """修改报考策略"""
        system = CHANGE_STU_CP_PROMPT.format(stu_cp=stu_cp)
        kwargs["response_format"] = {"type": "json_object"}
        kwargs["stream"] = False
        return cls._call_api(user_input=user_input, system=system, **kwargs)

    @classmethod
    def analyzing_plan(cls, user_input, history_msg, **kwargs):
        """分析志愿方案"""
        system = ANALYZING_PLAN_PROMPT
        kwargs["stream"] = True
        stream_response = cls._call_api(
            user_input=user_input, system=system, history_msg=history_msg, **kwargs
        )
        # 逐块生成内容
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            # 获取生成的块
            if delta.content:
                yield delta.content

    @classmethod
    def analyzing_explain_info(cls, user_input, history_msg, **kwargs):
        """解释信息"""
        system = ANALYZING_EXPLAIN_INFO_PROMPT
        kwargs["stream"] = True
        stream_response = cls._call_api(
            user_input=user_input, system=system, history_msg=history_msg, **kwargs
        )
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            # 获取生成的块
            if delta.content:
                yield delta.content

    @classmethod
    def generate_conversation_title(cls, user_message, **kwargs):
        """生成对话标题"""
        user_input = GENERATE_CONVERSATION_TITLE_PROMPT.format(
            user_message=user_message
        )
        return cls._call_api(user_input=user_input, **kwargs)

    @classmethod
    def kimi_tools(cls, user_input, history_msg, **kwargs):
        """kimi工具"""
        tools = cls.tools
        kwargs["stream"] = True
        res = cls._call_api(user_input=user_input, tools=tools, history_msg=history_msg, provider_name='moonshot', **kwargs)
        
        # 用于跟踪是否已触发工具调用
        has_tool_call = False
        tool_call_info = None
        accumulated_arguments = ""
        
        # 遍历流式响应
        for chunk in res:
            delta = chunk.choices[0].delta
            
            # 检查是否有工具调用
            if delta.tool_calls:
                # 标记已触发工具调用
                has_tool_call = True
                
                # 收集工具调用信息
                for tool_call_delta in delta.tool_calls:
                    # 如果是第一次收到工具调用信息，保存ID和名称
                    if tool_call_delta.id and not tool_call_info:
                        tool_call_info = {
                            "id": tool_call_delta.id,
                            "name": tool_call_delta.function.name if tool_call_delta.function else None,
                            "arguments": ""
                        }
                    
                    # 累积参数信息
                    if tool_call_delta.function and tool_call_delta.function.arguments:
                        accumulated_arguments += tool_call_delta.function.arguments
            
            # 如果有普通内容且未触发工具调用，直接流式返回
            elif delta.content and not has_tool_call:
                yield delta.content
        
        # 如果已触发工具调用，处理工具调用并返回结果
        if has_tool_call and tool_call_info:
            current_app.logger.info(f"触发工具调用: {tool_call_info['name']}，参数: {accumulated_arguments}")
            # 解析完整的参数
            try:
                tool_call_arguments = json.loads(accumulated_arguments)
                
                # 执行工具函数
                tool_call_name = tool_call_info["name"]
                tool_function = cls.tool_map[tool_call_name]
                tool_result = tool_function(tool_call_arguments)
                # current_app.logger.info(f"执行工具 {tool_call_name}，参数为 {tool_call_arguments}，结果为 {tool_result}")
                
                # 构建工具消息
                tools_messages = [
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call_info["id"],
                                "function": {
                                    "name": tool_call_name,
                                    "arguments": accumulated_arguments
                                },
                                "type": "function"
                            }
                        ]
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_info["id"],
                        "name": tool_call_name,
                        "content": json.dumps(tool_result)
                    }
                ]
                history_msg.append({"role": "user", "content": user_input})
                tools_messages = history_msg + tools_messages
                # 发送第二次请求获取最终响应
                kwargs['stream'] = True
                finally_res = cls._call_api(tools_messages=tools_messages, **kwargs)
                
                # 流式返回最终响应
                for chunk in finally_res:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
            except json.JSONDecodeError as e:
                # 如果JSON解析失败，返回错误信息
                error_msg = f"工具调用参数解析失败: {str(e)}"
                current_app.logger.error(error_msg)
                yield error_msg