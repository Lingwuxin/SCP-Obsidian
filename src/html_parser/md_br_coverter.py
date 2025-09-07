from markdownify import MarkdownConverter

# 1. 定义自定义转换器，重写<br>处理逻辑
class KeepBrConverter(MarkdownConverter):
    def convert_br(self, el, text, parent_tags):
        """强制保留原始<br>标签，不做转换"""
        return "<br>"  # 直接返回HTML的<br>标签

# 2. 封装便捷转换函数（参考官方示例）
def md_keep_br(html, **options):
    return KeepBrConverter(**options).convert(html)