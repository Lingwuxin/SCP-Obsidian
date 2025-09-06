from src.handle_zim.readzim import ReadZIM
import sys
import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.html_parser.html_processor import SCPHtmlProcessor
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


load_dotenv()


SCP_OFFLINE_ZIM_PATH = os.getenv("SCP_OFFLINE_ZIM_PATH")
if not SCP_OFFLINE_ZIM_PATH:
    raise ValueError("请设置环境变量 SCP_OFFLINE_ZIM_PATH 指向 SCP ZIM 文件的路径")
SCP_MD_OUTPUT_DIR = os.getenv("SCP_MD_OUTPUT_DIR")
if not SCP_MD_OUTPUT_DIR:
    raise ValueError("请设置环境变量 SCP_MD_OUTPUT_DIR 指向 Markdown 输出目录的路径")
if SCP_MD_OUTPUT_DIR and SCP_MD_OUTPUT_DIR[-1] == '/':
    SCP_MD_OUTPUT_DIR = SCP_MD_OUTPUT_DIR[:-1]

# 设置日志系统
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'scp_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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
        
        logger.info(f"✅ 成功处理: {scp_id}")
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
        
        logger.error(f"❌ 处理失败: {scp_id} - {error}")
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
        logger.info("=" * 50)
        logger.info("处理摘要:")
        logger.info(f"总计处理: {stats['total_processed']}")
        logger.info(f"成功: {stats['successful']}")
        logger.info(f"失败: {stats['failed']}")
        logger.info(f"成功率: {stats['success_rate']:.2f}%")
        logger.info(f"本次会话处理: {stats['current_session']['processed']}")
        logger.info(f"本次会话成功: {stats['current_session']['successful']}")
        logger.info(f"本次会话失败: {stats['current_session']['failed']}")
        logger.info("=" * 50)

# 创建全局跟踪器实例
tracker = SCPProcessingTracker(LOG_DIR)


    
def make_obsidian_md(zim: ReadZIM, scp_id: str) -> bool:
    """
    make the scp markdown file how to use the SCP ZIM.
    scp_id: The ID of the SCP to generate the markdown for. like "scp-001","scp-8002"
    """
    try:
        # 检查是否已经处理过
        if tracker.should_skip(scp_id):
            logger.info(f"⏭️ 跳过已处理的项目: {scp_id}")
            return True
        
        logger.info(f"🔄 开始处理: {scp_id}")
        content = zim.get_content(scp_id)
        
        if not content:
            tracker.record_failure(scp_id, "无法获取内容", {"reason": "content is None or empty"})
            return False
        
        html_processor = SCPHtmlProcessor(content)
        
        if not html_processor.page_content_div:
            tracker.record_failure(scp_id, "无法解析页面内容", {"reason": "page_content_div is None"})
            return False
        
        img_sources = html_processor.extract_image_sources()
        details: Dict[str, Any] = {"images_found": len(img_sources)}
        
        # 处理图片
        if img_sources and SCP_MD_OUTPUT_DIR is not None:
            successful_images = 0
            failed_images = 0
            
            for img_src in img_sources:
                # 提取并保存图片
                img_data = zim.get_img(img_src)
                if img_data:
                    # 保持原始目录结构，构建完整保存路径
                    save_path = os.path.join(SCP_MD_OUTPUT_DIR, img_src)
                    
                    # 自动创建所需的目录结构
                    save_dir = os.path.dirname(save_path)
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # 保存图片文件
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                    
                    logger.info(f"📷 图片已保存: {os.path.basename(img_src)}")
                    
                    # 更新HTML中的图片路径（使用相对路径）
                    html_processor.update_image_paths(img_src, img_src)
                    successful_images += 1
                else:
                    logger.warning(f"⚠️ 图片提取失败: {img_src}")
                    failed_images += 1
                    
            details.update({
                "images_successful": successful_images,
                "images_failed": failed_images
            })
                    
        elif img_sources and SCP_MD_OUTPUT_DIR is None:
            error_msg = "SCP_MD_OUTPUT_DIR 环境变量未设置"
            tracker.record_failure(scp_id, error_msg, details)
            raise ValueError(error_msg)
        
        # 生成 Markdown 文件
        md_content = f'{html_processor.page_content_div}'
        output_file = f"{SCP_MD_OUTPUT_DIR}/{scp_id}.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
            if html_processor.page_tags:
                f.write(f"\n\n\n{' '.join(html_processor.page_tags)}")
        
        details.update({
            "output_file": output_file,
            "tags_count": len(html_processor.page_tags),
            "content_length": len(md_content)
        })
        
        tracker.record_success(scp_id, details)
        return True
        
    except Exception as e:
        error_msg = f"处理过程中发生异常: {str(e)}"
        tracker.record_failure(scp_id, error_msg, {"exception_type": type(e).__name__})
        logger.exception(f"处理 {scp_id} 时发生异常")
        return False
#自动生成scp编号，如：scp-001、scp-1003
def scp_num_generator():
    """
    生成 SCP 编号
    """
    for i in range(1, 10000):
        yield f"scp-{i:03d}"

def main():
    """主函数"""
    try:
        zim_file_path = SCP_OFFLINE_ZIM_PATH
        zim = ReadZIM(zim_file_path)
        zim.read_zim()
        
        # 开始处理会话
        tracker.start_session()
        
        # 单个测试
        # make_obsidian_md(zim, 'scp-2511')
        
        # 批量处理
        logger.info("开始批量处理SCP文档...")
        failed_count = 0
        max_consecutive_failures = 10  # 最大连续失败次数
        
        for scp_id in scp_num_generator():
            if failed_count >= max_consecutive_failures:
                logger.warning(f"连续失败次数达到 {max_consecutive_failures}，停止处理")
                break
                
            success = make_obsidian_md(zim, scp_id)
            
            if not success:
                failed_count += 1
            else:
                failed_count = 0  # 重置连续失败计数
                
            # 每处理100个项目打印一次统计
            if tracker.status_data['current_session']['processed'] % 100 == 0:
                tracker.print_summary()
        
        # 处理完成，打印最终摘要
        tracker.print_summary()
        logger.info("处理完成！")
        
        # 如果有失败的项目，提供重试建议
        failed_items = tracker.status_data['failed_items']
        if failed_items:
            logger.info(f"有 {len(failed_items)} 个项目处理失败，详细信息请查看: {tracker.failed_file}")
            logger.info("可以重新运行程序来重试失败的项目")
            
    except KeyboardInterrupt:
        logger.info("用户中断了处理过程")
        tracker.print_summary()
    except Exception as e:
        logger.error(f"程序执行过程中发生严重错误: {e}")
        logger.exception("详细错误信息:")
    finally:
        # 确保保存最终状态
        tracker.save_status()
if __name__ == "__main__":
    main()
