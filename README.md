# SCP-Obsidian
将SCP基金会的文档通过AI转换为Obsidian文档，实现SCP基金会全系列的关系图谱
# 概览
1. 当前使用SCP离线计划提供ZIM文档获取SCP文档,后期可能会改为使用爬虫以实现文档动态更新
2. Agent所需的[Prompt.md](/Prompt.md)会不断更新
3. 项目输出的文档于[SCP-Obsidian-Markdown](https://github.com/Lingwuxin/SCP-Obsidian-Markdown)发布
# 方案
## SCP文档来源
[SCP基金会离线计划](https://scp-wiki-cn.wikidot.com/offline) V2，ZIM格式文档。
## 使用的工具
### AI
计划使用LangGraph搭建智能体，LLM提示词见[Prompt.md](/Prompt.md)
### MCP
使用python的`mcp.server.fastmcp`
#### Obsidian-MCP-Server
首先实现以下工具:
- 文档读取
- 双向连接管理
- 标签管理
#### SCP-ZIM-MCP-Server
[SCP-ZIM-MCP-Server](https://github.com/Lingwuxin/SCP-ZIM-MCP-Server)是为了验证该项目的可行性而开发的mcp工具，可以从ZIM文档读取内容，并转换成对应的md文档，现阶段意义不大，已废弃。
