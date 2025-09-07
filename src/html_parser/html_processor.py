"""
HTML 内容处理器
使用 BeautifulSoup 处理 SCP Wiki 的 HTML 内容，提取正文部分
"""

from bs4 import BeautifulSoup, Tag
import logging
from typing import Optional, Dict, List, Union
from src.html_parser.md_br_coverter import md_keep_br
# 获取日志记录器
logger = logging.getLogger(__name__)


class SCPHtmlProcessor:
    """SCP HTML 内容处理器"""

    def __init__(self, content: str):
        """
        初始化处理器

        Args:
            content: HTML 内容字符串
        """
        self.page_content: str = ""
        self.page_content_div: Optional[Tag] = None
        self.page_tags: list[str] = []
        self.soup: Optional[BeautifulSoup] = None
        if not self._process_html(content):
            logger.error("HTML文档处理失败")
            raise ValueError("获取文档失败")

    def _process_html(self, html_content: str) -> bool:
        '''
        处理HTML内容，移除不需要的元素并提取正文和标签
        Returns:
            bool: 处理是否成功
        '''
        try:
            self.soup = BeautifulSoup(html_content, 'html.parser')

            self._remove_unwanted_elements()
            self.page_content_div = self._extract_content()
            if self.page_content_div is None:
                logger.error("未找到页面内容区域")
                return False
            if self._html_to_markdown(str(self.page_content_div)) == False:
                logger.error("HTML转Markdown失败")
                return False
            self.page_tags = self._extract_and_convert_tags()
            return True

        except Exception as e:
            logger.error(f"处理HTML内容时发生错误: {e}")
            return False

    def _html_to_markdown(self, html: str) -> bool:
        """
        将HTML内容转换为Markdown格式

        Args:
            html: HTML内容字符串

        Returns:
            str: 转换后的Markdown内容
        """
        try:
            # 预处理HTML，将<br>标签替换为换行符
            # 这样markdownify就能正确处理换行

            
            # 使用markdownify转换，配置参数以更好地处理换行和空白
            self.page_content = md_keep_br(
                html, 
                heading_style="ATX",
                
                default_title=True,
                escape_underscores=False
            )
            return True
        except Exception as e:
            logger.error(f"转换HTML为Markdown时发生错误: {e}")
            return False

    def _extract_content(self) -> Optional[Tag]:
        '''
        提取正文内容
        Returns:
            Optional[Tag]: 提取的内容标签，如果提取失败返回None
        '''
        if self.soup:
            # 提取正文部分
            found_content_div = self.soup.find('div', id='page-content')
            if found_content_div and isinstance(found_content_div, Tag):
                logger.debug("成功找到页面内容区域")
                return found_content_div
            else:
                logger.warning("未找到id为'page-content'的div元素")
                return None
        else:
            logger.error("soup对象为空，无法提取内容")
            return None

    def _extract_and_convert_tags(self) -> list[str]:
        """
        提取页面标签并转换为 Obsidian 格式

        Returns:
            list[str]: 转换后的 Obsidian 标签列表
        """
        if not self.soup:
            logger.warning("soup对象为空，无法提取标签")
            return []

        # 查找标签容器
        tags_div = self.soup.find('div', class_='page-tags')
        if not tags_div or not isinstance(tags_div, Tag):
            logger.debug("未找到页面标签区域")
            return []

        # 提取所有标签链接
        tag_links = tags_div.find_all('a')
        obsidian_tags = []

        for link in tag_links:
            if isinstance(link, Tag):
                tag_text = link.get_text(strip=True)
                if tag_text:
                    # 转换为 Obsidian 标签格式
                    obsidian_tag = f"#{tag_text}"
                    obsidian_tags.append(obsidian_tag)

        logger.debug(f"提取到 {len(obsidian_tags)} 个标签: {obsidian_tags}")
        return obsidian_tags

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
            '.footer-wikiwalk-nav',
            'footer-wikiwalk-nav',
            # 其他不需要的元素
            # '#skrollr-body',包含正文
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

    def extract_image_sources(self) -> list[str]:
        """提取图片源路径，不修改HTML结构"""
        if not self.page_content_div:
            logger.warning("页面内容为空，无法提取图片")
            return []

        # 查找所有img标签
        img_tags = []
        if isinstance(self.page_content_div, Tag):
            img_tags = self.page_content_div.find_all('img')

        img_srcs = []
        for img in img_tags:
            if isinstance(img, Tag):  # 确保是Tag对象
                src = img.get('src')
                if src and isinstance(src, str):  # 确保src是字符串
                    # 清理路径，去除相对路径前缀
                    clean_src = src
                    if src.startswith('../'):
                        clean_src = src[3:]  # 移除 "../"
                    elif src.startswith('./'):
                        clean_src = src[2:]  # 移除 "./"
                    img_srcs.append(clean_src)
                    logger.debug(f"找到图片: {clean_src}")
                # 只拿第一个图片
                break

        logger.debug(f"共找到 {len(img_srcs)} 个图片")
        return img_srcs

    def update_image_paths(self, old_src: str, new_src: str) -> None:
        """更新图片路径"""
        if not self.page_content_div:
            logger.warning("页面内容为空，无法更新图片路径")
            return

        if isinstance(self.page_content_div, Tag):
            img_tags = self.page_content_div.find_all('img')
            for img in img_tags:
                if isinstance(img, Tag):
                    src = img.get('src')
                    if src and isinstance(src, str):
                        # 检查是否匹配原始路径
                        clean_src = src
                        if src.startswith('../'):
                            clean_src = src[3:]
                        elif src.startswith('./'):
                            clean_src = src[2:]

                        if clean_src == old_src:
                            img['src'] = new_src
                            logger.debug(f"更新图片路径: {old_src} -> {new_src}")
                            break


if __name__ == "__main__":
    # 配置基础日志
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    processor = SCPHtmlProcessor(
        "<html><body><div id='page-content'>Hello, SCP!</div></body></html>")
    logger.info(f"处理结果: {processor.page_content_div}")
