"""
API v1 版本蓝图
"""
from flask import Blueprint, jsonify

api_v1 = Blueprint("api_v1", __name__)


@api_v1.route("/health", methods=["GET"])
def health_check():
    """
    健康检查接口
    
    Returns:
        JSON 响应
    """
    return jsonify({
        "code": 0,
        "message": "success",
        "data": {
            "status": "healthy",
            "version": "1.0.0"
        }
    })


@api_v1.route("/ping", methods=["GET"])
def ping():
    """
    Ping 接口
    
    Returns:
        JSON 响应
    """
    return jsonify({
        "code": 0,
        "message": "success",
        "data": "pong"
    })


# 导入其他路由模块
# from app.api.v1 import user, auth
