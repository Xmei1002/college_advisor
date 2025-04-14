from openai import OpenAI
import os
from .prompt import (FILTER_COLLEGE_PROMPT, ANALYZING_CATEGORY_PROMPT, 
                     ANALYZING_COLLEGE_PROMPT, ANALYZING_SPECIALTY_PROMPT,
                     ANALYZING_STRATEGY_PROMPT,ANALYZING_SNAPSHOT_PROMPT,CHANGE_STU_CP_PROMPT,
                     ANALYZING_PLAN_PROMPT,GENERATE_CONVERSATION_TITLE_PROMPT)
from flask import current_app
import httpx
from pathlib import Path

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
    def upload_files(cls, files, cache_tag):
        """
        upload_files 会将传入的文件（路径）全部通过文件上传接口 '/v1/files' 上传，并获取上传后的
        文件内容生成文件 messages。每个文件会是一个独立的 message，这些 message 的 role 均为
        system，Kimi 大模型会正确识别这些 system messages 中的文件内容。
    
        如果你设置了 cache_tag 参数，那么 upload_files 还会将你上传的文件内容存入 Context Cache
        上下文缓存中，后续你就可以使用这个 Cache 来对文件内容进行提问。当你指定了 cache_tag 的值时，
        upload_files 会生成一个 role 为 cache 的 message，通过这个 message，你可以引用已被缓存
        的文件内容，这样就不必每次调用 `/v1/chat/completions` 接口时都要把文件内容再传输一遍。
        """
        client = cls._get_client()
        messages = []
        # 对每个文件路径，我们都会上传文件并抽取文件内容，最后生成一个 role 为 system 的 message，并加入
        # 到最终返回的 messages 列表中。
        for file in files:
            file_object = client.files.create(file=Path(file), purpose="file-extract")
            file_content = client.files.content(file_id=file_object.id).text
            messages.append({
                "role": "system",
                "content": file_content,
            })
    
        if cache_tag:
            # 当启用缓存（即 cache_tag 有值时），我们通过 HTTP 接口创建缓存，缓存的内容则是前文中通过文件上传
            # 和抽取接口生成的 messages 内容，我们为这些缓存设置一个默认的有效期 300 秒（通过 ttl 字段），并
            # 为这个缓存打上标记，标记值为 cache_tag（通过 tags 字段）。
            r = httpx.post(f"{client.base_url}caching",
                        headers={
                            "Authorization": f"Bearer {client.api_key}",
                        },
                        json={
                            "model": "moonshot-v1",
                            "messages": messages,
                            "ttl": 300,
                            "tags": [cache_tag],
                        })
    
            if r.status_code != 200:
                raise Exception(r.text)
    
            # 创建缓存成功后，我们不再需要将文件抽取后的内容原封不动地加入 messages 中，取而代之的是，我们可以设置一个
            # role 为 cache 的消息来引用我们已缓存的文件内容，只需要在 content 中指定我们给 Cache 设定的 tag 即可，
            # 这样可以有效减少网络传输的开销，即使是多个文件内容，也只需要添加一条 message，保持 messages 列表的清爽感。
            return [{
                "role": "cache",
                "content": f"tag={cache_tag};reset_ttl=300",
            }]
        else:
            return messages

    @classmethod
    def get_cache_info(cls, cache_id):
        r = httpx.get(f"https://api.moonshot.cn/v1/caching/{cache_id}",
            headers={
                "Authorization": f"Bearer sk-yGvlDJjVVGKfsdgELB4mGYDzEkqwWIR7OPZJF319jX7HCE1S",
            })
        # print("cache_json", r.json())
        return r.json().get("status")

    @classmethod
    def _call_api(cls, user_input, system=None, history_msg=None, cache_message=None, temperature=0.3, response_format=None, stream=False):
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

        if cache_message:
            messages.insert(0, cache_message)
            
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
        cache_id = "cache-ezycc5doc6di11ghppf1"
        cache_status = cls.get_cache_info(cache_id)
        # 获取缓存信息
        if cache_status and cache_status == "ready":
            # 如果缓存状态为ready
            print("cache ready")
            # 打印缓存已准备
            cache_message = {"role": "cache", "content": f"cache_id={cache_id}"}
            # 定义缓存消息
        else:
            # 如果缓存状态不为ready
            print("cache not ready, reset!")
            # 打印缓存未准备，重置
            cache_message = {"role": "cache", "content": f"cache_id={cache_id};reset_ttl=100"}
        stream_response =  cls._call_api(user_input=user_input, system=system, cache_message=cache_message, history_msg=history_msg,  temperature=temperature, stream=True)
        # 逐块生成内容
        for chunk in stream_response:
            delta = chunk.choices[0].delta
            # 获取生成的块
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