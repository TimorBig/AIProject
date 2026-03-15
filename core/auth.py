"""
飞书鉴权模块
封装 tenant_access_token 的获取和自动刷新逻辑
"""
import threading
import time
import requests
from typing import Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from utils.logger import log


@dataclass
class TokenInfo:
    """Token信息"""
    access_token: str
    expire_time: int  # 过期时间戳


class FeishuAuth:
    """
    飞书鉴权管理类
    负责获取和自动刷新 tenant_access_token
    """
    
    def __init__(self):
        self._token: Optional[TokenInfo] = None
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 配置
        self.app_id = settings.feishu.app_id
        self.app_secret = settings.feishu.app_secret
        self.auth_url = settings.feishu.auth_url
        self.refresh_interval = settings.token_refresh_interval
    
    def get_tenant_access_token(self) -> str:
        """
        获取 tenant_access_token
        如果token不存在或即将过期，会自动刷新
        
        Returns:
            tenant_access_token字符串
        """
        with self._lock:
            # 检查token是否有效（提前5分钟刷新）
            if self._token and self._is_token_valid():
                return self._token.access_token
            
            # 刷新token
            return self._refresh_token()
    
    def _is_token_valid(self) -> bool:
        """检查token是否有效（提前5分钟过期）"""
        if not self._token:
            return False
        
        current_time = int(time.time())
        # 提前5分钟刷新
        return current_time < (self._token.expire_time - 300)
    
    def _refresh_token(self) -> str:
        """
        刷新token
        
        Returns:
            新的tenant_access_token
        """
        method_name = "FeishuAuth._refresh_token"
        
        try:
            log.info(method_name, f"开始获取 tenant_access_token")
            
            response = requests.post(
                self.auth_url,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                log.error(method_name, f"获取token失败: {error_msg}")
                raise Exception(f"获取token失败: {error_msg}")
            
            token = result.get("tenant_access_token")
            expire = result.get("expire", 7200)  # 默认2小时
            
            # 计算过期时间
            current_time = int(time.time())
            expire_time = current_time + expire
            
            self._token = TokenInfo(
                access_token=token,
                expire_time=expire_time
            )
            
            log.info(method_name, f"获取token成功，有效期至: {expire_time}")
            log.log_api_call(
                method_name, 
                "tenant_access_token",
                {"app_id": self.app_id},
                {"code": result.get("code"), "expire": expire}
            )
            
            return token
            
        except requests.RequestException as e:
            log.log_api_error(method_name, "tenant_access_token", e)
            raise
        except Exception as e:
            log.log_api_error(method_name, "tenant_access_token", e)
            raise
    
    def start_auto_refresh(self):
        """
        启动自动刷新线程
        每小时自动刷新token
        """
        method_name = "FeishuAuth.start_auto_refresh"
        
        if self._refresh_thread and self._refresh_thread.is_alive():
            log.warning(method_name, "自动刷新线程已在运行")
            return
        
        self._stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True
        )
        self._refresh_thread.start()
        
        log.info(method_name, f"启动token自动刷新，间隔: {self.refresh_interval}秒")
    
    def stop_auto_refresh(self):
        """停止自动刷新线程"""
        method_name = "FeishuAuth.stop_auto_refresh"
        
        self._stop_event.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5)
        
        log.info(method_name, "停止token自动刷新")
    
    def _auto_refresh_loop(self):
        """自动刷新循环"""
        method_name = "FeishuAuth._auto_refresh_loop"
        
        while not self._stop_event.is_set():
            try:
                # 获取/刷新token
                self.get_tenant_access_token()
            except Exception as e:
                log.error(method_name, f"自动刷新token失败: {e}")
            
            # 等待下一次刷新
            self._stop_event.wait(self.refresh_interval)
    
    def get_auth_header(self) -> dict:
        """
        获取认证请求头
        
        Returns:
            包含Authorization的请求头字典
        """
        token = self.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
