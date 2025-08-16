import libzim
from libzim.reader import Archive
import os
from pathlib import Path


from typing import Optional

class ReadZIM:
    def __init__(self, file_path) -> None:
        self.zim_file_path = file_path
        self.archive: Optional[Archive] = None
    def get_content(self,path)->str|None:
        if self.archive is not None:
            res_path = f"{self.archive.main_entry.get_item().path}{path}"
            print(res_path)
            return self.archive.get_entry_by_path(res_path).get_item().content.tobytes().decode('utf-8', errors='ignore')
        else:
            return None
    
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
            
            print(f"ZIM文件: {self.zim_file_path}")
            print(f"文件大小: {os.path.getsize(self.zim_file_path) / (1024*1024):.2f} MB")
            print(f"条目数量: {archive.entry_count}")
            print(f"文章数量: {archive.article_count}")
            print(f"媒体数量: {archive.media_count}")
            if hasattr(archive, 'uuid'):
                print(f"UUID: {archive.uuid}")
            print("-" * 50)
            
            # 显示主条目信息
            if archive.has_main_entry:
                try:
                    main_entry = archive.main_entry
                    main_item = main_entry.get_item()
                    print(f"主条目路径: {main_item.path}")
                    print(f"主条目标题: {main_entry.title}")
                except Exception as e:
                    print(f"获取主条目信息失败: {e}")
            else:
                print("没有主条目")
            
            # 保存archive实例
            self.archive = archive
            print("ZIM文件加载成功!")

        except Exception as e:
            self.archive = None
            print(f"读取ZIM文件时出错: {e}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            



if __name__ == "__main__":
    zim_file_path = r"d:\VSCode-doc\SCP\scp-wiki_zh_all_2024-10.zim"

    if not os.path.exists(zim_file_path):
        print(f"错误: ZIM文件不存在: {zim_file_path}")
    else:
        zim = ReadZIM(zim_file_path)
        zim.read_zim()
        print(zim.get_content("scp-701"))
