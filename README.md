# 黑石密码 AI 聊天应用

基于《黑石密码》世界观的 AI 互动聊天应用。后端采用 Flask 框架，前端使用原生 HTML/CSS/JavaScript，数据库使用 SQLite 存储多轮对话历史，通过 DeepSeek API 驱动旁白角色扮演。

## 功能特性

- AI 角色扮演：旁白基于《黑石密码》世界观设定，回答风格贴合原著
- 多轮对话记忆：上下文连贯，AI 记住对话历史
- 多会话管理：支持新建、切换、删除独立会话
- 持久化存储：基于 SQLite 数据库，对话历史重启不丢失

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask (Python) |
| 前端 | HTML + CSS + JavaScript |
| 数据库 | SQLite |
| AI 接口 | DeepSeek Chat API |
| 版本管理 | Git + GitHub |

## 快速启动

1. 克隆仓库
   git clone https://github.com/Huanghua191/blackstone-ai-chat.git

2. 安装依赖
   pip install flask requests

3. 配置 API Key
   打开 app.py，将 YOUR_DEEPSEEK_API_KEY 替换为你的 DeepSeek API Key

4. 运行
   python app.py

5. 打开浏览器访问 http://127.0.0.1:5000