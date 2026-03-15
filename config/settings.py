"""
配置管理模块
集中管理所有配置项，支持从环境变量和.env文件加载
"""
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv


# 加载.env文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class FeishuConfig:
    """飞书配置"""
    app_id: str = ""
    app_secret: str = ""
    
    # API端点
    base_url: str = "https://open.feishu.cn/open-apis"
    auth_url: str = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    message_url: str = "https://open.feishu.cn/open-apis/im/v1/messages"
    
    def __post_init__(self):
        # 从环境变量加载
        self.app_id = os.getenv("FEISHU_APP_ID", self.app_id)
        self.app_secret = os.getenv("FEISHU_APP_SECRET", self.app_secret)


@dataclass
class DoubaoConfig:
    """豆包大模型配置"""
    api_key: str = ""
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = ""
    
    # 对话参数
    max_tokens: int = 2000
    temperature: float = 0.7
    
    def __post_init__(self):
        # 从环境变量加载
        self.api_key = os.getenv("DOUBAO_API_KEY", self.api_key)
        self.base_url = os.getenv("DOUBAO_BASE_URL", self.base_url)
        self.model = os.getenv("DOUBAO_MODEL", self.model)


@dataclass
class KeywordRule:
    """关键字规则"""
    keywords: List[str]
    reply: str
    match_type: str = "contains"  # contains, exact, prefix, suffix, regex
    case_sensitive: bool = False


@dataclass
class KeywordsConfig:
    """关键字配置"""
    rules: List[KeywordRule] = field(default_factory=list)
    
    def __post_init__(self):
        # 默认关键字规则（精准匹配）
        if not self.rules:
            self.rules = [
                KeywordRule(
                    keywords=["你好"],
                    reply="你好呀！很高兴见到你，有什么可以帮助你的吗？",
                    match_type="exact"
                ),
                KeywordRule(
                    keywords=["时间"],
                    reply="当前时间是：{current_time}",
                    match_type="exact"
                ),
                KeywordRule(
                    keywords=["你是谁"],
                    reply="我是蔡徐坤 唱跳rap🏀",
                    match_type="exact"
                ),
            ]


@dataclass
class BitableConfig:
    """多维表格配置"""
    app_token: str = ""    # 多维表格App Token
    table_id: str = ""     # 数据表ID
    
    def __post_init__(self):
        self.app_token = os.getenv("BITABLE_APP_TOKEN", self.app_token)
        self.table_id = os.getenv("BITABLE_TABLE_ID", self.table_id)


@dataclass
class Settings:
    """全局配置"""
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    doubao: DoubaoConfig = field(default_factory=DoubaoConfig)
    keywords: KeywordsConfig = field(default_factory=KeywordsConfig)
    bitable: BitableConfig = field(default_factory=BitableConfig)
    
    # 日志配置
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    
    # Token刷新间隔（秒）
    token_refresh_interval: int = 3600  # 1小时
    
    def __post_init__(self):
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
        self.log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"


# 全局配置实例
settings = Settings()
