import pdfplumber

def load_pdf(file_path):
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
            
    # 简单的切片：按 2000 字切一段
    chunks = [full_text[i:i+2000] for i in range(0, len(full_text), 2000)]
    return chunks