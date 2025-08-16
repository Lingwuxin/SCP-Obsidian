from readzim import ReadZIM
from html_processor import SCPHtmlProcessor
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("read scp zim")

@mcp.tool()
def make_md(zim_file_path, scp_id):
    zim = ReadZIM(zim_file_path)
    zim.read_zim()
    content = zim.get_content(scp_id)
    html_processor = SCPHtmlProcessor()
    if content:
        html_processor.process_html(content)
    if html_processor.content:
        # 在这里生成 Markdown 格式的内容
        md_content = f"# {html_processor.content}"
        with open(f"{scp_id}.md", "w", encoding="utf-8") as f:
            f.write(md_content)
    

if __name__ == "__main__":

    print(make_md(r"D:\VSCode-doc\SCP\scp-wiki_zh_all_2024-10.zim", "scp-001"))
