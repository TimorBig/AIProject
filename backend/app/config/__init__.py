"""
配置模块初始化
"""
import os
from typing import Dict, Type
from app.config.dev import DevConfig
from app.config.prod import ProdConfig


# 配置映射
config: Dict[str, Type] = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}


def get_config_name() -> str:
    """
    根据环境变量获取配置名称
    
    Returns:
        配置名称
    """
    env = os.environ.get("FLASK_ENV", "dev")
    return env if env in config else "dev"
