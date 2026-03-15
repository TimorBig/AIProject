"""
开发环境配置
"""
import os


class DevConfig:
    """开发环境配置类"""
    
    # 调试模式
    DEBUG = True
    
    # 密钥
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        "sqlite:///dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT 配置
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24小时
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    
    # 日志配置
    LOG_LEVEL = "DEBUG"
