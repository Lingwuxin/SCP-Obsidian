from src.handle_zim.readzim import ReadZIM
import sys
import os
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.html_parser.html_processor import SCPHtmlProcessor
from tqdm import tqdm

from src.utils.processing_tracker import SCPProcessingTracker
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

# 创建日志格式器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 创建文件处理器（记录所有级别的日志）
file_handler = logging.FileHandler(
    os.path.join(LOG_DIR, f'scp_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 创建控制台处理器（只显示警告和错误）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(
    level=logging.DEBUG,  # 设置为DEBUG以确保所有日志都被处理
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

def print_info(message):
    """
    打印重要信息到控制台和日志文件
    用于需要用户看到的重要信息，如开始处理、完成统计等
    """
    # 记录到日志文件
    logger.info(message)
    # 同时打印到控制台（使用tqdm.write避免干扰进度条）
    tqdm.write(f"[INFO] {message}")

def print_progress_info(message):
    """
    在进度条环境中安全地打印信息
    """
    logger.info(message)
    # 如果没有活动的进度条，直接打印；否则使用tqdm.write
    try:
        tqdm.write(f"[INFO] {message}")
    except:
        print(f"[INFO] {message}")

# 创建全局跟踪器实例
tracker = SCPProcessingTracker(LOG_DIR)


def get_scp_subdirectory(scp_id: str) -> str:
    """
    根据 SCP 编号确定应该保存到哪个子目录
    
    Args:
        scp_id: SCP 编号，如 "scp-001", "scp-1234", "scp-2500"
        
    Returns:
        str: 子目录名称，如 "001-1000", "1001-2000", "2001-3000"
    """
    try:
        # 提取数字部分
        if scp_id.startswith('scp-'):
            num_str = scp_id[4:]  # 去掉 "scp-" 前缀
        else:
            num_str = scp_id
            
        num = int(num_str)
        
        # 根据编号范围确定子目录
        if 1 <= num <= 1000:
            return "001-1000"
        elif 1001 <= num <= 2000:
            return "1001-2000"
        elif 2001 <= num <= 3000:
            return "2001-3000"
        elif 3001 <= num <= 4000:
            return "3001-4000"
        elif 4001 <= num <= 5000:
            return "4001-5000"
        elif 5001 <= num <= 6000:
            return "5001-6000"
        elif 6001 <= num <= 7000:
            return "6001-7000"
        elif 7001 <= num <= 8000:
            return "7001-8000"
        elif 8001 <= num <= 9000:
            return "8001-9000"
        elif 9001 <= num <= 10000:
            return "9001-10000"
        else:
            # 对于超出范围的编号，使用通用目录
            return "other"
            
    except ValueError:
        logger.warning(f"无法解析 SCP 编号: {scp_id}")
        return "other"


def make_obsidian_md(zim: ReadZIM, scp_id: str) -> bool:
    """
    make the scp markdown file how to use the SCP ZIM.
    scp_id: The ID of the SCP to generate the markdown for. like "scp-001","scp-8002"
    """
    try:
        # 检查是否已经处理过
        if tracker.should_skip(scp_id):
            logger.info(f"[SKIP] 跳过已处理的项目: {scp_id}")
            return True
        
        logger.info(f"[PROCESSING] 开始处理: {scp_id}")
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
                    
                    logger.info(f"[IMAGE] 图片已保存: {os.path.basename(img_src)}")
                    
                    # # 更新HTML中的图片路径（使用相对路径）
                    # html_processor.update_image_paths(img_src, img_src)
                    successful_images += 1
                else:
                    logger.warning(f"[WARNING] 图片提取失败: {img_src}")
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
        
        # 检查输出目录是否存在
        if SCP_MD_OUTPUT_DIR is None:
            error_msg = "SCP_MD_OUTPUT_DIR 环境变量未设置"
            tracker.record_failure(scp_id, error_msg, details)
            raise ValueError(error_msg)
        
        # 确定子目录
        subdirectory = get_scp_subdirectory(scp_id)
        output_dir = os.path.join(SCP_MD_OUTPUT_DIR, subdirectory)
        
        # 创建子目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建完整的输出文件路径
        output_file = os.path.join(output_dir, f"{scp_id}.md")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
            if html_processor.page_tags:
                f.write(f"\n\n\n{' '.join(html_processor.page_tags)}")
        
        details.update({
            "output_file": output_file,
            "subdirectory": subdirectory,
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
def scp_num_generator(start_num: int = 1, end_num: int = 10000):
    """
    生成 SCP 编号
    
    Args:
        start_num: 开始编号 (默认: 1)
        end_num: 结束编号 (默认: 10000)
    """
    for i in range(start_num, end_num + 1):
        yield f"scp-{i:03d}"

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="SCP Wiki 离线文档处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                          # 从头开始处理所有 SCP
  python main.py --start 100              # 从 SCP-100 开始处理
  python main.py --start 500 --end 1000   # 处理 SCP-500 到 SCP-1000
  python main.py --resume                 # 从上次中断的地方继续
  python main.py --single scp-173         # 只处理单个 SCP-173
        """
    )
    
    parser.add_argument(
        '--start', 
        type=int, 
        default=1,
        help='开始处理的 SCP 编号 (默认: 1)'
    )
    
    parser.add_argument(
        '--end', 
        type=int, 
        default=10000,
        help='结束处理的 SCP 编号 (默认: 10000)'
    )
    
    parser.add_argument(
        '--resume', 
        action='store_true',
        default=True,
        help='从上次中断的地方继续处理 (默认启用)'
    )
    
    parser.add_argument(
        '--no-resume', 
        action='store_true',
        help='禁用断点接续，从指定起始点重新开始处理'
    )
    
    parser.add_argument(
        '--single', 
        type=str,
        help='只处理单个 SCP，格式如 scp-173'
    )
    
    parser.add_argument(
        '--max-failures', 
        type=int, 
        default=10,
        help='最大连续失败次数，达到后停止处理 (默认: 10)'
    )
    
    args = parser.parse_args()
    
    # 处理 resume 和 no-resume 参数的逻辑
    if args.no_resume:
        args.resume = False
    
    return args

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        zim_file_path = SCP_OFFLINE_ZIM_PATH
        zim = ReadZIM(zim_file_path)
        zim.read_zim()
        
        # 开始处理会话
        tracker.start_session()
        
        # 处理单个 SCP
        if args.single:
            print_info(f"单个处理模式: {args.single}")
            success = make_obsidian_md(zim, args.single)
            if success:
                print_info(f"成功处理 {args.single}")
            else:
                logger.error(f"[FAILED] 处理失败 {args.single}")
            tracker.print_summary()
            return
        
        # 确定处理范围
        start_num = args.start
        end_num = args.end
        
        # 断点接续模式
        if args.resume:
            start_num = tracker.get_resume_point()
            print_info(f"断点接续模式: 从 SCP-{start_num:03d} 开始")
        
        # 批量处理
        print_info(f"开始批量处理SCP文档: SCP-{start_num:03d} 到 SCP-{end_num:03d}")
        failed_count = 0
        max_consecutive_failures = args.max_failures
        
        # 计算总数量和已完成数量用于进度条
        total_count = end_num - start_num + 1
        completed_in_range = 0
        
        # 如果是断点接续，计算已完成的数量
        if args.resume:
            for i in range(start_num, end_num + 1):
                scp_check_id = f"scp-{i:03d}"
                if tracker.should_skip(scp_check_id):
                    completed_in_range += 1
        
        # 创建进度条
        with tqdm(
            total=total_count,
            initial=completed_in_range,
            desc="处理SCP文档",
            unit="个",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {desc}",
            ncols=100,
            file=sys.stdout,  # 明确指定输出流
            leave=True,       # 完成后保留进度条
            dynamic_ncols=True  # 动态调整宽度
        ) as pbar:
            
            for scp_id in scp_num_generator(start_num, end_num):
                # 提取当前处理的编号
                current_num = int(scp_id[4:])  # 去掉 "scp-" 前缀
                
                if failed_count >= max_consecutive_failures:
                    logger.warning(f"连续失败次数达到 {max_consecutive_failures}，停止处理")
                    logger.info(f"当前处理到: {scp_id}")
                    break
                
                # 检查是否需要跳过
                if tracker.should_skip(scp_id):
                    pbar.set_description(f"处理SCP文档 [跳过{scp_id}]")
                    # 对于跳过的项目，如果不是断点接续模式，也需要更新进度条
                    if not args.resume or completed_in_range == 0:
                        pbar.update(1)
                    continue
                    
                success = make_obsidian_md(zim, scp_id)
                
                # 更新进度条描述
                if success:
                    failed_count = 0  # 重置连续失败计数
                    pbar.set_description(f"处理SCP文档 [✓{scp_id}]")
                else:
                    failed_count += 1
                    pbar.set_description(f"处理SCP文档 [✗{scp_id}]")
                
                # 保存当前进度（用于断点接续）
                tracker.save_resume_point(current_num)
                
                # 更新进度条
                pbar.update(1)
                
                # 每处理100个项目打印一次统计
                if tracker.status_data['current_session']['processed'] % 100 == 0:
                    # 暂时停止进度条显示统计
                    pbar.clear()
                    tracker.print_summary()
                    pbar.refresh()
                
                # 每处理10个项目更新进度条后缀信息
                if tracker.status_data['current_session']['processed'] % 10 == 0:
                    stats = tracker.get_statistics()
                    success_rate = stats['success_rate']
                    pbar.set_postfix({
                        '成功': stats['current_session']['successful'],
                        '失败': stats['current_session']['failed'],
                        '成功率': f"{success_rate:.1f}%"
                    })
        
        # 处理完成，打印最终摘要
        tracker.print_summary()
        print_info("处理完成！")
        
        # 如果有失败的项目，提供重试建议
        failed_items = tracker.status_data['failed_items']
        if failed_items:
            print_info(f"有 {len(failed_items)} 个项目处理失败，详细信息请查看: {tracker.failed_file}")
            print_info("可以使用 --resume 参数重新运行程序来继续处理")
            
    except KeyboardInterrupt:
        print_info("用户中断了处理过程")
        print_info("使用 --resume 参数可以从中断点继续处理")
        tracker.print_summary()
    except Exception as e:
        logger.error(f"程序执行过程中发生严重错误: {e}")
        logger.exception("详细错误信息:")
    finally:
        # 确保保存最终状态
        tracker.save_status()
if __name__ == "__main__":
    main()
