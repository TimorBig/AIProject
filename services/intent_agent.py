"""
意图识别Agent服务
使用豆包大模型进行意图识别，支持总结、更新表格、对话等意图类型
"""
import json
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_service import AIService
from utils.logger import log


class IntentType(Enum):
    """意图类型"""
    SUMMARY = "SUMMARY"           # 总结内容
    UPDATE_TABLE = "UPDATE_TABLE" # 更新多维表格
    CHAT = "CHAT"                 # 普通对话
    KEYWORD = "KEYWORD"           # 关键字匹配
    UNKNOWN = "UNKNOWN"           # 未知意图


@dataclass
class IntentResult:
    """意图识别结果"""
    intent_type: IntentType
    confidence: float = 1.0
    extracted_data: Dict[str, Any] = None
    reason: str = ""
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}


# 意图识别系统提示词
INTENT_RECOGNITION_SYSTEM_PROMPT = """你是一个专业的意图识别专家，负责分析用户发送的消息，准确识别用户的意图类型并提取相关信息。

## 意图类型

你需要将用户消息分类为以下三种意图之一：

### 1. SUMMARY - 总结内容
用户希望对某些内容进行总结、归纳、提炼要点。
触发关键词：总结、归纳、提炼、概括、要点

### 2. UPDATE_TABLE - 更新多维表格
用户希望向多维表格中新增或更新数据记录。
触发关键词：添加、新增、记录、登记、更新表格、修改
或者消息包含结构化数据字段（如：需求名称、负责人、状态、优先级等）

### 3. CHAT - 普通对话
用户进行日常对话、提问或闲聊，不涉及具体业务操作。

## 输出格式

请严格按照以下JSON格式输出，不要输出其他内容：
```json
{
  "intent_type": "SUMMARY|UPDATE_TABLE|CHAT",
  "confidence": 0.0-1.0,
  "extracted_data": {...},
  "reason": "判断理由"
}
```

### 各意图类型的 extracted_data 结构

**SUMMARY（总结内容）：**
```json
{
  "content_to_summarize": "需要总结的内容",
  "summary_style": "简洁"
}
```

**UPDATE_TABLE（更新多维表格）：**
```json
{
  "action": "create|update",
  "records": [
    {
      "需求内容": "xxx",
      "负责人": "xxx",
      "状态": "xxx",
      "优先级": "xxx",
      "备注": "xxx"
    }
  ],
  "match_field": "需求内容"
}
```
注意：根据用户消息内容识别字段，用户可能只提供部分字段，只提取用户明确提到的字段。

**CHAT（普通对话）：**
```json
{
  "topic": "对话主题",
  "sentiment": "positive|neutral|negative"
}
```

## 约束条件

- 准确识别意图类型，优先级：UPDATE_TABLE > SUMMARY > CHAT
- 当消息包含结构化数据字段时，优先判断为 UPDATE_TABLE
- 只输出JSON，不要输出其他内容"""


class IntentRecognitionAgent:
    """
    意图识别Agent
    使用豆包大模型进行意图识别
    """
    
    def __init__(self):
        """初始化意图识别Agent"""
        self.ai_service = AIService()
    
    def recognize(self, message: str, user_id: str = "") -> IntentResult:
        """
        识别用户消息的意图
        
        Args:
            message: 用户消息
            user_id: 用户ID
        
        Returns:
            意图识别结果
        """
        method_name = "IntentRecognitionAgent.recognize"
        
        if not message or not message.strip():
            return IntentResult(
                intent_type=IntentType.UNKNOWN,
                reason="消息为空"
            )
        
        log.info(method_name, f"开始意图识别 | 用户: {user_id} | 消息: {message[:50]}...")
        
        try:
            # 构建提示
            prompt = f"""请分析以下用户消息的意图：

用户消息：
{message}

请输出意图识别结果（JSON格式）："""
            
            # 调用AI服务
            response = self.ai_service.chat(
                message=prompt,
                user_id=user_id,
                conversation_history=[
                    {"role": "system", "content": INTENT_RECOGNITION_SYSTEM_PROMPT}
                ]
            )
            
            # 解析结果
            result = self._parse_response(response)
            
            log.info(method_name, f"意图识别完成 | 类型: {result.intent_type.value} | 置信度: {result.confidence}")
            
            return result
            
        except Exception as e:
            log.exception(method_name, f"意图识别异常: {e}")
            return IntentResult(
                intent_type=IntentType.CHAT,
                reason=f"识别异常，默认为对话: {str(e)}"
            )
    
    def _parse_response(self, response: str) -> IntentResult:
        """
        解析AI响应
        
        Args:
            response: AI响应文本
        
        Returns:
            意图识别结果
        """
        method_name = "IntentRecognitionAgent._parse_response"
        
        try:
            # 提取JSON部分
            json_str = response
            
            # 尝试找到JSON代码块
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 映射意图类型
            intent_type_str = data.get("intent_type", "CHAT").upper()
            intent_type_map = {
                "SUMMARY": IntentType.SUMMARY,
                "UPDATE_TABLE": IntentType.UPDATE_TABLE,
                "CHAT": IntentType.CHAT
            }
            intent_type = intent_type_map.get(intent_type_str, IntentType.CHAT)
            
            return IntentResult(
                intent_type=intent_type,
                confidence=float(data.get("confidence", 0.8)),
                extracted_data=data.get("extracted_data", {}),
                reason=data.get("reason", "")
            )
            
        except json.JSONDecodeError as e:
            log.warning(method_name, f"JSON解析失败: {e} | 响应: {response[:100]}")
            return IntentResult(
                intent_type=IntentType.CHAT,
                reason="JSON解析失败，默认为对话"
            )
        except Exception as e:
            log.warning(method_name, f"解析异常: {e}")
            return IntentResult(
                intent_type=IntentType.CHAT,
                reason=f"解析异常，默认为对话"
            )
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.ai_service.is_available()
