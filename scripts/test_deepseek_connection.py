#!/usr/bin/env python3
"""
测试 DeepSeek API 连接

使用前请确保:
1. 注册 DeepSeek 账号: https://platform.deepseek.com/
2. 创建 API Key
3. 在 .env 文件中设置 DEEPSEEK_API_KEY
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# 检查 API Key
api_key = os.getenv('DEEPSEEK_API_KEY')

if not api_key or api_key == 'your-deepseek-api-key-here':
    print("❌ 请先在 .env 文件中设置 DEEPSEEK_API_KEY")
    print("\n获取步骤:")
    print("1. 访问: https://platform.deepseek.com/")
    print("2. 注册账号 (支持国内手机号)")
    print("3. 进入控制台创建 API Key")
    print("4. 复制 API Key 并设置到 .env 文件")
    sys.exit(1)

print(f"✅ 已找到 API Key: {api_key[:20]}...")

try:
    from openai import OpenAI

    print("\n🔌 正在连接 DeepSeek API...")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    print("📤 发送测试请求...")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是一个友好的助手。"
            },
            {
                "role": "user",
                "content": "请用一句话介绍你自己。"
            }
        ],
        max_tokens=100,
        temperature=0.7,
    )

    print("\n✅ DeepSeek API 连接成功!")
    print(f"\n📝 响应内容:\n{response.choices[0].message.content}")
    print(f"\n📊 使用情况:")
    print(f"   - Prompt Tokens: {response.usage.prompt_tokens}")
    print(f"   - Completion Tokens: {response.usage.completion_tokens}")
    print(f"   - Total Tokens: {response.usage.total_tokens}")

    print("\n✅ DeepSeek API 工作正常，可以开始生成测试报告了！")
    print("\n💡 使用方法:")
    print("   ./run.sh python scripts/generate_universal_ai_report.py --provider deepseek")

except ImportError:
    print("\n❌ 缺少依赖: 请先安装 openai 库")
    print("运行: ./run.sh pip install openai")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ DeepSeek API 连接失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
