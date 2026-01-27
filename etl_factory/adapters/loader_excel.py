import pandas as pd

def load_excel(file_path):
    # 假设 Excel 里有 "问题" 和 "回答" 两列
    df = pd.read_excel(file_path)
    text_chunks = []
    
    for index, row in df.iterrows():
        # 拼成 AI 能读懂的格式
        content = f"客户咨询：{row['问题']}\n专家回复：{row['回答']}"
        text_chunks.append(content)
        
    return text_chunks # 返回一个列表，每行一个案例