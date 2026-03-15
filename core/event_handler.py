"""
飞书事件处理器
使用飞书SDK WebSocket长连接模式处理消息事件
"""
import json
from typing import Optional

import lark_oapi as lark
from lark_oapi.api.im.v1.model.p2_im_message_receive_v1 import P2ImMessageReceiveV1

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from core.auth import FeishuAuth
from core.message import MessageSender
from services.intent_service import IntentService, IntentType
from utils.logger import log


class FeishuEventHandler:
    """
    飞书事件处理器
    使用SDK WebSocket长连接模式订阅和处理消息事件
    """
    
    def __init__(self, auth: FeishuAuth):
        """
        初始化事件处理器
        
        Args:
            auth: 飞书鉴权实例
        """
        self.auth = auth
        self.message_sender = MessageSender(auth)
        self.intent_service = IntentService()
        # 初始化多维表格服务
        self.intent_service.set_bitable_service(auth)
        self.intent_service.bitable_config = {
            "app_token": settings.bitable.app_token,
            "table_id": settings.bitable.table_id,
        }
        self.ws_client: Optional[lark.ws.Client] = None
        self.event_handler: Optional[lark.EventDispatcherHandler] = None
    
    def _on_message_receive(self, data: P2ImMessageReceiveV1):
        """
        处理消息接收事件
        
        Args:
            data: 消息接收事件数据
        """
        method_name = "FeishuEventHandler._on_message_receive"
        
        try:
            # 解析事件数据
            event = data.event
            message = event.message
            sender = event.sender
            
            # 提取关键信息
            message_id = message.message_id
            message_type = message.message_type
            content = message.content
            chat_id = message.chat_id
            chat_type = message.chat_type
            
            # 提取发送者信息
            sender_id = sender.sender_id
            open_id = sender_id.open_id
            user_id = sender_id.user_id
            
            log.info(method_name, 
                f"收到消息 | 消息ID: {message_id} | 类型: {message_type} | 用户: {open_id}")
            
            # 只处理文本消息
            if message_type != "text":
                log.info(method_name, f"跳过非文本消息 | 类型: {message_type}")
                return
            
            # 解析消息内容
            try:
                content_json = json.loads(content)
                text_content = content_json.get("text", "")
            except json.JSONDecodeError:
                log.warning(method_name, f"消息内容解析失败: {content}")
                return
            
            # 忽略空消息
            if not text_content.strip():
                log.info(method_name, "消息内容为空，跳过处理")
                return
            
            # 处理消息，识别意图
            intent_type, reply = self.intent_service.process_message(
                message=text_content,
                user_id=open_id or user_id,
                message_id=message_id
            )
            
            # 发送回复（引用原消息）
            if reply:
                self._send_reply(
                    receive_id=open_id or chat_id,
                    message_id=message_id,
                    reply_content=reply,
                    chat_type=chat_type
                )
            
        except Exception as e:
            log.exception(method_name, f"处理消息事件异常: {e}")
    
    def _send_reply(
        self,
        receive_id: str,
        message_id: str,
        reply_content: str,
        chat_type: str = "p2p"
    ):
        """
        发送回复消息（引用回复）
        
        Args:
            receive_id: 接收者ID
            message_id: 原消息ID（用于引用）
            reply_content: 回复内容
            chat_type: 会话类型 (p2p/group)
        """
        method_name = "FeishuEventHandler._send_reply"
        
        try:
            # 确定接收者ID类型
            if chat_type == "p2p":
                receive_id_type = "open_id"
            else:
                receive_id_type = "chat_id"
            
            # 使用消息发送器发送引用回复
            result = self.message_sender.reply_to_message(
                message_id=message_id,
                content=reply_content,
                receive_id=receive_id,
                receive_id_type=receive_id_type
            )
            
            if result.get("success"):
                log.info(method_name, f"回复发送成功 | 原消息: {message_id}")
            else:
                log.error(method_name, f"回复发送失败: {result.get('error')}")
                
        except Exception as e:
            log.log_api_error(method_name, "send_reply", e)
    
    def start(self):
        """
        启动WebSocket长连接监听
        """
        method_name = "FeishuEventHandler.start"
        
        try:
            log.info(method_name, "正在初始化事件处理器...")
            
            # 创建事件处理器
            self.event_handler = lark.EventDispatcherHandler.builder(
                "",  # encrypt_key (可为空)
                "",  # verification_token (可为空)
                lark.LogLevel.DEBUG
            ).register_p2_im_message_receive_v1(self._on_message_receive) \
             .build()
            
            log.info(method_name, "事件处理器初始化成功")
            
            # 创建WebSocket客户端
            log.info(method_name, "正在启动WebSocket长连接...")
            self.ws_client = lark.ws.Client(
                app_id=settings.feishu.app_id,
                app_secret=settings.feishu.app_secret,
                log_level=lark.LogLevel.DEBUG,
                event_handler=self.event_handler
            )
            
            log.info(method_name, "WebSocket长连接已建立，开始监听消息...")
            
            # 启动长连接（阻塞）
            self.ws_client.start()
            
        except Exception as e:
            log.log_api_error(method_name, "start_websocket", e)
            raise
    
    def stop(self):
        """
        停止监听
        """
        method_name = "FeishuEventHandler.stop"
        log.info(method_name, "停止飞书长连接监听")


def create_event_handler(auth: FeishuAuth) -> FeishuEventHandler:
    """
    创建事件处理器实例
    
    Args:
        auth: 飞书鉴权实例
    
    Returns:
        事件处理器实例
    """
    return FeishuEventHandler(auth)
