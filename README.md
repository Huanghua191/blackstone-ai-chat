# 黑石密码 & 玫瑰与蜂蜜

两个基于 DeepSeek API 的 AI 互动应用，共享同一套 Flask + 原生前端的技术框架。

---

## 项目一：《黑石密码》AI 聊天应用

基于小说《黑石密码》世界观的 AI 互动聊天应用。后端采用 Flask 框架，前端使用原生 HTML/CSS/JavaScript，数据库使用 SQLite 存储多轮对话历史，通过 DeepSeek API 驱动旁白角色扮演。

### 功能特性
- AI 角色扮演：旁白基于《黑石密码》世界观设定，回答风格贴合原著
- 多轮对话记忆：上下文连贯，AI 记住对话历史
- 多会话管理：支持新建、切换、删除独立会话
- 持久化存储：基于 SQLite 数据库，对话历史重启不丢失

### 相关文件
- `app.py` — Flask 后端主程序
- `chat_history.db` — SQLite 对话数据库
- `blackstone_game.html` — 文字冒险游戏完整版（四条分支路线）

---

## 项目二：《玫瑰与蜂蜜》奇幻酒馆经营游戏

一款以奇幻世界为背景的 AI 酒馆经营游戏。玩家扮演意外继承破旧酒馆的老板，接待各类奇幻客人，通过倾听与互动收集配方、提升声望、升级设施。

### 功能特性
- AI 驱动的角色扮演：三位完整事件线客人（熊蜂女王碧翠丝、蛇族药师艾希拉、巫妖检查官莫里斯）+ 三位散客
- 经营数值系统：铜币、声望、配方收集、友谊值、吧台/招牌升级
- 关系记忆：熟客跨天数记忆，不会"第二天就失忆"
- 代答系统：独立的 AI 代答按钮，帮助玩家生成回复
- 存档系统：3 个手动槽位 + 自动存档
- 气氛组：每天角落随机坐着 0-2 位熟客，偶尔搭话但不抢戏
- 离场机制：AI 自行判断对话自然结束时机，通过标签触发天数推进

### 相关文件
- `tavern-game/tavern_game.py` — Flask 后端 + 完整前端（单文件全栈）
- `tavern-game/tavern_events.json` — 事件状态与游戏存档（本地文件，已在 .gitignore 中排除）

---

## 技术栈（两个项目共用）

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask (Python) |
| 前端 | HTML + CSS + JavaScript（原生） |
| 数据库 | SQLite（黑石密码） / JSON 文件存储（玫瑰与蜂蜜） |
| AI 接口 | DeepSeek Chat API |
| 版本管理 | Git + GitHub |

---

## 快速启动

### 《黑石密码》AI 聊天应用

```bash
# 克隆仓库
git clone https://github.com/Huanghua191/blackstone-ai-chat.git
cd blackstone-ai-chat

# 安装依赖
pip install flask requests

# 配置 API Key（环境变量方式）
# Windows: set DEEPSEEK_API_KEY=你的key
# Mac/Linux: export DEEPSEEK_API_KEY='你的key'

# 运行
python app.py

# 浏览器打开 http://127.0.0.1:5000

《玫瑰与蜂蜜》酒馆经营游戏
bash
# 进入酒馆项目目录
cd tavern-game

# 配置 API Key（同上，环境变量方式）

# 运行
python tavern_game.py

# 浏览器打开 http://127.0.0.1:5000

项目关系
两个项目共享同一套 Flask + DeepSeek API 的核心架构。《玫瑰与蜂蜜》是在《黑石密码·兄弟》AI 角色扮演框架的基础上，于 48 小时内完成题材切换和经营系统搭建的。这个过程中验证了该框架的跨题材迁移能力——从暗巷酒吧的冷峻叙事，到奇幻酒馆的温暖治愈，核心架构始终保持稳定。

关于作者
黄桦，广州松田职业学院建筑室内设计专业。室内设计 × 游戏叙事 × AI 应用。

GitHub 主页