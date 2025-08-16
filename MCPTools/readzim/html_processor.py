"""
HTML 内容处理器
使用 BeautifulSoup 处理 SCP Wiki 的 HTML 内容，提取正文部分
"""

from bs4 import BeautifulSoup, Tag
import re
import os
from typing import Optional, Dict, List, Union


class SCPHtmlProcessor:
    """SCP HTML 内容处理器"""
    
    def __init__(self):
        """
        初始化处理器
        
        Args:
            html_file_path: HTML 文件路径
        """
        self.soup: Optional[BeautifulSoup] = None
        self.content: Optional[str] = None
        

           

    def process_html(self, html_content: str) -> None:
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除不需要的元素
        self._remove_unwanted_elements()
        
        # 提取正文部分
        page_content_div = self.soup.find('div', id='page-content')
        # self.content = page_content_div.get_text() if page_content_div else None
        self.content=str(page_content_div)

    def _remove_unwanted_elements(self):
        """移除不需要的HTML元素"""
        if not self.soup:
            return
            
        # 要移除的元素选择器列表
        unwanted_selectors = [
            # 脚本和样式
            'script',
            'style',
            
            # 导航和菜单
            'nav',
            '.top-bar',
            '.mobile-top-bar',
            '.side-block',
            
            # 页脚和授权信息
            '.footer',
            '.licensebox',
            '#licensebox',
            '.footnotes-footer',
            '.footer-wikiwalk-nav'
            # 其他不需要的元素
            '#skrollr-body',
            'iframe',
            
            # 可折叠块（通常包含不重要信息）
            '.collapsible-block',
            
            # 图片块（如果不需要图片描述）
            # '.scp-image-block',
        ]
        
        for selector in unwanted_selectors:
            elements = self.soup.select(selector)
            for element in elements:
                element.decompose()  # 完全移除元素
    
    def get_clean_text(self) -> Optional[str]:
        """获取清理后的纯文本内容"""
        if not self.content:
            return None
        
        # 进一步清理文本
        text = self.content
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除行首行尾空白
        text = text.strip()
        
        # 移除一些常见的无用文本模式
        unwanted_patterns = [
            r'‡\s*授权\s*/\s*引用.*',  # 授权信息
            r'更多详情请参阅.*',        # 授权指南链接
            r'遵循\s*CC-BY-SA\s*协议.*', # CC协议信息
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        
        return text
        

if __name__ == "__main__":
    processor = SCPHtmlProcessor()
    processor.process_html("<html><body><div id='page-content'>Hello, SCP!</div></body></html>")
    print(processor.content)