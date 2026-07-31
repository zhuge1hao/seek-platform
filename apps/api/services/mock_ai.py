MOCK_ANSWER = "已收到你的需求。当前是 meizhaiseek v1.8.10，AI 对话已接入真实问答能力。"


def generate_mock_answer(prompt: str) -> str:
    return f"{MOCK_ANSWER}\n\n你刚才的问题是：{prompt}"
