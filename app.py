from flask import Flask, request, jsonify, render_template_string
import requests
import sqlite3
import os
import datetime

app = Flask(__name__)

# -------------------- 配置 --------------------
API_KEY = "sk-b76b7aab203848b2a8e9fd4b03c89618"
URL = "https://api.deepseek.com/v1/chat/completions"
DB_FILE = "chat_history.db"

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

# -------------------- 数据库 --------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

# -------------------- 会话管理 --------------------
def create_session(title="新对话"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "created_at": row[2]} for row in rows]

def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def update_session_title(session_id, title):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
    conn.commit()
    conn.close()

# -------------------- 消息管理 --------------------
def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
              (session_id, role, content))
    conn.commit()
    conn.close()

def load_messages(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

# -------------------- 网页模板 --------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>《黑石密码》世界对话</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Georgia", "Noto Serif SC", serif; background: #1a1a1a; color: #e0d6c2; height: 100vh; display: flex; }
        
        /* 侧边栏 */
        #sidebar { width: 260px; background: #111; border-right: 1px solid #2a2a2a; display: flex; flex-direction: column; overflow-y: auto; flex-shrink: 0; }
        #sidebar h3 { padding: 16px; font-size: 15px; color: #f3b33d; border-bottom: 1px solid #2a2a2a; }
        #newChatBtn { margin: 12px; padding: 10px; background: #3e342c; border: 1px solid #5c4e3d; color: #f3b33d; border-radius: 8px; cursor: pointer; font-size: 14px; }
        #sessionList { flex: 1; overflow-y: auto; padding: 8px; }
        .session-item { padding: 10px 12px; margin-bottom: 4px; background: #1a1a1a; border-radius: 8px; cursor: pointer; border: 1px solid transparent; display: flex; justify-content: space-between; align-items: center; }
        .session-item.active { border-color: #f3b33d; }
        .session-item .title { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
        .session-item .del-btn { background: none; border: none; color: #666; cursor: pointer; font-size: 14px; padding: 0 4px; }
        .session-item .del-btn:hover { color: #f33; }
        .session-time { font-size: 11px; color: #666; margin-top: 2px; }
        
        /* 主区域 */
        #main { flex: 1; display: flex; flex-direction: column; }
        #chatBox { flex: 1; overflow-y: auto; padding: 20px; }
        .msg { margin-bottom: 14px; line-height: 1.7; }
        .user { color: #f3b33d; }
        .bot { color: #c0b0a0; }
        .input-area { display: flex; gap: 10px; padding: 14px; background: #111; border-top: 1px solid #2a2a2a; }
        .input-area input { flex: 1; padding: 12px; background: #2a231e; border: 1px solid #5c4e3d; color: #e0d6c2; border-radius: 8px; font-size: 16px; }
        .input-area button { padding: 12px 20px; background: #3e342c; border: 1px solid #5c4e3d; color: #f3b33d; border-radius: 8px; cursor: pointer; }

        @media (max-width: 600px) {
            #sidebar { width: 200px; }
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <h3>📖 对话列表</h3>
        <button id="newChatBtn" onclick="newSession()">+ 新建对话</button>
        <div id="sessionList"></div>
    </div>
    <div id="main">
        <div class="chat-box" id="chatBox"><div class="msg bot">旁白：我是这个世界的旁白。你想了解什么？</div></div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="输入你的问题..." onkeydown="if(event.key==='Enter')send()">
            <button onclick="send()">发送</button>
        </div>
    </div>

    <script>
        let currentSessionId = null;

        async function loadSessions() {
            const res = await fetch('/sessions');
            const data = await res.json();
            const list = document.getElementById('sessionList');
            list.innerHTML = '';
            data.sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = 'session-item' + (s.id === currentSessionId ? ' active' : '');
                item.innerHTML = `<div style="flex:1;overflow:hidden;">
                    <div class="title">${s.title}</div>
                    <div class="session-time">${s.created_at}</div>
                </div>
                <button class="del-btn" data-id="${s.id}">✕</button>`;
                item.addEventListener('click', (e) => {
                    if (e.target.classList.contains('del-btn')) return;
                    switchSession(s.id);
                });
                item.querySelector('.del-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteSession(s.id);
                });
                list.appendChild(item);
            });
        }

        async function switchSession(id) {
            currentSessionId = id;
            const res = await fetch(`/messages/${id}`);
            const data = await res.json();
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML = '';
            if (data.messages.length === 0) {
                chatBox.innerHTML = '<div class="msg bot">旁白：开始一段新的对话吧。</div>';
            } else {
                data.messages.forEach(m => {
                    const cls = m.role === 'user' ? 'user' : 'bot';
                    const prefix = m.role === 'user' ? '你：' : '旁白：';
                    chatBox.innerHTML += `<div class="msg ${cls}">${prefix}${m.content}</div>`;
                });
            }
            loadSessions();
        }

        async function newSession() {
            const res = await fetch('/new_session', { method: 'POST' });
            const data = await res.json();
            currentSessionId = data.session_id;
            document.getElementById('chatBox').innerHTML = '<div class="msg bot">旁白：开始一段新的对话吧。</div>';
            loadSessions();
        }

        async function deleteSession(id) {
            await fetch(`/delete_session/${id}`, { method: 'POST' });
            if (currentSessionId === id) {
                currentSessionId = null;
                document.getElementById('chatBox').innerHTML = '<div class="msg bot">旁白：选择一个对话，或新建一个。</div>';
            }
            loadSessions();
        }

        async function send() {
            if (!currentSessionId) {
                await newSession();
            }

            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;

            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `<div class="msg user">你：${msg}</div>`;
            input.value = '';
            chatBox.innerHTML += `<div class="msg bot" id="loading">旁白：思考中...</div>`;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg, session_id: currentSessionId })
                });
                const data = await res.json();
                document.getElementById('loading').innerHTML = `旁白：${data.reply}`;
            } catch (e) {
                document.getElementById('loading').innerHTML = `旁白：联系不上拜勒联邦...`;
            }
        }

        // 初始化
        (async () => {
            await loadSessions();
            const sessions = await (await fetch('/sessions')).json();
            if (sessions.sessions.length > 0) {
                switchSession(sessions.sessions[0].id);
            }
        })();
    </script>
</body>
</html>
"""

# -------------------- 路由 --------------------
@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/sessions")
def list_sessions():
    return jsonify({"sessions": get_all_sessions()})

@app.route("/new_session", methods=["POST"])
def new_session():
    sid = create_session()
    return jsonify({"session_id": sid})

@app.route("/delete_session/<int:sid>", methods=["POST"])
def del_session(sid):
    delete_session(sid)
    return jsonify({"status": "ok"})

@app.route("/messages/<int:sid>")
def get_messages(sid):
    return jsonify({"messages": load_messages(sid)})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "")
    session_id = data.get("session_id")

    # 保存用户消息
    save_message(session_id, "user", user_msg)

    # 构建 AI 请求
    history = load_messages(session_id)
    messages = [system_prompt] + history

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    body = {
        "model": "deepseek-chat",
        "messages": messages
    }

    try:
        response = requests.post(URL, headers=headers, json=body)
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"抱歉，拜勒联邦的信号不太好..."

    save_message(session_id, "assistant", reply)

    # 自动更新标题
    history_count = len(history)
    if history_count == 0:
        title = user_msg[:20]
        update_session_title(session_id, title)

    return jsonify({"reply": reply})

# -------------------- 启动 --------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)