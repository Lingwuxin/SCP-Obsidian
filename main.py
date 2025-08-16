import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# Dify 配置
dify_config = {
    "base_url": "localhost", # 或者也从环境变量读取
    "agent_api_key": os.getenv("DIFY_AGENT_API_KEY"),
    "datasets_api_key": os.getenv("DIFY_DATASETS_API_KEY"),
}

# SCP 配置
scp_config = {
    "scp_offline_zim_path": os.getenv("SCP_OFFLINE_ZIM_PATH"),
}
