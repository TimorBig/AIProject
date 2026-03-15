"""
AI对话服务
使用OpenAI SDK兼容方式接入豆包大模型
"""
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from config.settings import settings
from utils.logger import log


class AIService:
    """
    AI对话服务
    使用OpenAI SDK接入豆包大模型
    """
    
    def __init__(self):
        """初始化AI服务"""
        self.config = settings.doubao
        self.client: Optional[OpenAI] = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        method_name = "AIService._init_client"
        
        try:
            if not self.config.api_key:
                log.warning(method_name, "豆包API Key未配置，AI服务将不可用")
                return
            
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            
            log.info(method_name, f"AI服务初始化成功 | 模型: {self.config.model}")
            
        except Exception as e:
            log.log_api_error(method_name, "init_client", e)
            self.client = None
    
    def chat(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        进行对话
        
        Args:
            message: 用户消息
            user_id: 用户ID（用于上下文管理）
            conversation_history: 对话历史
        
        Returns:
            AI回复内容
        """
        method_name = "AIService.chat"
        
        if not self.client:
            log.error(method_name, "AI服务未初始化或不可用")
            return "抱歉，AI服务暂时不可用，请稍后再试。"
        
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统提示
            messages.append({
                "role": "system",
                "content": "你是飞书智能助理，一个友好、专业的AI助手。请用简洁、清晰的语言回答用户问题。"
            })
            
            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history)
            
            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message
            })
            
            log.info(method_name, f"发送AI对话请求 | 用户: {user_id} | 消息: {message[:50]}...")
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            # 提取回复
            reply = response.choices[0].message.content
            
            log.info(method_name, f"AI回复成功 | 回复长度: {len(reply)}")
            log.log_api_call(
                method_name,
                "doubao_chat",
                {"user_id": user_id, "message_length": len(message)},
                {"reply_length": len(reply)}
            )
            
            return reply
            
        except Exception as e:
            log.log_api_error(method_name, "doubao_chat", e)
            return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """
        检查AI服务是否可用
        
        Returns:
            是否可用
        """
        return self.client is not None and bool(self.config.api_key)
    
    def update_config(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        更新配置并重新初始化客户端
        
        Args:
            api_key: 新的API Key
            base_url: 新的Base URL
            model: 新的模型名称
        """
        method_name = "AIService.update_config"
        
        if api_key:
            self.config.api_key = api_key
        if base_url:
            self.config.base_url = base_url
        if model:
            self.config.model = model
        
        self._init_client()
        log.info(method_name, "AI服务配置已更新")


class ConversationManager:
    """
    对话上下文管理器
    管理用户的对话历史
    """
    
    def __init__(self, max_history: int = 10):
        """
        初始化对话管理器
        
        Args:
            max_history: 最大保留历史消息数
        """
        self.max_history = max_history
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        获取用户的对话历史
        
        Args:
            user_id: 用户ID
        
        Returns:
            对话历史列表
        """
        return self._conversations.get(user_id, [])
    
    def add_message(self, user_id: str, role: str, content: str):
        """
        添加消息到对话历史
        
        Args:
            user_id: 用户ID
            role: 角色 (user/assistant)
            content: 消息内容
        """
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        self._conversations[user_id].append({
            "role": role,
            "content": content
        })
        
        # 限制历史长度
        if len(self._conversations[user_id]) > self.max_history * 2:
            self._conversations[user_id] = self._conversations[user_id][-self.max_history * 2:]
    
    def clear_history(self, user_id: str):
        """
        清除用户的对话历史
        
        Args:
            user_id: 用户ID
        """
        self._conversations[user_id] = []
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            统计信息
        """
        history = self._conversations.get(user_id, [])
        return {
            "total_messages": len(history),
            "user_messages": len([m for m in history if m["role"] == "user"]),
            "assistant_messages": len([m for m in history if m["role"] == "assistant"])
        }
