from flask import jsonify

class APIResponse:
    """
    标准化API响应格式
    """
    @staticmethod
    def success(data=None, message="操作成功", code=200):
        """
        成功响应
        :param data: 响应数据
        :param message: 响应消息
        :param code: 状态码
        :return: JSON响应
        """
        response = {
            "success": True,
            "message": message,
            "code": code
        }
        
        if data is not None:
            response["data"] = data
            
        # 只返回响应数据和状态码，不调用jsonify
        return jsonify(response), code
    
    @staticmethod
    def error(message="操作失败", errors=None, code=400):
        """
        错误响应
        :param message: 错误消息
        :param errors: 错误详情
        :param code: 状态码
        :return: JSON响应
        """
        response = {
            "success": False,
            "message": message,
            "code": code
        }
        
        if errors is not None:
            response["errors"] = errors
            
        # 只返回响应数据和状态码，不调用jsonify
        return jsonify(response), code
    
    @staticmethod
    def pagination(items, total, page, per_page, message="获取成功", code=200):
        """
        分页响应
        :param items: 当前页数据
        :param total: 总数据条数
        :param page: 当前页码
        :param per_page: 每页条数
        :param message: 响应消息
        :param code: 状态码
        :return: JSON响应
        """
        response = {
            "success": True,
            "message": message,
            "code": code,
            "data": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }
        
        # 只返回响应数据和状态码，不调用jsonify
        return jsonify(response), code