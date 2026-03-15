"""
生产环境配置
"""
import os


class ProdConfig:
    """生产环境配置类"""
    
    # 调试模式
    DEBUG = False
    
    # 密钥 (生产环境必须设置)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production environment")
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT 配置
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in production environment")
    JWT_ACCESS_TOKEN_EXPIRES = 2 * 60 * 60  # 2小时
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    
    # 日志配置
    LOG_LEVEL = "INFO"
