#!/usr/bin/env python3
"""
测试 Claude API 连接
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import anthropic

load_dotenv()

# 测试连接
api_key = os.getenv('CLAUDE_API_KEY')
base_url = os.getenv('CLAUDE_API_BASE_URL')

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")

try:
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url
    )

    print("\n尝试发送简单请求...")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=50,
        messages=[
            {
                "role": "user",
                "content": "Hello"
            }
        ]
    )

    print(f"\n✅ API 连接成功!")
    print(f"响应: {message.content[0].text}")

except Exception as e:
    print(f"\n❌ API 连接失败: {e}")
    import traceback
    traceback.print_exc()
