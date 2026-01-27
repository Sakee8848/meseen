import re

def clean_chat_log(raw_text):
    # 去掉 "[2026-01-26 10:00:00] 张三:" 这种头
    clean_text = re.sub(r"\[.*?\] .*?:", "", raw_text)
    # 去掉空行
    return clean_text.strip()