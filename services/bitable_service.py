"""
多维表格服务
封装飞书多维表格API，支持记录的查询、新增、更新操作
"""
import json
import requests
from typing import Optional, Dict, Any, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from core.auth import FeishuAuth
from utils.logger import log


class BitableService:
    """
    多维表格服务
    封装飞书多维表格API操作
    """
    
    def __init__(self, auth: FeishuAuth):
        """
        初始化多维表格服务
        
        Args:
            auth: 飞书鉴权实例
        """
        self.auth = auth
        self.base_url = settings.feishu.base_url
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        return self.auth.get_auth_header()
    
    # ==================== 查询记录 ====================
    
    def search_records(
        self,
        app_token: str,
        table_id: str,
        view_id: Optional[str] = None,
        field_names: Optional[List[str]] = None,
        sort: Optional[List[dict]] = None,
        filter_condition: Optional[str] = None,
        page_size: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询多维表格记录
        
        API: POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/search
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            view_id: 视图ID（可选）
            field_names: 返回字段名列表（可选）
            sort: 排序条件（可选）
            filter_condition: 筛选条件（可选）
            page_size: 分页大小
            page_token: 分页token
        
        Returns:
            查询结果
        """
        method_name = "BitableService.search_records"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
        
        body = {}
        if view_id:
            body["view_id"] = view_id
        if field_names:
            body["field_names"] = field_names
        if sort:
            body["sort"] = sort
        if filter_condition:
            body["filter"] = filter_condition
        if page_token:
            body["page_token"] = page_token
        body["page_size"] = page_size
        
        try:
            log.info(method_name, f"查询记录 | 表格: {table_id}")
            log.log_api_call(method_name, "search_records", {"table_id": table_id, "filter": filter_condition})
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"查询记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            log.info(method_name, f"查询记录成功 | 数量: {len(result.get('data', {}).get('items', []))}")
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "search_records", e)
            return {"success": False, "error": str(e), "data": None}
    
    def batch_get_records(
        self,
        app_token: str,
        table_id: str,
        record_ids: List[str]
    ) -> Dict[str, Any]:
        """
        批量获取记录
        
        API: GET /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_get
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            record_ids: 记录ID列表
        
        Returns:
            记录数据列表
        """
        method_name = "BitableService.batch_get_records"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_get"
        params = {"record_ids": ",".join(record_ids)}
        
        try:
            log.info(method_name, f"批量获取记录 | 数量: {len(record_ids)}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"批量获取记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "batch_get_records", e)
            return {"success": False, "error": str(e), "data": None}
    
    # ==================== 新增记录 ====================
    
    def create_record(
        self,
        app_token: str,
        table_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        新增单条记录
        
        API: POST /bitable/v1/apps/{app_token}/tables/{table_id}/records
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            fields: 字段数据字典
        
        Returns:
            新增的记录信息
        """
        method_name = "BitableService.create_record"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        body = {
            "fields": fields
        }
        
        try:
            log.info(method_name, f"新增记录 | 表格: {table_id} | 字段: {list(fields.keys())}")
            log.log_api_call(method_name, "create_record", {"table_id": table_id, "fields": fields})
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"新增记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            log.info(method_name, f"新增记录成功 | 记录ID: {result.get('data', {}).get('record', {}).get('record_id')}")
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "create_record", e)
            return {"success": False, "error": str(e), "data": None}
    
    def batch_create_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量新增记录
        
        API: POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            records: 记录列表，每条记录为字段数据字典
        
        Returns:
            新增的记录列表
        """
        method_name = "BitableService.batch_create_records"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        body = {
            "records": [{"fields": record} for record in records]
        }
        
        try:
            log.info(method_name, f"批量新增记录 | 表格: {table_id} | 数量: {len(records)}")
            log.log_api_call(method_name, "batch_create_records", {"table_id": table_id, "count": len(records)})
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"批量新增记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            log.info(method_name, f"批量新增记录成功")
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "batch_create_records", e)
            return {"success": False, "error": str(e), "data": None}
    
    # ==================== 更新记录 ====================
    
    def update_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新单条记录
        
        API: PUT /bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            record_id: 记录ID
            fields: 要更新的字段数据字典
        
        Returns:
            更新后的记录信息
        """
        method_name = "BitableService.update_record"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        body = {
            "fields": fields
        }
        
        try:
            log.info(method_name, f"更新记录 | 记录ID: {record_id} | 字段: {list(fields.keys())}")
            log.log_api_call(method_name, "update_record", {"record_id": record_id, "fields": fields})
            
            response = requests.put(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"更新记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            log.info(method_name, f"更新记录成功")
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "update_record", e)
            return {"success": False, "error": str(e), "data": None}
    
    def batch_update_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量更新记录
        
        API: POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            records: 记录列表，每条记录包含 record_id 和 fields
        
        Returns:
            更新的记录列表
        """
        method_name = "BitableService.batch_update_records"
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
        body = {
            "records": records
        }
        
        try:
            log.info(method_name, f"批量更新记录 | 表格: {table_id} | 数量: {len(records)}")
            log.log_api_call(method_name, "batch_update_records", {"table_id": table_id, "count": len(records)})
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                log.error(method_name, f"批量更新记录失败: {result.get('msg')}")
                return {"success": False, "error": result.get("msg"), "data": None}
            
            log.info(method_name, f"批量更新记录成功")
            return {"success": True, "data": result.get("data")}
            
        except Exception as e:
            log.log_api_error(method_name, "batch_update_records", e)
            return {"success": False, "error": str(e), "data": None}
    
    # ==================== 业务封装方法 ====================
    
    def find_record_by_field(
        self,
        app_token: str,
        table_id: str,
        field_name: str,
        field_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据字段值查找记录
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            field_name: 字段名
            field_value: 字段值
        
        Returns:
            匹配的记录，未找到返回None
        """
        method_name = "BitableService.find_record_by_field"
        
        # 构建筛选条件
        filter_condition = json.dumps({
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": field_name,
                    "operator": "is",
                    "value": [field_value]
                }
            ]
        })
        
        result = self.search_records(
            app_token=app_token,
            table_id=table_id,
            filter_condition=filter_condition
        )
        
        if result.get("success") and result.get("data", {}).get("items"):
            return result["data"]["items"][0]
        
        return None
    
    def upsert_record(
        self,
        app_token: str,
        table_id: str,
        fields: Dict[str, Any],
        match_field: str = "需求内容"
    ) -> Dict[str, Any]:
        """
        智能新增或更新记录（根据匹配字段判断）
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            fields: 字段数据
            match_field: 用于匹配的字段名
        
        Returns:
            操作结果
        """
        method_name = "BitableService.upsert_record"
        
        match_value = fields.get(match_field)
        if not match_value:
            log.warning(method_name, f"缺少匹配字段值: {match_field}")
            return {"success": False, "error": f"缺少匹配字段值: {match_field}"}
        
        # 查找是否存在
        existing_record = self.find_record_by_field(
            app_token=app_token,
            table_id=table_id,
            field_name=match_field,
            field_value=str(match_value)
        )
        
        if existing_record:
            # 更新记录
            record_id = existing_record.get("record_id")
            log.info(method_name, f"记录已存在，执行更新 | 记录ID: {record_id}")
            return self.update_record(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                fields=fields
            )
        else:
            # 新增记录
            log.info(method_name, f"记录不存在，执行新增")
            return self.create_record(
                app_token=app_token,
                table_id=table_id,
                fields=fields
            )
    
    def upsert_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]],
        match_field: str = "需求内容"
    ) -> Dict[str, Any]:
        """
        批量智能新增或更新记录
        
        Args:
            app_token: 多维表格App Token
            table_id: 数据表ID
            records: 记录列表
            match_field: 用于匹配的字段名
        
        Returns:
            操作结果统计
        """
        method_name = "BitableService.upsert_records"
        
        created = []
        updated = []
        errors = []
        
        for record in records:
            result = self.upsert_record(
                app_token=app_token,
                table_id=table_id,
                fields=record,
                match_field=match_field
            )
            
            if result.get("success"):
                # 判断是新增还是更新（根据返回数据判断）
                if "record_id" in result.get("data", {}).get("record", {}):
                    if "更新" in str(result):
                        updated.append(record)
                    else:
                        created.append(record)
            else:
                errors.append({"record": record, "error": result.get("error")})
        
        log.info(method_name, f"批量操作完成 | 新增: {len(created)} | 更新: {len(updated)} | 失败: {len(errors)}")
        
        return {
            "success": True,
            "data": {
                "created": len(created),
                "updated": len(updated),
                "errors": errors
            }
        }
