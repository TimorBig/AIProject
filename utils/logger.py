"""
日志模块
提供统一的日志记录功能，支持输出到文件和控制台
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


# 日志根目录
LOG_DIR = Path(__file__).parent.parent / "logs"


class MethodNameFilter(logging.Filter):
    """自定义过滤器，添加调用方法名到日志记录"""
    
    def filter(self, record):
        if not hasattr(record, 'method_name'):
            record.method_name = 'unknown'
        return True


def setup_logger(
    name: str = "feishu_bot",
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    设置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
    
    Returns:
        配置好的日志记录器
    """
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式：时间戳 | 级别 | 方法名 | 消息内容
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(method_name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加自定义过滤器
    logger.addFilter(MethodNameFilter())
    
    # 文件处理器 - 按日期分割
    if log_to_file:
        log_filename = LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(
            filename=log_filename,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "feishu_bot") -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


class LoggerAdapter:
    """
    日志适配器，提供便捷的日志记录方法
    自动记录方法名和异常信息
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, method_name: str, message: str, exc_info: bool = False):
        """内部日志方法"""
        extra = {'method_name': method_name}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
    
    def info(self, method_name: str, message: str):
        """记录信息级别日志"""
        self._log(logging.INFO, method_name, message)
    
    def debug(self, method_name: str, message: str):
        """记录调试级别日志"""
        self._log(logging.DEBUG, method_name, message)
    
    def warning(self, method_name: str, message: str):
        """记录警告级别日志"""
        self._log(logging.WARNING, method_name, message)
    
    def error(self, method_name: str, message: str, exc_info: bool = True):
        """记录错误级别日志，默认包含异常堆栈"""
        self._log(logging.ERROR, method_name, message, exc_info=exc_info)
    
    def exception(self, method_name: str, message: str):
        """记录异常日志，自动包含异常堆栈"""
        extra = {'method_name': method_name}
        self.logger.exception(message, extra=extra)
    
    def log_api_call(self, method_name: str, api_name: str, params: dict = None, response: dict = None):
        """
        记录API调用日志
        
        Args:
            method_name: 调用方法名
            api_name: API名称
            params: 请求参数
            response: 响应结果
        """
        msg_parts = [f"[API调用] {api_name}"]
        if params:
            msg_parts.append(f"请求参数: {params}")
        if response:
            msg_parts.append(f"响应结果: {response}")
        self._log(logging.INFO, method_name, " | ".join(msg_parts))
    
    def log_api_error(self, method_name: str, api_name: str, error: Exception):
        """
        记录API调用错误日志
        
        Args:
            method_name: 调用方法名
            api_name: API名称
            error: 异常对象
        """
        msg = f"[API错误] {api_name} | 异常类型: {type(error).__name__} | 异常信息: {str(error)}"
        self._log(logging.ERROR, method_name, msg, exc_info=True)


# 初始化全局日志
setup_logger()

# 全局日志适配器实例
log = LoggerAdapter(get_logger())
