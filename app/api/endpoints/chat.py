# app/api/endpoints/chat.py
from flask import Response, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.services.chat.chat_service import ChatService
from app.models.conversations import Conversation
from app.models.messages import Message
from app.models.user import User
from flask_smorest import Blueprint
from app.api.schemas.chat import (
    ConversationQuerySchema,
    MessageQuerySchema,
    StreamChatRequestSchema,
    UpdateTitleSchema,
    ConversationSchema,
    MessageSchema,
    ConversationDetailSchema,
    APIPaginationSchema,
    APISuccessSchema,
    APIErrorSchema,
    ChatQuestionQuerySchema
)
import random
from app.services.ai.llm_service import LLMService
from app.core.recommendation.ai_function_call import get_college_detail_by_name

chat_bp = Blueprint(
    'chat', 
    'chat',
    description='聊天相关接口',
)

@chat_bp.route('/list', methods=['GET'])
@chat_bp.arguments(ConversationQuerySchema, location="query")
@chat_bp.response(200, APIPaginationSchema)
@jwt_required()
@api_error_handler
def list_conversations(args):
    """
    获取会话列表
    
    返回当前用户参与的所有会话
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取查询参数
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    student_id = args.get('student_id')
    planner_id = args.get('planner_id')
    conversation_type = args.get('conversation_type')

    # 获取会话列表
    result = ChatService.get_user_conversations(
        student_id=student_id,
        planner_id=current_user_id,
        conversation_type=conversation_type,
        page=page,
        per_page=per_page
    )
    
    return APIResponse.pagination(
        items=result['conversations'],
        total=result['pagination']['total'],
        page=page,
        per_page=per_page,
        message="获取会话列表成功"
    )

@chat_bp.route('/<int:conversation_id>/messages', methods=['GET'])
@chat_bp.arguments(MessageQuerySchema, location="query")
@chat_bp.response(200, APIPaginationSchema)
@jwt_required()
@api_error_handler
def get_conversation_messages(args, conversation_id):
    """
    获取会话消息记录
    
    返回会话中的消息列表
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取会话
    conversation = ChatService.get_conversation(conversation_id)
    if not conversation:
        return APIResponse.error("会话不存在", code=404)
    
    # 验证权限
    if conversation.planner_id != current_user.id:
        return APIResponse.error("无权访问此会话", code=403)
    
    # 获取查询参数
    page = args.get('page', 1)
    per_page = args.get('per_page', 20)
    
    # 获取消息列表
    result = ChatService.get_conversation_messages(
        conversation_id=conversation_id,
        page=page,
        per_page=per_page
    )
    
    return APIResponse.pagination(
        items=result['messages'],
        total=result['pagination']['total'],
        page=page,
        per_page=per_page,
        message="获取消息记录成功"
    )

@chat_bp.route('/stream', methods=['POST'])
@chat_bp.arguments(StreamChatRequestSchema)
@jwt_required()
@api_error_handler
def stream_chat(args):
    """
    流式聊天接口
    
    发送消息并获取AI实时回复
    """
    # 获取请求参数
    student_id = args['student_id']
    planner_id = args['planner_id']
    conversation_type = args['conversation_type']
    message = args['message']
    conversation_id = args.get('conversation_id', False)  
    plan_id = args.get('plan_id')  # 可选参数

    # 验证会话类型
    if conversation_type not in [Conversation.TYPE_CHANGEINFO, Conversation.TYPE_VOLUNTEER, Conversation.TYPE_EXPLAININFO]:
        return APIResponse.error(f"无效的会话类型: {conversation_type}", code=400)
    
    # 权限验证
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    if current_user.id != planner_id:
        return APIResponse.error("无权进行此操作", code=403)
    
    app = current_app._get_current_object()  # 获取实际的应用对象

    def generate():
        with app.app_context():  # 使用显式应用对象
            # 处理消息并获取AI流式回复
            for response_chunk in ChatService.process_user_message(
                student_id=student_id,
                planner_id=planner_id,
                conversation_type=conversation_type,
                sender_id=current_user_id,
                message_content=message,
                conversation_id=conversation_id,
                plan_id=plan_id
            ):
                yield f"data: {response_chunk}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

# @chat_bp.route('/<int:conversation_id>/archive', methods=['POST'])
# @chat_bp.response(200, APISuccessSchema)
# @jwt_required()
# @api_error_handler
# def archive_conversation(conversation_id):
#     """
#     归档会话
    
#     将会话标记为已归档
#     """
#     current_user_id = get_jwt_identity()
    
#     # 获取会话
#     conversation = ChatService.get_conversation(conversation_id)
    
#     # 验证权限
#     if conversation.student_id != current_user_id and conversation.planner_id != current_user_id:
#         return APIResponse.error("无权操作此会话", code=403)
    
#     # 归档会话
#     updated_conversation = ChatService.archive_conversation(conversation_id)
    
#     return APIResponse.success(
#         data=updated_conversation.to_dict(),
#         message="会话已归档"
#     )

# @chat_bp.route('/<int:conversation_id>/reactivate', methods=['POST'])
# @chat_bp.response(200, APISuccessSchema)
# @jwt_required()
# @api_error_handler
# def reactivate_conversation(conversation_id):
#     """
#     重新激活会话
    
#     将已归档的会话重新激活
#     """
#     current_user_id = get_jwt_identity()
    
#     # 获取会话
#     conversation = ChatService.get_conversation(conversation_id)
    
#     # 验证权限
#     if conversation.student_id != current_user_id and conversation.planner_id != current_user_id:
#         return APIResponse.error("无权操作此会话", code=403)
    
#     # 重新激活会话
#     updated_conversation = ChatService.reactivate_conversation(conversation_id)
    
#     return APIResponse.success(
#         data=updated_conversation.to_dict(),
#         message="会话已重新激活"
#     )

@chat_bp.route('/<int:conversation_id>/title', methods=['PUT'])
@chat_bp.arguments(UpdateTitleSchema)
@chat_bp.response(200, APISuccessSchema)
@jwt_required()
@api_error_handler
def update_conversation_title(args, conversation_id):
    """
    更新会话标题
    
    修改会话的标题
    """
    current_user_id = get_jwt_identity()
    title = args['title']
    
    # 获取会话
    conversation = ChatService.get_conversation(conversation_id)
    
    # 验证权限
    if conversation.planner_id != current_user_id:
        return APIResponse.error("无权操作此会话", code=403)
    
    # 更新标题
    updated_conversation = ChatService.update_conversation_title(
        conversation_id=conversation_id,
        title=title
    )
    
    return APIResponse.success(
        data=updated_conversation.to_dict(),
        message="会话标题已更新"
    )

# 常量定义 - 可以放在文件顶部
CHANGE_STRATEGY_QUESTIONS = [
    "我想把意向城市从北京改为上海和深圳",
    "把学费范围调整为2万以内",
    "我想在意向专业中添加计算机类",
    "从意向专业中删除土木类",
    "从意向专业中删除金融学类",
    "删除所有意向城市",
    "删除所有意向专业",
    "在意向城市中添加上海",
    "学费范围调整为1-2万",
    "学费范围调整为1万以内"
]

ANALYZING_PLAN_QUESTIONS = [
    "计算机科学和软件工程这两个专业有什么区别？哪个就业前景更好？",
    "我的分数在本科线上30分，能上什么层次的大学？",
    "师范类院校的就业情况如何？是否只能当老师？",
    "医学专业学制那么长，值得报考吗？",
    "985和211大学的差距到底有多大？对就业有什么影响？",
    "现在哪些新兴专业比较有发展前景？",
    "填报志愿时应该冲稳保的比例是多少合适？",
    "我对金融和会计都感兴趣，选择哪个专业更有发展前景？",
    "跨省报考和本省报考有什么优劣势？录取难度会有区别吗？"
    "艺术类院校的就业情况如何？毕业后能从事哪些工作？",
    "理工科和文科哪个专业更有发展前景？",
    "现在计算机专业就业前景如何？",
    "什么是双非院校？它们和985、211相比有什么差距？"
]

# 添加到已有的chat_bp蓝图
@chat_bp.route('/questions', methods=['GET'])
@chat_bp.arguments(ChatQuestionQuerySchema, location="query")
@chat_bp.response(200)
@jwt_required()
@api_error_handler
def get_predefined_questions(args):
    """
    获取预定义的问题列表
    
    返回针对不同场景的预设问题，帮助用户快速提问
    """
    # 获取请求参数
    question_type = args.get('type', 'volunteer')
    count = 3
    if question_type == "changeinfo":
        questions = [{'id': i+1, 'content': q, 'type': 'change_strategy'} 
                    for i, q in enumerate(CHANGE_STRATEGY_QUESTIONS)]
    elif question_type == "volunteer":
        questions = [{'id': i+1, 'content': q, 'type': 'volunteer'} 
                    for i, q in enumerate(ANALYZING_PLAN_QUESTIONS)]
    questions = random.sample(questions, count)
    return APIResponse.success(
        data={'questions': questions},
        message="获取预设问题成功"
    )

@chat_bp.route('/<int:conversation_id>/title', methods=['GET'])
@chat_bp.response(200, APISuccessSchema)
@jwt_required()
@api_error_handler
def get_conversation_title(conversation_id):
    """
    获取会话标题
    
    根据会话ID获取会话的标题信息
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    is_planner = current_user.user_type == User.USER_TYPE_PLANNER
    if not is_planner:
        return APIResponse.error("无权限访问该接口", code=403)
    
    # 获取会话
    conversation = ChatService.get_conversation(conversation_id)
    if not conversation:
        return APIResponse.error("会话不存在", code=404)
    
    # 验证权限
    if conversation.planner_id != current_user.id:
        return APIResponse.error("无权访问此会话", code=403)
    
    # 返回会话标题
    return APIResponse.success(
        data={"id": conversation.id, "title": conversation.title},
        message="获取会话标题成功"
    )


@chat_bp.route('/test', methods=['POST'])
@jwt_required()
@api_error_handler
def chat_test():
    input = request.json.get('input')
    res = LLMService.kimi_tools(input)
    # res = get_college_detail_by_name('郑州大学')
    return APIResponse.success(
        data=res,
        message="成功"
    )