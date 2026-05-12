import requests

# 你的 Key
API_KEY = "sk-b76b7aab203848b2a8e9fd4b03c89618"

# API 地址
URL = "https://api.deepseek.com/v1/chat/completions"

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 系统提示词——给 AI 的角色设定
system_prompt = {
    "role": "system",
    "content": (
        "你是《黑石密码》世界里的旁白。"
        "拜勒联邦是一个虚构的资本主义国家，正处于虚假的金融繁荣中，"
        "实体经济已经衰退，失业率飙升，金融危机即将爆发。"
        "主角林奇是一个从底层崛起的年轻人，靠智慧和手段建立了商业帝国。"
        "回答时请基于这个设定，不要引用其他作品。"
    )
}

# 对话历史——保存所有消息，让 AI 有记忆
messages = [system_prompt]

print("=== 《黑石密码》世界对话 ===")
print("（输入 'quit' 或 '退出' 结束对话）\n")

while True:
    # 获取用户输入
    user_input = input("你：")
    
    # 检查是否退出
    if user_input.lower() in ["quit", "退出", "q"]:
        print("\n对话结束。帝国还在转动。")
        break
    
    # 把用户消息加入对话历史
    messages.append({"role": "user", "content": user_input})
    
    # 构建请求体
    data = {
        "model": "deepseek-chat",
        "messages": messages
    }
    
    # 发送请求
    response = requests.post(URL, headers=headers, json=data)
    result = response.json()
    
    # 提取 AI 回复
    reply = result["choices"][0]["message"]["content"]
    
    # 把 AI 回复也加入对话历史，这样下一轮还能记住
    messages.append({"role": "assistant", "content": reply})
    
    # 打印回复
    print(f"旁白：{reply}\n")