
import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

def test_google_connectivity():
    print("=" * 50)
    print("🧪 Google Gemini API 连通性测试")
    print("=" * 50)

    # 1. 检查 API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 错误: 未能在环境变量中找到 GOOGLE_API_KEY")
        print("   请确保 .env 文件中已正确设置 GOOGLE_API_KEY=your_key_here")
        return

    print(f"✅ 检测到 API Key: {api_key[:8]}******")

    # 2. 初始化模型
    try:
        print("⏳ 正在初始化 ChatGoogleGenerativeAI (gemini-1.5-flash)...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.3,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
    except Exception as e:
        print(f"❌ 初始化模型失败: {e}")
        return

    # 3. 发送测试消息
    try:
        print("🚀 正在发送测试消息: '你好，请用一句话介绍你自己'...")
        messages = [HumanMessage(content="你好，请用一句话介绍你自己")]
        response = llm.invoke(messages)
        
        print("-" * 50)
        print("📝 模型回复:")
        print(response.content)
        print("-" * 50)
        print("✅ 测试成功！Google API 连接正常。")
        
    except Exception as e:
        print("-" * 50)
        print(f"❌ 调用失败: {e}")
        print("\n可能有以下原因:")
        print("1. API Key 无效")
        print("2. 网络连接问题 (你需要能够访问 Google servers)")
        print("3. 该模型版本 (gemini-1.5-flash) 在当前地区不可用")

if __name__ == "__main__":
    test_google_connectivity()
