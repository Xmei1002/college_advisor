import hashlib
import json

def calculate_user_data_hash(student_data):
    """
    计算用户数据的哈希值
    
    :param student_data: 学生数据字典
    :return: 哈希值字符串
    """
    # 确保数据是稳定排序的
    serialized = json.dumps(student_data, sort_keys=True)
    # 计算SHA256哈希
    hash_obj = hashlib.sha256(serialized.encode('utf-8'))
    return hash_obj.hexdigest()