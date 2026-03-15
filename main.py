"""
飞书智能助理 - 主入口
启动飞书长连接监听，处理用户消息
"""
import signal
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from core.auth import FeishuAuth
from core.event_handler import FeishuEventHandler
from services.intent_service import IntentService
from utils.logger import setup_logger, get_logger, log


def check_config():
    """
    检查配置是否完整
    """
    method_name = "check_config"
    
    errors = []
    
    # 检查飞书配置
    if not settings.feishu.app_id:
        errors.append("FEISHU_APP_ID 未配置")
    if not settings.feishu.app_secret:
        errors.append("FEISHU_APP_SECRET 未配置")
    
    # 检查豆包配置（警告级别）
    if not settings.doubao.api_key:
        log.warning(method_name, "DOUBAO_API_KEY 未配置，AI对话功能将不可用")
    
    # 检查多维表格配置（警告级别）
    if not settings.bitable.app_token:
        log.warning(method_name, "BITABLE_APP_TOKEN 未配置，多维表格功能将不可用")
    if not settings.bitable.table_id:
        log.warning(method_name, "BITABLE_TABLE_ID 未配置，多维表格功能将不可用")
    
    if errors:
        for error in errors:
            log.error(method_name, error)
        return False
    
    return True


def main():
    """
    主函数
    """
    method_name = "main"
    
    print("=" * 60)
    print("飞书智能助理启动中...")
    print("=" * 60)
    
    # 初始化日志
    setup_logger(
        name="feishu_bot",
        log_to_file=settings.log_to_file,
        log_to_console=settings.log_to_console
    )
    
    log.info(method_name, "日志系统初始化完成")
    
    # 检查配置
    if not check_config():
        log.error(method_name, "配置检查失败，请检查环境变量或.env文件")
        sys.exit(1)
    
    log.info(method_name, f"飞书AppID: {settings.feishu.app_id}")
    log.info(method_name, f"豆包模型: {settings.doubao.model or '未配置'}")
    log.info(method_name, f"多维表格: {settings.bitable.app_token or '未配置'} | 表格ID: {settings.bitable.table_id or '未配置'}")
    
    # 初始化鉴权模块
    auth = FeishuAuth()
    
    # 启动token自动刷新
    auth.start_auto_refresh()
    log.info(method_name, "鉴权模块启动完成，token自动刷新已开启")
    
    # 初始化事件处理器
    event_handler = FeishuEventHandler(auth)
    
    # 检查AI服务可用性
    intent_service = IntentService()
    if intent_service.is_ai_available():
        log.info(method_name, "AI服务可用")
    else:
        log.warning(method_name, "AI服务不可用，仅关键字回复功能可用")
    
    # 注册信号处理
    def signal_handler(sig, frame):
        log.info(method_name, "收到退出信号，正在关闭...")
        auth.stop_auto_refresh()
        event_handler.stop()
        log.info(method_name, "飞书智能助理已停止")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动长连接监听
        log.info(method_name, "正在启动飞书长连接...")
        event_handler.start()
        
    except Exception as e:
        log.exception(method_name, f"启动失败: {e}")
        auth.stop_auto_refresh()
        sys.exit(1)


if __name__ == "__main__":
    main()
