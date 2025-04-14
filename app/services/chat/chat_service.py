# app/services/chat/chat_service.py
import logging
logger = logging.getLogger(__name__)
from app.extensions import db
from app.models.conversations import Conversation
from app.models.messages import Message
from app.models.user import User
from app.services.ai.moonshot import MoonshotAI
from datetime import datetime
import json
import time
from app.models.collegePreference import CollegePreference
from app.utils.user_hash import calculate_user_data_hash
from app.services.student.student_data_service import StudentDataService
from app.models.student_volunteer_plan import StudentVolunteerPlan
class ChatService:
    """聊天服务类，处理聊天相关业务逻辑"""
    
    @classmethod
    def create_conversation(cls, student_id, planner_id, conversation_type, title='新对话'):
        """
        创建新的会话
        
        :param student_id: 学生ID
        :param planner_id: 规划师ID
        :param conversation_type: 会话类型 (changeinfo/volunteer)
        :param title: 会话标题，默认自动生成
        :return: 创建的会话对象
        """
        conversation = Conversation(
            student_id=student_id,
            planner_id=planner_id,
            conversation_type=conversation_type,
            title=title,
            is_active=True,
            last_message_time=datetime.now()
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return conversation
    
    @classmethod
    def get_conversation(cls, conversation_id):
        """
        获取会话详情
        
        :param conversation_id: 会话ID
        :return: 会话对象
        """
        return Conversation.query.get(conversation_id)
    
    @classmethod
    def get_user_conversations(cls, student_id, planner_id, conversation_type=None, page=1, per_page=20):
        """
        获取用户的会话列表
        
        :param student_id: 学生ID
        :param planner_id: 规划师ID
        :param page: 页码
        :param per_page: 每页记录数
        :return: 会话列表和分页信息
        """
        query = Conversation.query
        
        query = query.filter(Conversation.student_id == student_id, Conversation.planner_id == planner_id)
        
        if conversation_type:
            query = query.filter(Conversation.conversation_type == conversation_type)

        # 按最后消息时间倒序排列
        query = query.order_by(Conversation.last_message_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建返回结果
        conversations = pagination.items
        
        return {
            'conversations': [conv.to_dict() for conv in conversations],
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    
    @classmethod
    def archive_conversation(cls, conversation_id):
        """
        归档会话
        
        :param conversation_id: 会话ID
        :return: 更新后的会话对象
        """
        conversation = cls.get_conversation(conversation_id)
        conversation.is_archived = True
        db.session.commit()
        
        return conversation
    
    @classmethod
    def reactivate_conversation(cls, conversation_id):
        """
        重新激活已归档的会话
        
        :param conversation_id: 会话ID
        :return: 更新后的会话对象
        """
        conversation = cls.get_conversation(conversation_id)
        conversation.is_archived = False
        conversation.is_active = True
        conversation.last_message_time = datetime.now()
        db.session.commit()
        
        return conversation
    
    @classmethod
    def update_conversation_title(cls, conversation_id, title):
        """
        更新会话标题
        
        :param conversation_id: 会话ID
        :param title: 新标题
        :return: 更新后的会话对象
        """
        conversation = cls.get_conversation(conversation_id)
        conversation.title = title
        db.session.commit()
        
        return conversation
    
    @classmethod
    def add_message(cls, conversation_id, sender_id, role, content, message_type=None):
        """
        添加消息
        
        :param conversation_id: 会话ID
        :param sender_id: 发送者ID
        :param role: 角色(student/planner/ai/system)
        :param content: 消息内容
        :param message_type: 消息类型，默认为文本
        :return: 创建的消息对象
        """
        if message_type is None:
            message_type = Message.TYPE_TEXT
            
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            role=role,
            message_type=message_type,
            content=content
        )
        
        db.session.add(message)
        
        # 更新会话最后消息时间
        conversation = cls.get_conversation(conversation_id)
        conversation.last_message_time = datetime.now()
        
        db.session.commit()
        
        return message
    
    @classmethod
    def get_conversation_messages(cls, conversation_id, page=1, per_page=20):
        """
        获取会话消息记录
        
        :param conversation_id: 会话ID
        :param page: 页码
        :param per_page: 每页记录数
        :return: 消息列表和分页信息
        """
        # 验证会话存在
        cls.get_conversation(conversation_id)
        
        # 查询消息
        query = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.id.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        messages = pagination.items
        
        return {
            'messages': [msg.to_dict() for msg in messages],
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    
    @classmethod
    def get_message(cls, message_id):
        """
        获取消息详情
        
        :param message_id: 消息ID
        :return: 消息对象
        """
        return Message.query.get_or_404(message_id)
    
    @classmethod
    def get_recent_messages(cls, conversation_id, limit=20):
        """
        获取最近的消息记录（用于AI上下文）
        
        :param conversation_id: 会话ID
        :param limit: 消息数量限制
        :return: 最近的消息列表
        """
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.id.desc())\
            .limit(limit).all()
        
        # 反转列表，使其按时间顺序排列
        messages.reverse()
        return messages
    
    @classmethod
    def format_messages_for_ai(cls, messages):
        """
        将消息列表格式化为AI可用的格式
        
        :param messages: 消息列表
        :return: 格式化后的消息列表
        """
        formatted_messages = []
        
        for message in messages:
            if message.role == Message.ROLE_AI:
                role = "assistant"
            elif message.role in [Message.ROLE_STUDENT, Message.ROLE_PLANNER]:
                role = "user"
            else:  # 系统消息等
                continue
                
            formatted_messages.append({
                "role": role,
                "content": message.content if message.content.strip() else "[空消息]"
            })
        return formatted_messages
    
    @classmethod
    def process_user_message(cls, student_id, planner_id, conversation_type, sender_id, message_content, conversation_id, plan_id=None):
        """
        处理用户消息并生成AI回复(流式)
        
        :param student_id: 学生ID
        :param planner_id: 规划师ID
        :param conversation_type: 会话类型
        :param sender_id: 消息发送者ID
        :param message_content: 消息内容
        :param plan_id: 志愿方案ID(用于分析)
        :yield: AI回复内容块
        """
        try:
            # 确定发送者角色
            sender_role = Message.ROLE_PLANNER
            logger.info(f"学生ID: {student_id}, 规划师ID: {planner_id}, 会话类型: {conversation_type}, 发送者ID: {sender_id}, 消息内容: {message_content}, 角色: {sender_role}")
            task_result = None
            if conversation_id:
            # 查找或创建会话
                conversation = Conversation.query.filter_by(id = conversation_id).first() 
                if not conversation:
                    raise ValueError("会话不存在")
            else:
                from app.tasks.volunteer_tasks import generate_conversation_title_task
                conversation = cls.create_conversation(
                    student_id=student_id,
                    planner_id=planner_id,
                    conversation_type=conversation_type
                )
                task_result = generate_conversation_title_task.delay(conversation.id, message_content)
                
            # 获取最近消息作为上下文
            recent_messages = cls.get_recent_messages(conversation.id)
            formatted_history = cls.format_messages_for_ai(recent_messages)
            
            # 保存用户消息
            user_message = cls.add_message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                role=sender_role,
                content=message_content
            )
            
            # 创建AI消息占位
            ai_message = Message(
                conversation_id=conversation.id,
                role=Message.ROLE_AI,
                sender_id=0,
                message_type=Message.TYPE_TEXT,
                content=""  # 初始为空
            )
            db.session.add(ai_message)
            db.session.commit()
            
            # 准备返回元数据
            metadata = {
                "conversation_id": conversation.id,
                "message_id": ai_message.id
            }
            
            # 返回元数据
            yield json.dumps({"type": "metadata", "data": metadata})
            
            # 根据会话类型和是否有plan决定调用方式
            if conversation_type == Conversation.TYPE_VOLUNTEER:
                # 使用方案分析
                ai_stream = MoonshotAI.analyzing_plan(message_content, formatted_history, plan_id)
                
                # 处理AI流式响应
                full_content = ""
                for chunk in ai_stream:
                    if chunk:
                        full_content += chunk
                        yield json.dumps({"type": "chunk", "content": chunk})
                
                # 更新AI消息内容
                ai_message.content = full_content
                
            elif conversation_type == Conversation.TYPE_CHANGEINFO:
                # 处理修改报考信息的请求
                preference = CollegePreference.query.filter_by(student_id=student_id).first()
                if not preference:
                    yield json.dumps({"type": "error", "message": "未找到学生报考策略"})
                    return
                    
                # 将偏好信息转换为字符串
                stu_cp_str = json.dumps(preference.to_dict(send_ai=True), ensure_ascii=False)
                
                # 调用AI获取完整的JSON响应（非流式）
                ai_res_json = MoonshotAI.change_student_college_preferences(message_content, stu_cp_str)
                 
                # 解析AI返回的内容
                try:
                    json_data = json.loads(ai_res_json)
                    
                    # 处理变更
                    changes = json_data.get('changes', [])
                    if changes:
                        # 更新数据库
                        updated_preference = update_college_preferences(student_id, changes)
                        if not updated_preference:
                            yield json.dumps({"type": "error", "message": "更新报考策略失败"})
                            return
                    
                    # 获取确认消息
                    confirmation_message = json_data.get('confirmation_message', '')
                    if confirmation_message:
                        # 流式输出确认消息
                        full_content = ""
                        for char in confirmation_message:
                            chunk = char
                            full_content += chunk
                            yield json.dumps({"type": "chunk", "content": chunk})
                        
                        # 更新AI消息内容 - 只保存确认消息
                        ai_message.content = confirmation_message

                    restart_generation = json_data.get('restart_generation', False)
                    if restart_generation:
                        from app.tasks.volunteer_tasks import generate_volunteer_plan_task

                        student_data = StudentDataService.extract_college_recommendation_data(student_id)
                        # 计算当前数据哈希
                        current_hash = calculate_user_data_hash(student_data)
                        
                        # 检查是否存在最近的成功方案
                        latest_plan = StudentVolunteerPlan.query.filter_by(
                            student_id=student_id,
                            is_current=True,
                            generation_status=StudentVolunteerPlan.GENERATION_STATUS_SUCCESS
                        ).order_by(StudentVolunteerPlan.version.desc()).first()
                        message = "已为您重新生成志愿表，请在<志愿方案>中查看。"
                        # 如果存在最近方案且数据哈希相同，拒绝重新生成
                        if latest_plan and latest_plan.user_data_hash == current_hash:
                            message="用户数据未发生变化，无需重新生成志愿方案",
                        else:
                            # 启动异步任务，并传递当前数据哈希
                            task = generate_volunteer_plan_task.delay(
                                student_id=student_id,
                                planner_id=planner_id,
                                user_data_hash=current_hash
                            )
                        full_content = ""
                        for char in message:
                            chunk = char
                            full_content += chunk
                            yield json.dumps({"type": "chunk", "content": chunk})

                        ai_message.content = message

                except json.JSONDecodeError as e:
                    yield json.dumps({"type": "error", "message": "处理AI响应失败，请重试"})
                    return
                except Exception as e:
                    logger.error(f"处理报考策略更新失败: {str(e)}")
                    yield json.dumps({"type": "error", "message": "更新报考策略失败，请重试"})
                    return
            
            # 更新会话最后消息时间
            conversation.last_message_time = datetime.now()
            db.session.commit()
            
            # 新会话时，更新会话标题
            if conversation_id:
                yield json.dumps({"type": "end", "title": conversation.title})
            else:
                if task_result is not None and task_result.ready():
                    result = task_result.get()
                    title = result.get("title") if result else f"新会话-{conversation.id}"
                else:
                    title = f"新会话-{conversation.id}"
                # 发送完成信号
                yield json.dumps({"type": "end", "title": title})
            
        except Exception as e:
            # 记录错误
            logger.error(f"处理消息时出错: {str(e)}")
            
            # 返回错误信息
            yield json.dumps({"type": "error", "message": '当前AI服务不可用，请稍后再试。'})
            
            # 如果已创建AI消息，更新错误信息
            try:
                if 'ai_message' in locals() and ai_message.id:
                    ai_message.content = "Error"
                    db.session.commit()
            except:
                pass

def update_college_preferences(student_id, changes):
    """
    根据AI返回的结果更新学生报考策略
    
    :param student_id: 学生ID
    :param changes: 变更列表，每项包含field, operation和value
    :return: 更新后的偏好字典或None（失败时）
    """
    from app.models import CollegePreference
    
    try:
        preference = CollegePreference.query.filter_by(student_id=student_id).first()
        if not preference:
            return None
        
        # 处理所有变更
        for change in changes:
            field = change.get('field')
            operation = change.get('operation')
            value = change.get('value')
            
            if not hasattr(preference, field):
                continue
                
            current_value = getattr(preference, field)
            
            # 根据操作类型进行不同处理
            if operation == 'replace':
                # 完全替换字段值
                setattr(preference, field, value)
            
            elif operation == 'add' and field in ['preferred_locations', 'preferred_majors', 'preferred_schools', 'school_types']:
                # 添加到列表字段
                if current_value:
                    # 将当前值拆分为列表
                    current_list = [item.strip() for item in current_value.split(',')]
                    # 确保不重复添加
                    if value not in current_list:
                        current_list.append(value)
                    # 重新组合为字符串
                    new_value = ','.join(current_list)
                    setattr(preference, field, new_value)
                else:
                    # 如果当前字段为空
                    setattr(preference, field, value)
            
            elif operation == 'remove' and field in ['preferred_locations', 'preferred_majors', 'preferred_schools', 'school_types']:
                # 从列表字段中移除
                if current_value:
                    # 将当前值拆分为列表
                    current_list = [item.strip() for item in current_value.split(',')]
                    # 移除指定值
                    if value in current_list:
                        current_list.remove(value)
                    # 重新组合为字符串
                    new_value = ','.join(current_list)
                    setattr(preference, field, new_value)
        
        # 保存到数据库
        preference.save()
        return preference.to_dict()
    except Exception as e:
        logger.error(f"更新报考策略失败: {str(e)}")
        return None