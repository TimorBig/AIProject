"""
消息发送模块
封装飞书消息发送API，支持引用回复
"""
import json
import requests
from typing import Optional, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from core.auth import FeishuAuth
from utils.logger import log


class MessageSender:
    """
    消息发送类
    封装飞书消息发送API，支持引用回复
    """
    
    def __init__(self, auth: FeishuAuth):
        """
        初始化消息发送器
        
        Args:
            auth: 飞书鉴权实例
        """
        self.auth = auth
        self.message_url = settings.feishu.message_url
    
    def send_text_message(
        self,
        receive_id: str,
        receive_id_type: str,
        content: str,
        quote_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            receive_id: 接收者ID
            receive_id_type: 接收者ID类型 (open_id, user_id, union_id, email, chat_id)
            content: 消息内容
            quote_message_id: 被引用消息的ID，用于引用回复
        
        Returns:
            API响应结果
        """
        return self.send_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            msg_type="text",
            content=json.dumps({"text": content}),
            quote_message_id=quote_message_id
        )
    
    def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        msg_type: str,
        content: str,
        quote_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送消息（通用方法）
        
        Args:
            receive_id: 接收者ID
            receive_id_type: 接收者ID类型
            msg_type: 消息类型 (text, post, image, etc.)
            content: 消息内容（JSON字符串）
            quote_message_id: 被引用消息的ID
        
        Returns:
            API响应结果
        """
        method_name = "MessageSender.send_message"
        
        try:
            # 构建请求参数
            params = {
                "receive_id_type": receive_id_type
            }
            
            # 构建请求体
            body = {
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": content
            }
            
            # 添加引用消息ID
            if quote_message_id:
                body["quote"] = quote_message_id
            
            # 获取认证头
            headers = self.auth.get_auth_header()
            
            log.info(method_name, f"发送消息 | 接收者: {receive_id} | 类型: {msg_type} | 引用: {quote_message_id}")
            log.log_api_call(
                method_name,
                "send_message",
                {"receive_id": receive_id, "msg_type": msg_type, "quote": quote_message_id}
            )
            
            # 发送请求
            response = requests.post(
                self.message_url,
                params=params,
                headers=headers,
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                log.error(method_name, f"发送消息失败: {error_msg}")
                return {"success": False, "error": error_msg, "response": result}
            
            log.info(method_name, f"发送消息成功")
            return {"success": True, "data": result.get("data")}
            
        except requests.RequestException as e:
            log.log_api_error(method_name, "send_message", e)
            return {"success": False, "error": str(e)}
        except Exception as e:
            log.log_api_error(method_name, "send_message", e)
            return {"success": False, "error": str(e)}
    
    def reply_to_message(
        self,
        message_id: str,
        content: str,
        receive_id: str,
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        引用回复消息
        
        Args:
            message_id: 被回复消息的ID
            content: 回复内容
            receive_id: 接收者ID
            receive_id_type: 接收者ID类型
        
        Returns:
            API响应结果
        """
        method_name = "MessageSender.reply_to_message"
        
        log.info(method_name, f"引用回复消息 | 原消息ID: {message_id} | 内容: {content[:50]}...")
        
        return self.send_text_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            content=content,
            quote_message_id=message_id
        )
    
    def send_rich_text_message(
        self,
        receive_id: str,
        receive_id_type: str,
        title: str,
        content_lines: list,
        quote_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送富文本消息
        
        Args:
            receive_id: 接收者ID
            receive_id_type: 接收者ID类型
            title: 标题
            content_lines: 内容行列表，每行是一个列表，包含多个文本元素
            quote_message_id: 被引用消息的ID
        
        Returns:
            API响应结果
        """
        # 构建富文本内容
        rich_content = [[{"tag": "text", "text": line} if isinstance(line, str) else line for line in row] for row in content_lines]
        
        content = json.dumps({
            "zh_cn": {
                "title": title,
                "content": rich_content
            }
        }, ensure_ascii=False)
        
        return self.send_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            msg_type="post",
            content=content,
            quote_message_id=quote_message_id
        )
