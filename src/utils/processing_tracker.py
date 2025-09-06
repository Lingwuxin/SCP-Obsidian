
from datetime import datetime
import json
import os
from typing import Any, Dict, Optional
from venv import logger

from tqdm import tqdm


class SCPProcessingTracker:
    """SCP 处理状态跟踪器"""
    
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.status_file = os.path.join(log_dir, 'processing_status.json')
        self.failed_file = os.path.join(log_dir, 'failed_items.json')
        self.status_data = self.load_status()
        
    def load_status(self) -> dict:
        """加载处理状态"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        
        return {
            'last_run': None,
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'completed_items': [],
            'failed_items': [],
            'current_session': {
                'start_time': None,
                'processed': 0,
                'successful': 0,
                'failed': 0
            }
        }
    
    def save_status(self):
        """保存处理状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def start_session(self):
        """开始新的处理会话"""
        self.status_data['current_session'] = {
            'start_time': datetime.now().isoformat(),
            'processed': 0,
            'successful': 0,
            'failed': 0
        }
        self.status_data['last_run'] = datetime.now().isoformat()
        logger.info("开始新的SCP处理会话")
    
    def record_success(self, scp_id: str, details: Optional[Dict[str, Any]] = None):
        """记录成功处理的项目"""
        if scp_id not in self.status_data['completed_items']:
            self.status_data['completed_items'].append(scp_id)
        
        self.status_data['successful'] += 1
        self.status_data['total_processed'] += 1
        self.status_data['current_session']['successful'] += 1
        self.status_data['current_session']['processed'] += 1
        
        # 从失败列表中移除（如果存在）
        if scp_id in self.status_data['failed_items']:
            self.status_data['failed_items'].remove(scp_id)
            self.status_data['failed'] -= 1
        
        logger.info(f"[SUCCESS] 成功处理: {scp_id}")
        if details:
            logger.info(f"   详情: {details}")
        
        self.save_status()
    
    def record_failure(self, scp_id: str, error: str, details: Optional[Dict[str, Any]] = None):
        """记录失败的项目"""
        failure_record = {
            'scp_id': scp_id,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        # 保存详细的失败记录
        failed_items = []
        if os.path.exists(self.failed_file):
            try:
                with open(self.failed_file, 'r', encoding='utf-8') as f:
                    failed_items = json.load(f)
            except:
                pass
        
        # 更新或添加失败记录
        existing_index = -1
        for i, item in enumerate(failed_items):
            if item['scp_id'] == scp_id:
                existing_index = i
                break
        
        if existing_index >= 0:
            failed_items[existing_index] = failure_record
        else:
            failed_items.append(failure_record)
        
        try:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存失败记录时出错: {e}")
        
        # 更新状态
        if scp_id not in self.status_data['failed_items']:
            self.status_data['failed_items'].append(scp_id)
            self.status_data['failed'] += 1
        
        self.status_data['total_processed'] += 1
        self.status_data['current_session']['failed'] += 1
        self.status_data['current_session']['processed'] += 1
        
        logger.error(f"[FAILED] 处理失败: {scp_id} - {error}")
        if details:
            logger.error(f"   详情: {details}")
        
        self.save_status()
    
    def should_skip(self, scp_id: str) -> bool:
        """检查是否应该跳过此项目"""
        return scp_id in self.status_data['completed_items']
    
    def get_statistics(self) -> dict:
        """获取处理统计信息"""
        return {
            'total_processed': self.status_data['total_processed'],
            'successful': self.status_data['successful'],
            'failed': self.status_data['failed'],
            'success_rate': (self.status_data['successful'] / max(1, self.status_data['total_processed'])) * 100,
            'current_session': self.status_data['current_session'],
            'failed_items_count': len(self.status_data['failed_items'])
        }
    
    def print_summary(self):
        """打印处理摘要"""
        stats = self.get_statistics()
        summary_lines = [
            "=" * 50,
            "处理摘要:",
            f"总计处理: {stats['total_processed']}",
            f"成功: {stats['successful']}",
            f"失败: {stats['failed']}",
            f"成功率: {stats['success_rate']:.2f}%",
            f"本次会话处理: {stats['current_session']['processed']}",
            f"本次会话成功: {stats['current_session']['successful']}",
            f"本次会话失败: {stats['current_session']['failed']}",
            "=" * 50
        ]
        
        # 记录到日志文件
        for line in summary_lines:
            logger.info(line)
        
        # 打印到控制台（使用tqdm.write避免干扰进度条）
        try:
            for line in summary_lines:
                tqdm.write(f"[INFO] {line}")
        except:
            for line in summary_lines:
                print(f"[INFO] {line}")
    
    def get_resume_point(self) -> int:
        """
        获取断点接续的起始点
        
        Returns:
            int: 下一个需要处理的 SCP 编号
        """
        if not self.status_data['completed_items']:
            return 1
        
        # 从已完成的项目中找到最大编号
        max_completed = 0
        for scp_id in self.status_data['completed_items']:
            try:
                if scp_id.startswith('scp-'):
                    num = int(scp_id[4:])  # 去掉 "scp-" 前缀
                    max_completed = max(max_completed, num)
            except ValueError:
                continue
        
        # 返回下一个编号
        next_num = max_completed + 1
        return next_num
    
    def save_resume_point(self, scp_num: int):
        """
        保存当前处理点，用于断点接续
        
        Args:
            scp_num: 当前处理的 SCP 编号
        """
        self.status_data['last_processed_num'] = scp_num
        self.save_status()
