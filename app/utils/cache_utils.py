from app.extensions import cache
from flask import current_app

def inspect_redis_cache(redis_cache):
    """深入检查RedisCache对象的结构"""
    print("RedisCache类型:", type(redis_cache))
    print("RedisCache属性:", dir(redis_cache))
    
    # 遍历所有属性寻找可能的Redis客户端
    for attr_name in dir(redis_cache):
        if attr_name.startswith('__'):
            continue
        try:
            attr = getattr(redis_cache, attr_name)
            attr_type = type(attr).__name__
            # 检查属性名或类型中是否包含'redis'或'client'
            if ('redis' in attr_name.lower() or 'client' in attr_name.lower() or 
                'redis' in attr_type.lower() or 'client' in attr_type.lower()):
                print(f"可能的Redis客户端: {attr_name} -> {type(attr)}")
        except:
            pass


from app.extensions import cache
from flask import current_app

def delete_old_cache_for_student(student_id, current_hash):
    """删除学生的旧缓存数据，只保留当前哈希对应的缓存"""
    try:
        # 获取Redis客户端 - 使用写客户端，因为删除是写操作
        redis_client = cache.cache._write_client
        
        # 当前缓存键
        current_key = f"flask_cache_college_stats:{student_id}:{current_hash}"
        # 匹配模式
        pattern = f"flask_cache_college_stats:{student_id}:*"
        
        # 使用Redis的scan_iter方法
        deleted_count = 0
        for key in redis_client.scan_iter(pattern):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if key_str != current_key:
                redis_client.delete(key)
                deleted_count += 1
                current_app.logger.info(f"删除旧缓存: {key_str}")
        
        if deleted_count > 0:
            current_app.logger.info(f"已清理学生{student_id}的{deleted_count}个旧缓存")
        return deleted_count
    
    except Exception as e:
        current_app.logger.error(f"清理缓存时发生错误: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return 0