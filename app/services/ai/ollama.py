import requests
import json
import time
import os
from .prompt import FILTER_COLLEGE_PROMPT
# 尝试导入 Flask 的 current_app，如果不可用则忽略
try:
    from flask import current_app
except ImportError:
    current_app = None

class OllamaAPI:
    # 类变量
    _base_url = None
    _generate_endpoint = None
    _chat_endpoint = None
    
    @classmethod
    def _initialize_endpoints(cls):
        """初始化 API 端点"""
        if cls._base_url is None:
            # 从环境变量获取基础 URL，或使用默认值
            cls._base_url = os.getenv("OLLAMA_API_BASE_URL", "http://model.henanduojing.com")
            
            # 如果 URL 中没有端口，添加默认端口
            if ":" not in cls._base_url:
                cls._base_url = f"{cls._base_url}:11434"
            
            # 设置端点
            cls._generate_endpoint = f"{cls._base_url}/api/generate"
            cls._chat_endpoint = f"{cls._base_url}/api/chat"
            
            # 日志记录
            cls._log_info(f"Ollama API 端点初始化: {cls._generate_endpoint}")

    @classmethod
    def _log_info(cls, message):
        """统一的日志记录方法"""
        if current_app and hasattr(current_app, 'logger'):
            current_app.logger.info(message)
        else:
            print(message)
            
    @classmethod
    def _log_error(cls, message):
        """统一的错误日志记录方法"""
        if current_app and hasattr(current_app, 'logger'):
            current_app.logger.error(message)
        else:
            print(f"错误: {message}")

    @classmethod
    def _call_api(cls, endpoint, payload, stream=False):
        """处理 API 调用的通用方法"""
        # 确保端点已初始化
        cls._initialize_endpoints()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 记录请求信息
        cls._log_info(f"发送请求到: {endpoint}")
        cls._log_info(f"请求内容: {json.dumps(payload, ensure_ascii=False)[:500]}...")
        cls._log_info(f"流式请求: {stream}")
        
        # 明确设置payload中的stream参数与传入的参数一致
        payload["stream"] = stream
        
        # 非流式响应处理
        if not stream:
            try:
                response = requests.post(endpoint, headers=headers, json=payload)
                cls._log_info(f"状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"API 错误 {response.status_code}: {response.text}"
                    cls._log_error(error_msg)
                    return {"error": error_msg}
                
                # 解析 JSON 响应
                try:
                    result = response.json()
                    cls._log_info(f"响应结构: {list(result.keys()) if result else 'None'}")
                    return result
                except json.JSONDecodeError as e:
                    error_msg = f"无法解析 JSON 响应: {e}"
                    cls._log_error(error_msg)
                    return {"error": error_msg, "raw": response.text}
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API 请求错误: {e}"
                cls._log_error(error_msg)
                return {"error": str(e)}
        
        # 流式响应处理
        else:
            # 创建一个函数，不要立即执行它
            def stream_generator():
                try:
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        stream=True
                    )
                    
                    if response.status_code != 200:
                        yield f"API 错误 {response.status_code}: {response.text}"
                        return
                    
                    for line in response.iter_lines():
                        if line:
                            line_text = line.decode('utf-8')
                            try:
                                data = json.loads(line_text)
                                if endpoint == cls._generate_endpoint and 'response' in data:
                                    yield data['response']
                                elif endpoint == cls._chat_endpoint and 'message' in data and 'content' in data['message']:
                                    yield data['message']['content']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                yield f"[解析错误: {line_text}]"
                except requests.exceptions.RequestException as e:
                    yield f"[请求错误: {str(e)}]"
            
            # 如果是流式处理，就返回生成器
            return stream_generator()
    
    @classmethod
    def generate(cls, prompt, model="deepseek-r1:32b", temperature=0.7, max_tokens=2048, stream=False):
        """使用 generate API 获取响应"""
        # 确保端点已初始化
        cls._initialize_endpoints()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_length": max_tokens,  # Ollama 使用 max_length 而不是 max_tokens
            "stream": stream  # 确保这个参数与传入的一致
        }
        
        # 确保 stream 参数传递正确
        return cls._call_api(cls._generate_endpoint, payload, stream=stream)
    
    @classmethod
    def chat(cls, messages, model="deepseek-r1:32b", temperature=0.7, max_tokens=2048, stream=False):
        """使用 chat API 进行对话"""
        # 确保端点已初始化
        cls._initialize_endpoints()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_length": max_tokens,  # Ollama 使用 max_length 而不是 max_tokens
            "stream": stream  # 确保这个参数与传入的一致
        }
        
        # 确保 stream 参数传递正确
        return cls._call_api(cls._chat_endpoint, payload, stream=stream)
    
    @classmethod
    def filter_colleges(cls, user_info='', simplified_colleges_json='', temperature=0.3, stream=False):
        print("开始测试 OllamaAPI.filter_colleges()")
        prompt =  FILTER_COLLEGE_PROMPT.format(user_info=user_info, college_info=simplified_colleges_json)
        # 调用 generate API，传递 stream 参数
        response = cls.generate(
            prompt=prompt,
            model="deepseek-r1:32b",
            temperature=temperature,
            max_tokens=4096,
            stream=stream
        )
        
        # 处理不同的响应类型
        if stream:
            # 流式响应 - 返回生成器
            return response
        else:
            if "error" in response:
                raise Exception(response["error"])
            else:
                # 正常响应
                result_text = response.get("response", "无响应")
                cls._log_info(f"响应内容: {result_text}")  # 打印前100个字符
                
                return result_text


# 在主程序中使用流式响应
# if __name__ == "__main__":
#     print("开始测试 OllamaAPI.filter_colleges()")
    
#     # 1. 非流式模式 - 返回完整结果
#     print("\n=== 非流式模式 ===")
#     result = OllamaAPI.filter_colleges(stream=False)
#     print("完整响应:")
#     print(result)
    
#     # 2. 流式模式 - 逐块返回结果
#     print("\n=== 流式模式 ===")
#     stream_response = OllamaAPI.filter_colleges(stream=True)
    
#     print("流式响应:")
#     full_text = ""
#     try:
#         for chunk in stream_response:
#             print(chunk, end="", flush=True)  # 立即打印每个文本块
#             full_text += chunk
#             time.sleep(0.01)  # 减缓输出速度，方便观察
#         print("\n")
        
#         # 如果需要解析JSON，可以对完整响应进行处理
#     except Exception as e:
#         print(f"\n流式处理出错: {e}")