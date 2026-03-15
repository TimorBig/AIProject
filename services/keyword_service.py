"""
关键字匹配服务
实现关键字自动回复功能
"""
import re
from datetime import datetime
from typing import Optional, Tuple, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings, KeywordRule
from utils.logger import log


class KeywordService:
    """
    关键字匹配服务
    支持多种匹配模式：精确匹配、包含匹配、前缀匹配、后缀匹配、正则匹配
    """
    
    def __init__(self):
        """初始化关键字服务"""
        self.rules: List[KeywordRule] = settings.keywords.rules
    
    def match(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        匹配消息中的关键字
        
        Args:
            message: 用户消息内容
        
        Returns:
            (是否匹配, 回复内容)
        """
        method_name = "KeywordService.match"
        
        if not message or not message.strip():
            return False, None
        
        message = message.strip()
        
        for rule in self.rules:
            matched, reply = self._match_rule(message, rule)
            if matched:
                log.info(method_name, f"关键字匹配成功 | 规则: {rule.keywords} | 匹配类型: {rule.match_type}")
                return True, reply
        
        return False, None
    
    def _match_rule(self, message: str, rule: KeywordRule) -> Tuple[bool, Optional[str]]:
        """
        根据规则匹配消息
        
        Args:
            message: 用户消息
            rule: 关键字规则
        
        Returns:
            (是否匹配, 回复内容)
        """
        # 处理大小写
        check_message = message if rule.case_sensitive else message.lower()
        
        for keyword in rule.keywords:
            check_keyword = keyword if rule.case_sensitive else keyword.lower()
            
            matched = False
            
            if rule.match_type == "exact":
                # 精确匹配
                matched = check_message == check_keyword
            elif rule.match_type == "contains":
                # 包含匹配
                matched = check_keyword in check_message
            elif rule.match_type == "prefix":
                # 前缀匹配
                matched = check_message.startswith(check_keyword)
            elif rule.match_type == "suffix":
                # 后缀匹配
                matched = check_message.endswith(check_keyword)
            elif rule.match_type == "regex":
                # 正则匹配
                try:
                    pattern = re.compile(check_keyword)
                    matched = bool(pattern.search(check_message))
                except re.error:
                    log.warning("KeywordService._match_rule", f"正则表达式无效: {keyword}")
                    continue
            
            if matched:
                # 处理回复内容中的占位符
                reply = self._process_reply(rule.reply)
                return True, reply
        
        return False, None
    
    def _process_reply(self, reply: str) -> str:
        """
        处理回复内容中的占位符
        
        Args:
            reply: 原始回复内容
        
        Returns:
            处理后的回复内容
        """
        # 替换时间占位符
        if "{current_time}" in reply:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reply = reply.replace("{current_time}", current_time)
        
        # 替换日期占位符
        if "{current_date}" in reply:
            current_date = datetime.now().strftime("%Y-%m-%d")
            reply = reply.replace("{current_date}", current_date)
        
        return reply
    
    def add_rule(self, rule: KeywordRule):
        """
        添加关键字规则
        
        Args:
            rule: 关键字规则
        """
        method_name = "KeywordService.add_rule"
        self.rules.append(rule)
        log.info(method_name, f"添加关键字规则: {rule.keywords}")
    
    def remove_rule(self, keywords: List[str]) -> bool:
        """
        移除关键字规则
        
        Args:
            keywords: 要移除的关键字列表
        
        Returns:
            是否成功移除
        """
        method_name = "KeywordService.remove_rule"
        
        for i, rule in enumerate(self.rules):
            if rule.keywords == keywords:
                self.rules.pop(i)
                log.info(method_name, f"移除关键字规则: {keywords}")
                return True
        
        return False
    
    def get_all_rules(self) -> List[dict]:
        """
        获取所有关键字规则
        
        Returns:
            规则列表
        """
        return [
            {
                "keywords": rule.keywords,
                "reply": rule.reply,
                "match_type": rule.match_type,
                "case_sensitive": rule.case_sensitive
            }
            for rule in self.rules
        ]
