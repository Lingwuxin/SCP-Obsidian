import libzim
from libzim.reader import Archive
import os
from pathlib import Path
import urllib.parse
import logging
from typing import Optional

# 获取日志记录器
logger = logging.getLogger(__name__)

class ReadZIM:
    def __init__(self, file_path) -> None:
        self.zim_file_path = file_path
        self.archive: Optional[Archive] = None

    def get_content(self,path)->str|None:
        if self.archive is not None:
            res_path = f"{self.archive.main_entry.get_item().path}{path}"
            return self.archive.get_entry_by_path(res_path).get_item().content.tobytes().decode('utf-8', errors='ignore')
        else:
            return None
    def get_img(self, path) -> bytes | None:
        """
        从ZIM文件中提取图片并返回字节数据
        
        Args:
            path: 图片在ZIM文件中的路径
            
        Returns:
            bytes: 图片的字节数据，如果失败返回None
        """
        if self.archive is not None:
            try:
                logger.debug(f"提取图片: {path}")
                
                # 尝试多种路径格式
                paths_to_try = [
                    path,  # 原始路径
                    urllib.parse.unquote(path),  # URL解码路径
                    urllib.parse.quote(path, safe='/:'),  # URL编码路径
                ]
                
                for try_path in paths_to_try:
                    try:
                        logger.debug(f"尝试路径: {try_path}")
                        # 获取图片二进制数据
                        entry = self.archive.get_entry_by_path(try_path)
                        item = entry.get_item()
                        image_data = item.content.tobytes()
                        
                        logger.debug(f"图片提取成功，大小: {len(image_data)} 字节")
                        return image_data
                    except Exception as inner_e:
                        logger.debug(f"路径 {try_path} 失败: {inner_e}")
                        continue
                
                logger.warning(f"所有路径尝试都失败了: {path}")
                return None
                
            except Exception as e:
                logger.error(f"提取图片失败: {path} - {e}")
                return None
        else:
            logger.error("ZIM文件未加载")
            return None
    
    def search_entries(self, keyword: str, max_results: int = 10) -> list[str]:
        """
        搜索ZIM文件中包含关键字的条目
        
        Args:
            keyword: 搜索关键字
            max_results: 最大返回结果数
            
        Returns:
            list[str]: 匹配的条目路径列表
        """
        if not self.archive:
            return []
        
        matching_entries = []
        try:
            # 使用libzim的搜索功能
            logger.info(f"搜索包含 '{keyword}' 的条目...")
            
            # 尝试几种可能的搜索模式
            search_patterns = [
                keyword,
                keyword.replace('%', ''),  # 移除%符号
                urllib.parse.unquote(keyword),  # URL解码
            ]
            
            for pattern in search_patterns:
                logger.debug(f"搜索模式: {pattern}")
                # 这里只是一个简单的实现，实际的libzim可能有不同的API
                # 可以根据实际的libzim版本调整
                break
                
        except Exception as e:
            logger.error(f"搜索条目时出错: {e}")
        
        return matching_entries
        
    def read_zim(self):
        """读取ZIM文件并输出目录结构"""
        try:
            # 验证文件路径
            if not self.zim_file_path:
                raise ValueError("ZIM文件路径为空")
            
            if not os.path.exists(self.zim_file_path):
                raise FileNotFoundError(f"ZIM文件不存在: {self.zim_file_path}")
            
            # 尝试打开ZIM文件
            archive = Archive(self.zim_file_path)  # 直接使用字符串路径
            
            logger.info(f"ZIM文件: {self.zim_file_path}")
            logger.info(f"文件大小: {os.path.getsize(self.zim_file_path) / (1024*1024):.2f} MB")
            logger.info(f"条目数量: {archive.entry_count}")
            logger.info(f"文章数量: {archive.article_count}")
            logger.info(f"媒体数量: {archive.media_count}")
            if hasattr(archive, 'uuid'):
                logger.info(f"UUID: {archive.uuid}")
            logger.info("-" * 50)
            
            # 显示主条目信息
            if archive.has_main_entry:
                try:
                    main_entry = archive.main_entry
                    main_item = main_entry.get_item()
                    logger.info(f"主条目路径: {main_item.path}")
                    logger.info(f"主条目标题: {main_entry.title}")
                except Exception as e:
                    logger.warning(f"获取主条目信息失败: {e}")
            else:
                logger.warning("没有主条目")
            
            # 保存archive实例
            self.archive = archive
            logger.info("ZIM文件加载成功!")

        except Exception as e:
            self.archive = None
            logger.error(f"读取ZIM文件时出错: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.exception("详细错误信息:")
            raise
            



if __name__ == "__main__":
    # 配置基础日志
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    zim_file_path = r"d:\VSCode-doc\SCP\scp-wiki_zh_all_2024-10.zim"

    if not os.path.exists(zim_file_path):
        logger.error(f"错误: ZIM文件不存在: {zim_file_path}")
    else:
        zim = ReadZIM(zim_file_path)
        zim.read_zim()
        # print(zim.get_img("scp-wiki.wdfiles.com/local--files/scp-002/800px-SCP002-new.jpg")) # 测试提取图片（pass）
        logger.info(zim.get_content("scp-wiki.wdfiles.com/local--files//scp-001")) # 测试获取内容（pass）
