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
        
        # 使用数学计算确定子目录范围
        if 1 <= num <= 10000:
            # 计算范围起始值 (向上取整到千位)
            start = ((num - 1) // 1000) * 1000 + 1
            end = start + 999
            
            # 格式化目录名
            if start == 1:
                return f"001-{end}"
            else:
                return f"{start}-{end}"
        else:
            # 对于超出范围的编号，使用通用目录
            return "other"
            
    except ValueError:
        return "other"
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