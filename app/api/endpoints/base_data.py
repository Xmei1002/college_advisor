from flask import request
from flask_smorest import Blueprint
from app.utils.response import APIResponse
from app.utils.decorators import api_error_handler
from app.models.zwh_specialties_type import ZwhSpecialtiesType
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_xgk_yuanxiao_2025 import ZwhXgkYuanxiao2025
from flask_jwt_extended import jwt_required, get_jwt_identity

def get_pid_name(pid):
    """
    根据pid获取对应的分组名称
    """
    pid_names = {
        1: "一线地区",
        2: "二线地区",
        3: "三线地区",
        4: "四线地区",
        5: "五线地区",
        # 可以根据实际需要添加更多分组
    }
    
    return pid_names.get(pid, f"{pid}线地区")

# 创建基础数据蓝图
base_data_bp = Blueprint(
    'base_data', 
    'base_data',
    description='基础数据查询接口',
)

@base_data_bp.route('/specialty_type', methods=['GET'])
@api_error_handler
def get_specialty_types():
    """
    获取专业类别数据
    
    如果提供keyword参数，则直接返回匹配的专业列表
    否则返回完整的专业类别层级结构，用于前端实现二级联动
    """
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    
    # 如果有关键词，直接进行模糊查询
    if keyword:
        # 直接查询名称匹配的专业
        specialties = ZwhSpecialtiesType.query.filter(
            ZwhSpecialtiesType.sptname.like(f'%{keyword}%')
        ).order_by(ZwhSpecialtiesType.sort).all()
        
        # 转换为字典列表
        result = [item.to_dict() for item in specialties]
        
        return APIResponse.success(
            data=result,
            message="获取专业类别成功"
        )
    
    # 如果没有关键词，返回层级结构
    # 查询所有专业类别
    all_types = ZwhSpecialtiesType.query.order_by(ZwhSpecialtiesType.sort).all()
    
    # 按照父子关系组织数据
    result = []
    
    # 先找出所有顶级类别（sptfather = '0'），使用字符串比较
    parent_types = [t for t in all_types if t.sptfather == '0']
    
    # 为每个顶级类别添加子类别
    for parent in parent_types:
        parent_dict = parent.to_dict()
        parent_dict['children'] = []
        
        # 查找该父类下的所有子类，使用字符串比较
        for child in all_types:
            if child.sptfather == str(parent.id):  # 将parent.id转为字符串再比较
                parent_dict['children'].append(child.to_dict())
        
        result.append(parent_dict)
    
    return APIResponse.success(
        data=result,
        message="获取专业类别成功"
    )

@base_data_bp.route('/area', methods=['GET'])
@api_error_handler
def get_areas():
    """
    获取地区数据
    
    如果提供keyword参数，则直接返回匹配的地区列表
    否则返回按pid分组的省级地区数据，用于前端实现二级联动
    """
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    
    # 如果有关键词，直接进行模糊查询
    if keyword:
        # 直接查询名称匹配的省级地区
        areas = ZwhAreas.query.filter(
            ZwhAreas.aname.like(f'%{keyword}%')
        ).filter(
            ZwhAreas.aname != '1'
        ).filter(
            ZwhAreas.afather == 1  # 添加这个条件，只查询省级地区
        ).order_by(ZwhAreas.sort, ZwhAreas.aid).all()
        
        # 转换为字典列表
        result = [area.to_dict() for area in areas]
        
        return APIResponse.success(
            data=result,
            message="获取地区数据成功"
        )
    
    # 如果没有关键词，返回按pid分组的结构
    # 查询afather为1的省级地区
    areas = ZwhAreas.query.filter_by(afather=1).filter(
        ZwhAreas.aname != '1'
    ).order_by(ZwhAreas.sort, ZwhAreas.aid).all()
    
    # 按pid分组
    grouped_areas = {}
    
    for area in areas:
        pid = area.pid
        
        # 如果pid不在分组字典中，初始化一个新列表
        if pid not in grouped_areas:
            grouped_areas[pid] = []
        
        # 将地区添加到对应的pid分组中
        grouped_areas[pid].append(area.to_dict())
    
    # 转换为前端友好的格式
    result = []

    # 按pid升序排列
    for pid in sorted(grouped_areas.keys()):
        pid_group = {
            'pid': pid,
            'group_name': get_pid_name(pid),  # 获取pid对应的分组名称
            'areas': grouped_areas[pid]
        }
        result.append(pid_group)
    
    return APIResponse.success(
        data=result,
        message="获取地区数据成功"
    )

@base_data_bp.route('/college', methods=['GET'])
@api_error_handler
def get_colleges():
    """
    获取院校名称数据
    
    返回院校ID和名称列表，支持按名称模糊查询
    """
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = ZwhXgkYuanxiao2025.query.filter_by(status=1)  # 只查询状态正常的院校
    
    # 如果有关键词，添加模糊查询条件
    if keyword:
        query = query.filter(ZwhXgkYuanxiao2025.cname.like(f'%{keyword}%'))
    
    # 按排序字段排序，热门院校靠前
    query = query.order_by(ZwhXgkYuanxiao2025.sort, ZwhXgkYuanxiao2025.cid)
    
    # 只选择需要的字段
    colleges = query.all()
    
    # 只返回id和名称
    result = [{'id': college.cid, 'name': college.cname} for college in colleges]
    
    return APIResponse.success(
        data=result,
        message="获取院校名称成功"
    )