"""
Flask 应用初始化模块
"""
from flask import Flask
from flask_cors import CORS


def create_app(config_name: str = "dev") -> Flask:
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 (dev/prod)
    
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    from app.config import config
    app.config.from_object(config[config_name])
    
    # 启用跨域支持
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册蓝图
    from app.api.v1 import api_v1
    app.register_blueprint(api_v1, url_prefix="/api/v1")
    
    return app
