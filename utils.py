import re

def extract_mention(text: str) -> str:
    # 支持 @数字、<@!数字>、@用户昵称 等多种格式
    # 优先提取数字 ID
    match = re.search(r'@(\d+)', text)
    if match:
        return match.group(1)
    match = re.search(r'<@!?(\d+)>', text)
    if match:
        return match.group(1)
    # 如果没有数字，可尝试提取@后的第一个词（但可能不唯一）
    return None