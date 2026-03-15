"""
意图识别服务
整合关键字匹配、意图识别Agent和多维表格操作，进行意图识别和分发
"""
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.keyword_service import KeywordService
from services.ai_service import AIService, ConversationManager
from services.intent_agent import IntentRecognitionAgent, IntentType
from services.bitable_service import BitableService
from config.settings import settings
from utils.logger import log


@dataclass
class ProcessResult:
    """处理结果"""
    intent_type: IntentType
    reply: str
    confidence: float = 1.0
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IntentService:
    """
    意图识别服务
    负责识别用户消息意图并分发到对应的处理流程
    
    流程：
    1. 关键字匹配 -> 直接回复
    2. 意图识别Agent -> 判断意图类型
       - SUMMARY: 总结内容
       - UPDATE_TABLE: 更新多维表格
       - CHAT: 普通对话
    """
    
    def __init__(self):
        """初始化意图识别服务"""
        self.keyword_service = KeywordService()
        self.intent_agent = IntentRecognitionAgent()
        self.ai_service = AIService()
        self.conversation_manager = ConversationManager()
        self.bitable_service: Optional[BitableService] = None
        
        # 多维表格配置（从环境变量或配置文件获取）
        self.bitable_config = {
            "app_token": getattr(settings, 'bitable_app_token', ''),
            "table_id": getattr(settings, 'bitable_table_id', ''),
        }
    
    def set_bitable_service(self, auth):
        """设置多维表格服务（需要鉴权实例）"""
        from core.auth import FeishuAuth
        if isinstance(auth, FeishuAuth):
            self.bitable_service = BitableService(auth)
    
    def process_message(
        self,
        message: str,
        user_id: str,
        message_id: str
    ) -> Tuple[IntentType, str]:
        """
        处理消息，返回意图类型和回复内容
        
        Args:
            message: 用户消息
            user_id: 用户ID
            message_id: 消息ID
        
        Returns:
            (意图类型, 回复内容)
        """
        method_name = "IntentService.process_message"
        
        try:
            result = self._process(message, user_id)
            
            log.info(method_name, 
                f"消息处理完成 | 意图: {result.intent_type.value} | 用户: {user_id} | 消息ID: {message_id}")
            
            return result.intent_type, result.reply
            
        except Exception as e:
            log.exception(method_name, f"处理消息异常: {e}")
            return IntentType.UNKNOWN, "抱歉，处理您的消息时出现错误，请稍后再试。"
    
    def _process(self, message: str, user_id: str) -> ProcessResult:
        """
        内部处理逻辑
        
        Args:
            message: 用户消息
            user_id: 用户ID
        
        Returns:
            处理结果
        """
        method_name = "IntentService._process"
        
        # 1. 关键字匹配（最高优先级）
        matched, keyword_reply = self.keyword_service.match(message)
        if matched:
            log.info(method_name, "关键字匹配成功")
            return ProcessResult(
                intent_type=IntentType.KEYWORD,
                reply=keyword_reply,
                confidence=1.0
            )
        
        # 2. 调用意图识别Agent
        if not self.intent_agent.is_available():
            log.warning(method_name, "意图识别Agent不可用，降级为普通对话")
            return self._handle_chat(message, user_id)
        
        intent_result = self.intent_agent.recognize(message, user_id)
        
        # 3. 根据意图类型分发处理
        if intent_result.intent_type == IntentType.SUMMARY:
            return self._handle_summary(message, user_id, intent_result)
        
        elif intent_result.intent_type == IntentType.UPDATE_TABLE:
            return self._handle_update_table(message, user_id, intent_result)
        
        else:  # CHAT 或其他
            return self._handle_chat(message, user_id)
    
    def _handle_summary(
        self,
        message: str,
        user_id: str,
        intent_result
    ) -> ProcessResult:
        """
        处理总结意图
        
        Args:
            message: 用户消息
            user_id: 用户ID
            intent_result: 意图识别结果
        
        Returns:
            处理结果
        """
        method_name = "IntentService._handle_summary"
        
        log.info(method_name, "处理总结意图")
        
        # 获取需要总结的内容
        extracted = intent_result.extracted_data or {}
        content_to_summarize = extracted.get("content_to_summarize", message)
        
        # 构建总结提示
        summary_prompt = f"""请对以下内容进行总结，提炼要点：

{content_to_summarize}

请用简洁清晰的语言总结，列出主要要点。"""
        
        # 调用AI进行总结
        history = self.conversation_manager.get_history(user_id)
        summary_reply = self.ai_service.chat(summary_prompt, user_id, history)
        
        # 更新对话历史
        self.conversation_manager.add_message(user_id, "user", message)
        self.conversation_manager.add_message(user_id, "assistant", summary_reply)
        
        # 添加意图标识前缀
        reply = f"【总结内容】\n已为您总结如下内容：\n\n{summary_reply}"
        
        return ProcessResult(
            intent_type=IntentType.SUMMARY,
            reply=reply,
            confidence=intent_result.confidence
        )
    
    def _handle_update_table(
        self,
        message: str,
        user_id: str,
        intent_result
    ) -> ProcessResult:
        """
        处理更新多维表格意图
        
        Args:
            message: 用户消息
            user_id: 用户ID
            intent_result: 意图识别结果
        
        Returns:
            处理结果
        """
        method_name = "IntentService._handle_update_table"
        
        log.info(method_name, "处理更新多维表格意图")
        
        # 检查多维表格服务是否可用
        if not self.bitable_service:
            log.warning(method_name, "多维表格服务未初始化")
            return ProcessResult(
                intent_type=IntentType.UPDATE_TABLE,
                reply="【更新表格】\n抱歉，多维表格服务暂未配置，请联系管理员。",
                confidence=intent_result.confidence
            )
        
        # 获取提取的数据
        extracted = intent_result.extracted_data or {}
        records = extracted.get("records", [])
        match_field = extracted.get("match_field", "需求内容")
        
        if not records:
            # 没有提取到结构化数据，尝试用AI理解
            return ProcessResult(
                intent_type=IntentType.UPDATE_TABLE,
                reply="【更新表格】\n正在为您更新多维表格，请稍后...\n\n抱歉，未能从消息中提取到有效的数据字段，请提供更明确的信息，例如：\n- 需求内容：xxx\n- 负责人：xxx\n- 状态：xxx",
                confidence=intent_result.confidence
            )
        
        # 获取多维表格配置
        app_token = self.bitable_config.get("app_token")
        table_id = self.bitable_config.get("table_id")
        
        if not app_token or not table_id:
            log.error(method_name, "多维表格配置缺失")
            return ProcessResult(
                intent_type=IntentType.UPDATE_TABLE,
                reply="【更新表格】\n抱歉，多维表格配置缺失，请联系管理员。",
                confidence=intent_result.confidence
            )
        
        # 执行更新操作
        reply_parts = ["【更新表格】", "正在为您更新多维表格，请稍后...\n"]
        
        try:
            # 批量处理记录
            results = []
            for record in records:
                result = self.bitable_service.upsert_record(
                    app_token=app_token,
                    table_id=table_id,
                    fields=record,
                    match_field=match_field
                )
                results.append(result)
            
            # 统计结果
            success_count = sum(1 for r in results if r.get("success"))
            fail_count = len(results) - success_count
            
            if success_count > 0:
                reply_parts.append(f"成功处理 {success_count} 条记录。")
            if fail_count > 0:
                reply_parts.append(f"{fail_count} 条记录处理失败。")
            
            # 显示处理的记录详情
            reply_parts.append("\n已处理的记录：")
            for i, record in enumerate(records, 1):
                reply_parts.append(f"\n{i}. {record.get(match_field, '未知')}")
                for key, value in record.items():
                    if key != match_field:
                        reply_parts.append(f"   - {key}: {value}")
            
        except Exception as e:
            log.exception(method_name, f"更新多维表格异常: {e}")
            reply_parts.append(f"\n操作失败：{str(e)}")
        
        return ProcessResult(
            intent_type=IntentType.UPDATE_TABLE,
            reply="\n".join(reply_parts),
            confidence=intent_result.confidence
        )
    
    def _handle_chat(self, message: str, user_id: str) -> ProcessResult:
        """
        处理普通对话意图
        
        Args:
            message: 用户消息
            user_id: 用户ID
        
        Returns:
            处理结果
        """
        method_name = "IntentService._handle_chat"
        
        log.info(method_name, "处理普通对话意图")
        
        # 获取对话历史
        history = self.conversation_manager.get_history(user_id)
        
        # 调用AI服务
        ai_reply = self.ai_service.chat(message, user_id, history)
        
        # 更新对话历史
        self.conversation_manager.add_message(user_id, "user", message)
        self.conversation_manager.add_message(user_id, "assistant", ai_reply)
        
        return ProcessResult(
            intent_type=IntentType.CHAT,
            reply=ai_reply,
            confidence=0.9
        )
    
    def clear_conversation(self, user_id: str):
        """
        清除用户的对话历史
        
        Args:
            user_id: 用户ID
        """
        method_name = "IntentService.clear_conversation"
        self.conversation_manager.clear_history(user_id)
        log.info(method_name, f"已清除用户对话历史 | 用户: {user_id}")
    
    def get_conversation_stats(self, user_id: str) -> dict:
        """
        获取用户对话统计
        
        Args:
            user_id: 用户ID
        
        Returns:
            统计信息
        """
        return self.conversation_manager.get_conversation_stats(user_id)
    
    def is_ai_available(self) -> bool:
        """
        检查AI服务是否可用
        
        Returns:
            是否可用
        """
        return self.ai_service.is_available()
