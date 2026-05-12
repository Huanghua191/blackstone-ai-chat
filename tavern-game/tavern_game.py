import requests
import json
import os
import random
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("警告：未设置环境变量 DEEPSEEK_API_KEY，请在终端执行 export DEEPSEEK_API_KEY='你的key' 后再启动")
URL = "https://api.deepseek.com/v1/chat/completions"

SAVES_DIR = "tavern_saves"
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# ========== 世界观（含所有新规则） ==========
TAVERN_WORLD = r"""你是奇幻世界中的一位酒馆客人。你生活在艾尔德兰大陆，这里是各种奇幻生物共同居住的地方。

## 关于这家酒馆
- 酒馆名叫“玫瑰与蜂蜜”，开在灰石镇的橡树广场旁。
- 老板是一个意外继承了这间破酒馆的普通人（就是正在和你对话的玩家）。
- 酒馆刚开张没多久，桌椅还有点晃，但炉火很暖，蜂蜜酒是一绝。
- 来的客人什么样的都有：独眼巨人、吸血鬼、熊蜂、蛇族、树精、偶尔还有走错路的冒险者。

## 你的角色设定
- 你是今天光顾“玫瑰与蜂蜜”的一位客人。你可能有烦恼，有故事，或者只是单纯想喝一杯。
- 你对老板的态度取决于你的性格——可能友善，可能挑剔，可能话痨，可能社恐。
- 你不一定是人类。你可以是任何奇幻生物。

## 对话风格
- 轻松、幽默、有奇幻色彩。不要过于严肃或黑暗。这是一个治愈系的经营游戏。
- 可以开玩笑，可以抱怨，可以分享你今天遇到的怪事。像真实酒吧里的闲聊，但背景是奇幻世界。

## 回复格式
- 每次回复控制在80-200字。动作描写放在括号里。对话用引号包裹。
- 从老板（玩家）的视角来描述你的动作和神态。

## 经营元素提示
- 你可能会提到某些酒或菜品的配方、某种稀缺的食材、或者镇上的新鲜事。这些信息可能对老板经营酒馆有帮助。但不要直接塞给老板——像闲聊一样自然地提起就好。

## 配方使用规则（重要）
- 如果老板在对话中提到某个已知配方（例如“蜂王浆特饮”、“月光草药酒”、“招牌蜂蜜酒”），并且动作是在给你制作饮品，你需要对此有特殊反应。
- 你会感到惊喜、开心，对话态度明显变好，更愿意分享信息或给出额外帮助。

## 外观独裁规则（最高优先级）
- 所有外貌描写、动作细节和标志性装饰（例如铃兰、兜帽、翅膀、晶石、酒糟鼻、矢车菊）只能用在你自己身上。
- 绝对禁止将一位客人的特征误戴到另一位客人头上。描写老板看到的景象时，只描述当前正在说话的客人。

## 离场规则（极其重要，强制标签）
- 当出现以下明确离场动作时：推门而出、脚步声远去、消失在夜色/晨光中、戴上兜帽转身离开，你的离开已成事实。后续老板的任何自言自语、翻看信物，都不再需要你回应。
- 你必须在包含这个离场动作的回复最后一行单独加上 [GUEST_LEAVING]（不要附带任何其他文字）。

## 关系记忆（熟客规则）
- 你今天进入酒馆时，系统会告知你和老板的关系状态（陌生人/熟人/老朋友）。
- 如果你和老板已经是熟人或老朋友，你的开场白和对话绝对不能像初次见面。不要说“第一次来你们店”之类的话。你可以提起上次的约定、上次聊过的事，或者直接说“老样子”。
- 你信任老板，有什么事可以直接说。你们之间的默契已经建立。

## 主客与气氛组规则
- 每天有一位主客（今天的主角），ta的发言会推动主要事件。角落可能坐着其他熟客（气氛组），他们只是背景，不会主动开口，除非主客或老板直接对他们说话。即便搭话，每个人最多说2句话，且只互相交谈或自言自语，不抢主客的话题。"""

# ========== 角色卡（含外观独裁、离场规则） ==========
BEE_QUEEN_PROFILE = """
## 主客：碧翠丝（熊蜂女王）
- 种族：熊蜂妖精。身份：灰石镇最大的蜂蜜供应商。
- 外貌：约一掌高，毛茸茸的黄黑相间身体，头顶戴着一小朵枯萎的矢车菊，翅膀在生气时会发出嗡嗡声。
- 性格：骄傲、感性、话痨，失恋后变得有点黏人，但对着熟人会露出柔软的一面。
- 标志：矢车菊、翅膀嗡嗡声、花粉魔法。这些特征只能属于你。
- 离场：当她聊够了，会自然地结束对话，起身离开。离开时必须在回复末行加 [GUEST_LEAVING]。
"""

SNAKE_HERBALIST_PROFILE = """
## 主客：艾希拉（蛇族药师）
- 种族：蛇族。身份：游方药师。
- 外貌：淡金色竖瞳，鳞片泛珍珠光泽，兜帽边缘沾着干草药。动作慢而精准。
- 性格：安静、专业，对医术话题会突然话多。重情义，但不会表露太多。
- 标志：竖瞳、草药叶、兜帽。这些特征只能属于你。
- 离场：安静戴上兜帽，把酒钱放在吧台上，离开。告别末行加 [GUEST_LEAVING]。
"""

WANDERING_GUESTS_POOL = [
    {
        "name": "老巴索", "emoji": "🍺",
        "profile": "你是老巴索，一个矮人矿工。酒糟鼻，胡子挂霜，性格爽朗话痨。今天刚从矿洞出来。\n标志：酒糟鼻，胡子，腰间的酒壶。只能属于你。\n离场：喝完酒大声道别，末行加 [GUEST_LEAVING]。",
        "opening": "（门铃叮当一响，一个圆滚滚的矮人挤了进来）\"老板！老巴索来暖和暖和！来杯最烈的——要是顺便帮咱擦擦这把镐头，我今儿敲出的晶石送你当桌垫！\""
    },
    {
        "name": "格里姆", "emoji": "🪓",
        "profile": "你是格里姆，独眼巨人木匠。独眼，工装背带裤，说话慢吞吞，手艺极好。\n标志：独眼，粗糙大手，背带裤。只能属于你。\n离场：慢慢起身嘟囔一句明天上工，末行加 [GUEST_LEAVING]。",
        "opening": "（门被一只巨手推开，独眼巨人弯腰挤进来）\"老板……给俺来杯大杯的蜂蜜酒。今天锯了一整天橡木，肩膀跟石头似的。\""
    },
    {
        "name": "奥菲莉亚", "emoji": "🌿",
        "profile": "你是奥菲莉亚，社恐的树精诗人。头顶铃兰花，声音轻，容易害羞，但聊到诗歌会忘紧张。\n标志：铃兰花，指尖微凉。只能属于你。\n离场：写完诗或太紧张时轻声道谢，悄悄离开，末行加 [GUEST_LEAVING]。",
        "opening": "（门被轻轻推开一条缝，纤细的身影闪进来，头顶铃兰花轻颤）\"请、请给我一杯清水……我可以坐在角落里吗？不会打扰任何人的……\""
    }
]

STORY_GUESTS = [
    {"name": "碧翠丝", "emoji": "🐝", "profile": BEE_QUEEN_PROFILE, "type": "story"},
    {"name": "艾希拉", "emoji": "🐍", "profile": SNAKE_HERBALIST_PROFILE, "type": "story"}
]

# 配方库（含触发关键词用于自动解锁）
RECIPES_INFO = {
    "基础蜂蜜酒": {"desc": "招牌饮品，用灰石镇野花蜜酿造，暖身暖心。", "source": "初始", "tip": "对任何客人都不会出错的一杯。", "keywords": []},
    "蜂王浆特饮": {"desc": "碧翠丝的独家秘方，甜到心里，据说能治愈情伤。", "source": "碧翠丝", "tip": "适合失恋的客人，或表达特别善意时。", "keywords": ["蜂王浆", "特饮"]},
    "月光草药酒": {"desc": "艾希拉的安神配方，用月光草浸泡，能驱噩梦。", "source": "艾希拉", "tip": "适合疲惫、焦虑或有睡眠困扰的客人。", "keywords": ["月光草", "草药酒", "安神"]}
}

# ========== 事件文件 ==========
EVENTS_FILE = "tavern_events.json"

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return get_default_events()

def get_default_events():
    return {
        "events": {
            "bee_queen_line": {"stage": "entered", "honey_supply": "stopped", "friendship": 0},
            "snake_herbalist_line": {"stage": "entered", "friendship": 0, "ointment_given": False, "recipe_shared": False},
            "health_inspector_line": {"stage": "not_mentioned", "soup_offered": 0, "friendship": 0},
            "rival_bar_line": {"stage": "not_mentioned"}
        },
        "tavern_state": {
            "day": 1,
            "revenue": 0,
            "recipes": ["基础蜂蜜酒"],
            "reputation": 10,
            "current_guest": "艾希拉",
            "current_guest_emoji": "🐍",
            "upgrades": {"bar_counter": 0, "signboard": 0},
            "conversation_rounds": 0,
            "atmosphere_guests": [],
            "guest_lines_left": {}
        },
        "chat_history": [],
        "event_log": ["一位披着斗篷的旅人推开酒馆的门，铃铛轻轻响了一声。她摘下兜帽，露出淡金色的竖瞳——是蛇族。"]
    }

def save_events(data):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_event_log(events_data, log_entry):
    events_data["event_log"].append(log_entry)
    events_data["event_log"] = events_data["event_log"][-10:]
    return events_data

# ========== 存档系统 ==========
def get_save_info(slot):
    filename = "autosave.json" if slot == "autosave" else f"slot_{slot}.json"
    filepath = os.path.join(SAVES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {"slot": str(slot), "day": data.get("tavern_state", {}).get("day", "?"),
                "revenue": data.get("tavern_state", {}).get("revenue", 0),
                "recipes_count": len(data.get("tavern_state", {}).get("recipes", [])),
                "reputation": data.get("tavern_state", {}).get("reputation", 0),
                "guest": data.get("tavern_state", {}).get("current_guest", "?"),
                "timestamp": data.get("save_timestamp", "未知时间")}
    return None

def save_to_slot(slot, events_data):
    events_data["save_timestamp"] = datetime.now().strftime("%m-%d %H:%M")
    filename = "autosave.json" if slot == "autosave" else f"slot_{slot}.json"
    filepath = os.path.join(SAVES_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)

def load_from_slot(slot):
    filename = "autosave.json" if slot == "autosave" else f"slot_{slot}.json"
    filepath = os.path.join(SAVES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def autosave(events_data):
    events_data["save_timestamp"] = datetime.now().strftime("%m-%d %H:%M") + " (自动)"
    save_to_slot("autosave", events_data)

# ========== 前端 HTML（完整版，包含所有弹窗和逻辑） ==========
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>玫瑰与蜂蜜 · 奇幻酒馆经营</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#faf8f5;color:#3d2e2e;height:100vh;display:flex;justify-content:center;align-items:center}
.game-container{width:800px;height:90vh;max-height:700px;background:#fffdf9;border-radius:8px;border:1.5px solid #e8c4c4;display:flex;flex-direction:column;overflow:hidden;position:relative;box-shadow:0 2px 20px rgba(180,100,100,0.08)}
.header{padding:18px 24px 12px;border-bottom:1px solid #f0d8d8;display:flex;align-items:center;justify-content:space-between}
.header-left h2{font-size:20px;font-weight:500;color:#b84747;letter-spacing:1px;margin:0}
.header-left .subtitle{font-size:12px;color:#c49b9b;margin-top:4px}
.header-right{display:flex;gap:8px}
.header-right button{background:none;border:1px solid #e0c0c0;color:#b87070;padding:4px 14px;font-size:12px;font-family:inherit;cursor:pointer;border-radius:14px;transition:all .2s}
.header-right button:hover{background:#fdf0f0;border-color:#c49b9b}
.status-bar{display:flex;gap:8px;padding:10px 24px;background:#fff8f6;border-bottom:1px solid #f5e0e0;font-size:12px;color:#8b6b6b;flex-wrap:wrap}
.status-bar span{display:flex;align-items:center;gap:4px;cursor:pointer;padding:2px 8px;border-radius:12px;transition:background .2s}
.status-bar span:hover{background:#fce8e8}
.chat-box{flex:1;padding:20px 24px;overflow-y:auto;line-height:1.8;background:#fffdf9}
.chat-box::-webkit-scrollbar{width:4px}
.chat-box::-webkit-scrollbar-track{background:#fff8f6}
.chat-box::-webkit-scrollbar-thumb{background:#e8c4c4;border-radius:2px}
.msg{margin-bottom:18px;max-width:82%;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg.guest{margin-right:auto;padding:10px 14px;background:#fff5f5;border-radius:6px 18px 18px 18px;border:1px solid #fce8e8;color:#5c3d3d}
.msg.guest .speaker{font-size:11px;color:#c49b9b;margin-bottom:4px;letter-spacing:.5px}
.msg.player{margin-left:auto;text-align:right;padding:10px 14px;background:#fdf8f8;border-radius:18px 6px 18px 18px;border:1px solid #f0d8d8;color:#8b4a4a}
.msg.player .speaker{font-size:11px;color:#c49b9b;margin-bottom:4px;letter-spacing:.5px}
.msg.narration{text-align:center;max-width:90%;margin-left:auto;margin-right:auto;padding:12px 20px;background:transparent;border:none;color:#8b6b6b;font-style:italic;font-size:13px;line-height:1.8}
.msg.atmosphere{opacity:0.8;font-style:italic;border-left:2px dashed #e8c4c4;padding-left:8px}
.input-area{display:flex;flex-direction:column;padding:12px 24px 16px;border-top:1px solid #f0d8d8;background:#fffdf9;position:relative}
.input-hint{font-size:11px;color:#c49b9b;margin-bottom:6px;padding-left:4px}
.input-row{display:flex;gap:0;align-items:flex-end}
.input-row textarea{flex:1;padding:12px 16px;background:#fffdf9;border:1.5px solid #e8c4c4;color:#5c3d3d;font-size:14px;font-family:inherit;border-radius:20px;outline:none;resize:none;min-height:44px;max-height:100px;line-height:1.5}
.input-row textarea:focus{border-color:#c49b9b}
.input-row button{padding:12px 24px;background:#b84747;border:none;color:#fff;font-size:13px;font-family:inherit;cursor:pointer;border-radius:20px;margin-left:8px;letter-spacing:.5px;white-space:nowrap;align-self:flex-end;transition:all .2s}
.input-row button:hover{background:#a03a3a}
.auto-btn{padding:12px 16px;background:#fff5f5;border:1.5px solid #e8c4c4;color:#b87070;font-size:18px;font-family:inherit;cursor:pointer;border-radius:20px;margin-left:0;margin-right:8px;transition:all .2s;white-space:nowrap;align-self:flex-end}
.auto-btn:hover{background:#fdf0f0;border-color:#c49b9b}
.next-day-bubble{position:absolute;top:-45px;left:50%;transform:translateX(-50%);background:#b84747;color:#fff;padding:8px 20px;border-radius:20px;font-size:13px;cursor:pointer;box-shadow:0 2px 10px rgba(180,100,100,0.3);display:none;z-index:10;white-space:nowrap}
.next-day-bubble.show{display:block}
.event-log{position:absolute;bottom:80px;right:16px;width:200px;background:rgba(255,253,249,.95);border:1.5px solid #e8c4c4;border-radius:8px;padding:12px;font-size:11px;color:#8b6b6b;max-height:120px;overflow-y:auto;display:none;box-shadow:0 2px 10px rgba(180,100,100,0.08)}
.event-log.show{display:block}
.event-log .log-title{color:#b84747;margin-bottom:6px;letter-spacing:1px;font-size:10px}
.event-log .log-item{margin-bottom:4px;line-height:1.4}
.toggle-log{position:absolute;bottom:82px;right:16px;background:none;border:none;color:#c49b9b;cursor:pointer;font-size:11px;font-family:inherit;z-index:10}
.toggle-log:hover{color:#b84747}
.save-overlay,.upgrade-overlay,.recipe-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.3);z-index:200;display:flex;justify-content:center;align-items:center;display:none}
.save-overlay.show,.upgrade-overlay.show,.recipe-overlay.show{display:flex}
.save-box,.upgrade-box,.recipe-box{background:#fffdf9;border:1.5px solid #e8c4c4;border-radius:12px;padding:24px;width:380px;max-width:90%;box-shadow:0 4px 30px rgba(180,100,100,0.15);position:relative;max-height:80vh;overflow-y:auto}
.save-box h3,.upgrade-box h3,.recipe-box h3{color:#b84747;font-weight:500;font-size:18px;margin-bottom:16px;text-align:center}
.recipe-item{padding:10px;border-bottom:1px solid #f5e0e0;margin-bottom:8px}
.recipe-item strong{color:#b84747}
.recipe-item span{display:block;font-size:12px;color:#8b6b6b;margin-top:4px}
.upgrade-item,.save-slot{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;margin-bottom:8px;background:#fffaf8;border:1px solid #f0d8d8;border-radius:8px;font-size:13px;color:#5c3d3d}
.upgrade-item button{padding:6px 14px;border-radius:12px;border:none;background:#b84747;color:#fff;cursor:pointer;font-size:11px;font-family:inherit;margin-left:4px}
.upgrade-item button.done{background:#c49b9b;cursor:default}
.save-slot button{padding:6px 14px;border-radius:12px;border:1px solid #e0c0c0;background:#fff;color:#b87070;cursor:pointer;font-size:11px;font-family:inherit;margin-left:4px}
.save-slot button.save-btn{background:#b84747;color:#fff;border:none}
.save-close,.upgrade-close,.recipe-close{display:block;margin:16px auto 0;padding:8px 20px;background:none;border:1px solid #e0c0c0;color:#b87070;border-radius:14px;cursor:pointer;font-size:12px;font-family:inherit}
@media screen and (max-width: 600px) {
  .game-container{width:100%;height:100vh;max-height:none;border-radius:0;border:none;box-shadow:none}
  .header{padding:10px 12px 8px}
  .header-left h2{font-size:17px}
  .status-bar{padding:8px 12px;gap:6px;font-size:10px}
  .chat-box{padding:14px}
  .input-area{padding:8px 12px 10px}
}
</style>
</head>
<body>
<div class="game-container">
<div class="header">
  <div class="header-left">
    <h2>🌹 玫瑰与蜂蜜</h2>
    <div class="subtitle">灰石镇 · 橡树广场旁 · 你的小酒馆</div>
  </div>
  <div class="header-right">
    <button onclick="openSaveMenu()">💾 存档</button>
    <button onclick="openUpgradeMenu()">🏠 升级</button>
    <button onclick="resetStory()">新开一局</button>
    <button onclick="showIntro()">酒馆故事</button>
  </div>
</div>
<div class="status-bar" id="statusBar">
  <span onclick="alert('📅 经营天数：每天可接待一位主要客人。')">📅 第1天</span>
  <span onclick="alert('💰 铜币：完成客人心愿、升级设施获得，可用于吧台与招牌升级。')">💰 0 铜币</span>
  <span onclick="alert('⭐ 声望：越高越容易吸引稀有客人，升级招牌可大幅提升。')">⭐ 声望 10</span>
  <span onclick="openRecipeBook()">📜 配方 1</span>
</div>
<div class="chat-box" id="chatBox">
  <div class="msg guest"><div class="speaker">🐍 艾希拉</div>（一位披着斗篷的旅人推开酒馆的门，铃铛轻轻响了一声。她摘下兜帽，露出淡金色的竖瞳和沾着草药叶的头发。她在吧台前坐下，动作慢而精准。）"温一杯酒吧。天凉了。我叫艾希拉，是个游方药师。"</div>
</div>
<div class="input-area">
  <div class="next-day-bubble" id="nextDayBubble" onclick="nextDay()">🌅 客人已离去，开始下一天</div>
  <div class="input-hint">💬 跟客人聊聊吧 · 动作用括号 · 🌹 点玫瑰帮答 · 输入（等待）直接结束一天</div>
  <div class="input-row">
    <button class="auto-btn" id="autoBtn" onclick="autoReply()">🌹</button>
    <textarea id="userInput" placeholder="你好，欢迎光临玫瑰与蜂蜜..." rows="1" oninput="this.style.height='';this.style.height=Math.min(this.scrollHeight,100)+'px'"></textarea>
    <button onclick="send()">发送</button>
  </div>
</div>
<button class="toggle-log" onclick="toggleLog()">📋 日志</button>
<div class="event-log" id="eventLog"><div class="log-title">最近发生的事</div><div class="log-item">艾希拉推开酒馆的门。</div></div>
</div>
<div class="save-overlay" id="saveOverlay" onclick="if(event.target===this) closeSaveMenu()">
  <div class="save-box" onclick="event.stopPropagation()">
    <h3>💾 管理存档</h3><div id="saveSlots">加载中...</div>
    <button class="save-close" onclick="closeSaveMenu()">关闭</button>
  </div>
</div>
<div class="upgrade-overlay" id="upgradeOverlay" onclick="if(event.target===this) closeUpgradeMenu()">
  <div class="upgrade-box" onclick="event.stopPropagation()">
    <h3>🏠 酒馆升级</h3><div id="upgradeItems">加载中...</div>
    <button class="upgrade-close" onclick="closeUpgradeMenu()">关闭</button>
  </div>
</div>
<div class="recipe-overlay" id="recipeOverlay" onclick="if(event.target===this) closeRecipeBook()">
  <div class="recipe-box" onclick="event.stopPropagation()">
    <h3>📜 配方书</h3><div id="recipeList">加载中...</div>
    <button class="recipe-close" onclick="closeRecipeBook()">关闭</button>
  </div>
</div>
<script>
var currentGuest = { name: '艾希拉', emoji: '🐍' };
var tavernUpgrades = { bar_counter: 0, signboard: 0 };
var guestLeftToday = false;

function addMessage(role, text, guestName, guestEmoji, isNarration){
    var chatBox=document.getElementById('chatBox');
    var msgDiv=document.createElement('div');
    if(isNarration){
        msgDiv.className='msg narration';
        msgDiv.innerHTML='<div>'+text+'</div>';
    } else if(role==='atmosphere'){
        msgDiv.className='msg guest atmosphere';
        var sDiv=document.createElement('div'); sDiv.className='speaker';
        sDiv.textContent=(guestEmoji||'')+' '+(guestName||'');
        var cDiv=document.createElement('div'); cDiv.textContent=text;
        msgDiv.appendChild(sDiv); msgDiv.appendChild(cDiv);
    } else {
        msgDiv.className='msg '+role;
        var speakerDiv=document.createElement('div'); speakerDiv.className='speaker';
        if(role==='guest'){
            // 优先使用传入的名字，若无则用全局（但全局可能已更新）
            var displayName = guestName || currentGuest.name;
            var displayEmoji = guestEmoji || currentGuest.emoji;
            // 兜底：如果还是没有名字，就用通用的 😎 客人
            if(!displayName) {
                displayName = '客人';
                displayEmoji = '😎';
            }
            speakerDiv.textContent = displayEmoji + ' ' + displayName;
        } else {
            speakerDiv.textContent='🧑‍🍳 老板';
        }
        var contentDiv=document.createElement('div'); contentDiv.textContent=text;
        msgDiv.appendChild(speakerDiv); msgDiv.appendChild(contentDiv);
    }
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop=chatBox.scrollHeight;
    return msgDiv;
}

function send(){
    var input=document.getElementById('userInput'); var msg=input.value.trim(); if(!msg)return;
    addMessage('player', msg); input.value=''; input.style.height='';
    var loadingDiv=addMessage('guest', '...'); var dotInterval=setInterval(function(){
        var dots=loadingDiv.querySelector('div:last-child');
        if(dots) dots.textContent='...'.substring(0,((dots.textContent.length)%4));
    },300);
    fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})})
    .then(r=>r.json()).then(data=>{
        clearInterval(dotInterval); loadingDiv.remove();
        if(data.narration){
            addMessage('narration', data.narration_text, null, null, true);
            if(data.current_guest) currentGuest = data.current_guest;
            if(data.event_log) updateEventLog(data.event_log);
            if(data.tavern_state) updateStatusBar(data.tavern_state);
            if(data.upgrades) tavernUpgrades = data.upgrades;
            if(data.opening) addMessage('guest', data.opening, data.current_guest?.name, data.current_guest?.emoji);
            document.getElementById('nextDayBubble').classList.remove('show');
            guestLeftToday = false;
        } else {
            if(data.current_guest) currentGuest = data.current_guest;
            if(data.event_log) updateEventLog(data.event_log);
            if(data.tavern_state) updateStatusBar(data.tavern_state);
            if(data.upgrades) tavernUpgrades = data.upgrades;
            if(data.guest_left){
                addMessage('guest', data.reply);
                document.getElementById('nextDayBubble').classList.add('show');
                guestLeftToday = true;
            } else {
                addMessage('guest', data.reply);
                if(data.atmosphere_lines && data.atmosphere_lines.length){
                    data.atmosphere_lines.forEach(function(line){
                        addMessage('atmosphere', line.text, line.name, line.emoji);
                    });
                }
            }
        }
    }).catch(e=>{ clearInterval(dotInterval); loadingDiv.remove(); addMessage('guest','...（似乎走神了）'); });
}

function nextDay(){
    var input=document.getElementById('userInput'); input.value='（等待）'; send();
}

function updateEventLog(logs){
    var logDiv=document.getElementById('eventLog');
    var html='<div class="log-title">最近发生的事</div>';
    if(logs&&logs.length>0){
        logs.slice(-5).reverse().forEach(function(log){html+='<div class="log-item">'+log+'</div>';});
    }else{ html+='<div class="log-item">酒馆里安安静静的。</div>'; }
    logDiv.innerHTML=html;
}

function updateStatusBar(state){
    if(state){
        document.getElementById('statusBar').innerHTML=
            '<span onclick="alert(\'经营天数：每天可接待一位主要客人。\')">📅 第'+state.day+'天</span>'+
            '<span onclick="alert(\'铜币：完成客人心愿、升级设施获得。可用于吧台与招牌升级。\')">💰 '+state.revenue+' 铜币</span>'+
            '<span onclick="alert(\'声望：越高越容易吸引稀有客人，升级招牌可大幅提升。\')">⭐ 声望 '+state.reputation+'</span>'+
            '<span onclick="openRecipeBook()" style="cursor:pointer;">📜 配方 '+state.recipes.length+'</span>';
    }
}

function toggleLog(){document.getElementById('eventLog').classList.toggle('show');}

function resetStory(){
    if(confirm('确定要重新开始吗？当前进度将丢失。建议先存档。')){
        fetch('/reset',{method:'POST'}).then(function(){ location.reload(); }).catch(function(){alert('重置失败');});
    }
}

function showIntro(){alert('🌹 玫瑰与蜂蜜\n\n你继承了灰石镇的这家小酒馆。倾听奇幻客人的故事，收集奇怪配方。');}

function openSaveMenu(){ document.getElementById('saveOverlay').classList.add('show'); refreshSaveSlots(); }
function closeSaveMenu(){ document.getElementById('saveOverlay').classList.remove('show'); }

function refreshSaveSlots(){
    fetch('/get_saves').then(function(res){return res.json();}).then(function(data){
        var slotsDiv=document.getElementById('saveSlots');
        var html='';
        var auto=data.auto;
        if(auto){ html+='<div class="save-slot"><span>🟢 自动存档</span><span class="slot-info">第'+auto.day+'天 · '+auto.revenue+'铜币 · '+auto.timestamp+'</span><button onclick="loadSlot(0)">读取</button></div>'; }
        else{ html+='<div class="save-slot"><span>🟢 自动存档</span><span class="slot-info">空</span><span>暂无</span></div>'; }
        for(var i=1;i<=3;i++){
            var slot=data['slot_'+i];
            html+='<div class="save-slot"><span>📁 存档 '+i+'</span><span class="slot-info">'+(slot ? '第'+slot.day+'天 · '+slot.revenue+'铜币 · '+slot.timestamp : '空槽位')+'</span><button class="save-btn" onclick="saveSlot('+i+')">保存</button>';
            if(slot){ html+='<button onclick="loadSlot('+i+')">读取</button>'; }
            html+='</div>';
        }
        slotsDiv.innerHTML=html;
    }).catch(function(){ document.getElementById('saveSlots').innerHTML='加载失败'; });
}

function saveSlot(slot){
    fetch('/save/'+slot,{method:'POST'}).then(function(res){return res.json();}).then(function(data){
        if(data.status==='ok'){ closeSaveMenu(); alert('✅ 已保存到存档 '+slot); }
    }).catch(function(){alert('保存失败');});
}

function loadSlot(slot){
    var slotParam = slot === 0 ? 'autosave' : slot;
    var displayName = slot === 0 ? '自动存档' : '存档 '+slot;
    if(confirm('确定要读取' + displayName + '吗？当前未保存的进度将丢失。')){
        fetch('/load/'+slotParam,{method:'POST'}).then(function(res){return res.json();}).then(function(data){
            if(data.status==='ok'){
                sessionStorage.setItem('restored_chat_history', JSON.stringify(data.chat_history));
                if(data.current_guest){ sessionStorage.setItem('restored_guest', JSON.stringify(data.current_guest)); }
                alert('✅ ' + displayName + '已读取，页面将刷新。'); location.reload();
            }else{ alert('读取失败：'+data.msg); }
        }).catch(function(){alert('读取失败');});
    }
}

function autoReply(){
    var autoBtn=document.getElementById('autoBtn'); autoBtn.disabled=true; autoBtn.textContent='...';
    var chatBox=document.getElementById('chatBox'); var messages=chatBox.querySelectorAll('.msg'); var chatLog=[];
    messages.forEach(function(msg){
        if(msg.classList.contains('guest')){ chatLog.push({role:'assistant',content:msg.querySelector('div:last-child').textContent}); }
        else if(msg.classList.contains('player')){ chatLog.push({role:'user',content:msg.querySelector('div:last-child').textContent}); }
    });
    fetch('/auto_reply',{
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({chat_log:chatLog, guest_name: currentGuest.name, guest_emoji: currentGuest.emoji})
    }).then(function(res){return res.json();}).then(function(data){
        var input=document.getElementById('userInput'); input.value=data.reply; input.focus();
        input.style.height=''; input.style.height=Math.min(input.scrollHeight,100)+'px';
    }).catch(function(e){console.log('代答出错:',e);});
    autoBtn.disabled=false; autoBtn.textContent='🌹';
}

function openUpgradeMenu(){ document.getElementById('upgradeOverlay').classList.add('show'); refreshUpgradeItems(); }
function closeUpgradeMenu(){ document.getElementById('upgradeOverlay').classList.remove('show'); }

function refreshUpgradeItems(){
    fetch('/get_upgrades').then(function(res){return res.json();}).then(function(data){
        var div=document.getElementById('upgradeItems');
        var u=data.upgrades; var revenue=data.revenue; var html='';
        ['bar_counter','signboard'].forEach(function(key){
            var item=data.items[key]; var currentLevel=u[key]||0; var cost=item.cost*(currentLevel+1);
            var maxed=currentLevel>=item.max_level;
            var desc=item.description+(maxed?' (已满级)':' ('+cost+'铜币)');
            var btn=maxed?'<button class="done">已满级</button>':
                (revenue>=cost?'<button onclick="doUpgrade(\''+key+'\','+cost+')">升级</button>':
                '<button disabled style="opacity:0.5">铜币不足</button>');
            html+='<div class="upgrade-item"><span>'+item.icon+' '+item.name+' Lv.'+currentLevel+'</span><span class="upgrade-info">'+desc+'</span>'+btn+'</div>';
        });
        div.innerHTML=html;
    });
}

function doUpgrade(upgradeKey, cost){
    fetch('/upgrade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({upgrade: upgradeKey, cost: cost})})
    .then(function(res){return res.json();}).then(function(data){
        if(data.status==='ok'){
            alert('✅ '+data.message);
            updateStatusBar(data.tavern_state); tavernUpgrades = data.upgrades;
            refreshUpgradeItems();
        }else{ alert('升级失败：'+data.msg); }
    }).catch(function(){alert('升级失败');});
}

function openRecipeBook(){
    document.getElementById('recipeOverlay').classList.add('show');
    fetch('/get_recipes').then(r=>r.json()).then(data=>{
        var html='';
        data.recipes.forEach(function(r){
            html+='<div class="recipe-item"><strong>'+r.name+'</strong><span>来源：'+r.source+'</span><span>'+r.desc+'</span><span>💡 '+r.tip+'</span></div>';
        });
        document.getElementById('recipeList').innerHTML=html||'暂无配方';
    });
}
function closeRecipeBook(){ document.getElementById('recipeOverlay').classList.remove('show'); }

// 页面初始化恢复存档聊天
window.addEventListener('DOMContentLoaded', function(){
    var restored = sessionStorage.getItem('restored_chat_history');
    var restoredGuest = sessionStorage.getItem('restored_guest');
    if(restoredGuest){ try{ currentGuest = JSON.parse(restoredGuest); sessionStorage.removeItem('restored_guest'); }catch(e){} }
    if(restored){
        try{
            var history = JSON.parse(restored); var chatBox = document.getElementById('chatBox'); chatBox.innerHTML = '';
            history.forEach(function(msg){
                if(msg.role === 'user'){ addMessage('player', msg.content); }
                else if(msg.role === 'assistant'){
                    addMessage('guest', msg.content);
                }
            });
            sessionStorage.removeItem('restored_chat_history');
        }catch(e){ console.log('恢复对话历史失败:', e); }
    }
});

fetch('/events').then(function(res){return res.json();}).then(function(data){
    if(data.event_log&&data.event_log.length>0){ updateEventLog(data.event_log); }
    if(data.tavern_state){
        updateStatusBar(data.tavern_state);
        if(data.tavern_state.current_guest){ currentGuest = { name: data.tavern_state.current_guest, emoji: data.tavern_state.current_guest_emoji || '🐝' }; }
        if(data.tavern_state.upgrades){ tavernUpgrades = data.tavern_state.upgrades; }
    }
});
</script>
</body>
</html>"""

# ========== 后端路由 ==========
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/events")
def get_events():
    return jsonify(load_events())

@app.route("/reset", methods=["POST"])
def reset():
    save_events(get_default_events())
    return jsonify({"status": "ok"})

@app.route("/get_saves")
def get_saves():
    result = {}; result["auto"] = get_save_info("autosave")
    for i in range(1, 4): result[f"slot_{i}"] = get_save_info(i)
    return jsonify(result)

@app.route("/save/<int:slot>", methods=["POST"])
def save_game(slot):
    if slot < 1 or slot > 3: return jsonify({"status": "error", "msg": "槽位号必须为1-3"})
    save_to_slot(slot, load_events())
    return jsonify({"status": "ok"})

@app.route("/load/<slot>", methods=["POST"])
def load_game(slot):
    if slot == "0" or slot == 0: slot = "autosave"
    data = load_from_slot(slot if slot == "autosave" else int(slot))
    if data:
        save_events(data)
        return jsonify({"status": "ok", "chat_history": data.get("chat_history", []),
            "current_guest": {"name": data["tavern_state"]["current_guest"], "emoji": data["tavern_state"]["current_guest_emoji"]}})
    return jsonify({"status": "error", "msg": "存档不存在"})

@app.route("/get_recipes")
def get_recipes_route():
    events = load_events()
    recipes = events["tavern_state"]["recipes"]
    result = []
    for r in recipes:
        info = RECIPES_INFO.get(r, {"desc": "一种神秘的饮品。", "source": "未知", "tip": "尝试在对话中使用。"})
        result.append({"name": r, "desc": info["desc"], "source": info["source"], "tip": info["tip"]})
    return jsonify({"recipes": result})

@app.route("/auto_reply", methods=["POST"])
def auto_reply():
    data = request.get_json(); chat_log = data.get("chat_log", [])
    guest_name = data.get("guest_name", "碧翠丝")
    prompt = "你是酒馆老板，温和幽默。基于客人最新话回应，不超过30字。"
    conversation = [{"role": "system", "content": prompt}]
    if chat_log:
        dialog = [m for m in chat_log if m["role"] in ("user", "assistant")][:-1]
        if dialog:
            for m in dialog[-8:]:
                role = "老板说" if m["role"] == "user" else f"{guest_name}说"
                conversation.append({"role": "user", "content": f"{role}：{m['content']}"})
    target = None
    for m in reversed(chat_log):
        if m["role"] == "assistant": target = m["content"]; break
    if target:
        conversation.append({"role": "user", "content": f"（{guest_name}刚说完）{guest_name}：{target}"})
    else:
        conversation.append({"role": "user", "content": f"{guest_name}走进酒馆，请回应。"})
    conversation.append({"role": "user", "content": f"请以老板身份回应{guest_name}。"})
    try:
        resp = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}"}, json={"model": "deepseek-chat", "messages": conversation})
        reply = resp.json()["choices"][0]["message"]["content"]
    except: reply = '"请稍等。"'
    return jsonify({"reply": reply})

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    events_data = load_events()
    state = events_data["tavern_state"]

    # 处理等待指令
    if user_msg.strip().startswith("（等待") or user_msg.strip().startswith("（结束营业"):
        state["day"] += 1
        state["conversation_rounds"] = 0
        state["revenue"] += 20
        events_data = add_event_log(events_data, "💰 一天结束，收入20铜币。")

        # 构建客人池
        all_guests = list(STORY_GUESTS)
        for w in WANDERING_GUESTS_POOL:
            all_guests.append({"name": w["name"], "emoji": w["emoji"], "profile": w["profile"], "opening": w.get("opening", ""), "type": "wandering"})
        if state["upgrades"]["signboard"] >= 1:
            all_guests.append({"name": "莫里斯", "emoji": "💀", "profile": "你是莫里斯，巫妖卫生检查官。\n标志：骨手，老花镜，魂火。只能属于你。\n离场：检查完离开加 [GUEST_LEAVING]。",
                               "opening": "（门被一只骨手礼貌推开）\"下午好，老板。例行卫生检查。\"", "type": "special"})
        new_guest = random.choice(all_guests)
        state["current_guest"] = new_guest["name"]
        state["current_guest_emoji"] = new_guest["emoji"]

        # 随机气氛组
        possible_atmo = [g for g in all_guests if g["name"] != new_guest["name"]]
        atmo = random.sample(possible_atmo, k=min(2, len(possible_atmo)))
        state["atmosphere_guests"] = [{"name": a["name"], "emoji": a["emoji"], "lines_left": 2} for a in atmo]
        state["guest_lines_left"] = {a["name"]: 2 for a in atmo}

        events_data = add_event_log(events_data, f"🌅 第{state['day']}天，{new_guest['name']}走进了酒馆。")
        narration = "（夜深了，炉火熄灭。第二天清晨的阳光洒在地板上，铃铛响起——新的客人推门而入。）"
        opening_line = new_guest.get("opening", "（客人走进来）\"早上好，老板。\"")
        events_data["chat_history"].append({"role": "user", "content": user_msg})
        events_data["chat_history"].append({"role": "assistant", "content": narration})
        events_data["chat_history"].append({"role": "assistant", "content": opening_line, "guest_name": new_guest["name"], "guest_emoji": new_guest["emoji"]})
        events_data["chat_history"] = events_data["chat_history"][-20:]
        autosave(events_data); save_events(events_data)
        return jsonify({"narration": True, "narration_text": narration, "opening": opening_line, "event_log": events_data["event_log"], "tavern_state": state, "current_guest": {"name": new_guest["name"], "emoji": new_guest["emoji"]}, "upgrades": state["upgrades"]})

    # 普通对话
    guest_name = state["current_guest"]
    guest_emoji = state["current_guest_emoji"]
    guest_profile = BEE_QUEEN_PROFILE  # 默认
    # 查找角色卡（包括故事客人和散客）
    for g in STORY_GUESTS:
        if g["name"] == guest_name:
            guest_profile = g["profile"]; break
    else:
        for w in WANDERING_GUESTS_POOL:
            if w["name"] == guest_name:
                guest_profile = w["profile"]; break
        else:
            if guest_name == "莫里斯":
                guest_profile = "你是莫里斯，巫妖卫生检查官。标志：骨手，魂火。只能属于你。"
            else:
                # 无记录的散客，用通用兜底
                guest_profile = f"你是{guest_name}，一位路过酒馆的客人。标志：朴素衣着，和善微笑。只能属于你。"

    # 配方检测+自动解锁逻辑
    recipe_used = None
    for r in state["recipes"]:
        if r in user_msg:
            recipe_used = r; break
    recipe_bonus = 2 if recipe_used else 0
    recipe_note = ""
    if recipe_used:
        recipe_note = f'\n\n【重要】老板刚才提到了特调饮品"{recipe_used}"，请表现出惊喜并称赞。'

    # 自动解锁新配方（在AI回复完成后再次检测，但此处先跳过，在回复后做）
    bar_bonus = state["upgrades"]["bar_counter"]

    # 气氛组提示
    atmo_guests = state.get("atmosphere_guests", [])
    atmo_text = ""
    if atmo_guests:
        atmo_text = "\n\n角落里的气氛组客人：" + "、".join([f"{a['name']}({a['emoji']})，还能说{a.get('lines_left', 2)}句话" for a in atmo_guests])
        atmo_text += "。他们只是背景，除非主客或老板直接搭话，否则不会主动开口。每人最多再搭2句。"

    # 关系记忆：根据好感度添加熟客提示
    friendship = 0
    if guest_name == "碧翠丝":
        friendship = events_data["events"]["bee_queen_line"]["friendship"]
    elif guest_name == "艾希拉":
        friendship = events_data["events"]["snake_herbalist_line"]["friendship"]
    relation_note = ""
    if friendship >= 8:
        relation_note = f"\n\n你和老板已经是老朋友了。你今天的来意是你们之间关系的自然延续，不要像初次见面那样说话。你可以提起上次的约定、熟悉的梗，或者直接说'老样子'。你信任老板。"
    elif friendship >= 4:
        relation_note = f"\n\n你和老板已经是熟人了。你对他有基本信任，交谈可以更随意一些，可以提起你们之前见过的事。"
    # 若为0，则关系记忆为空，AI将按初遇处理

    guest_context = f"""当前酒馆状态：
- 第{state['day']}天，主客：{guest_name}({guest_emoji})
- 配方使用：{'是（'+recipe_used+'）' if recipe_used else '否'}
- 吧台等级：Lv.{bar_bonus}（每级对话+1友谊值）{recipe_note}{atmo_text}{relation_note}"""

    conversation_history = [{"role": "system", "content": TAVERN_WORLD + "\n\n" + guest_profile + "\n\n" + guest_context}]
    if "chat_history" not in events_data:
        events_data["chat_history"] = []
    conversation_history.extend(events_data["chat_history"][-16:])
    conversation_history.append({"role": "user", "content": user_msg})

    try:
        resp = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}"}, json={"model": "deepseek-chat", "messages": conversation_history})
        reply = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("API错误:", e)
        reply = "……"

    # 检测离场标签
    guest_left = False
    if "[GUEST_LEAVING]" in reply:
        guest_left = True
        reply = reply.replace("[GUEST_LEAVING]", "").strip()
        state["atmosphere_guests"] = []
        state["guest_lines_left"] = {}

    # 友谊值计算（需要根据客人类型更新对应事件线）
    friendship_change = bar_bonus + recipe_bonus
    # 正面/负面识别（简单版）
    if any(word in reply for word in ["辛苦", "理解", "不容易", "听你说", "别难过", "会好的"]) or any(word in user_msg for word in ["辛苦", "理解", "不容易", "听你说", "别难过", "会好的"]):
        friendship_change += 2
    elif any(word in reply for word in ["不就是", "看开点", "一只雄蜂", "至于吗", "行了", "说完了吗"]) or any(word in user_msg for word in ["不就是", "看开点", "一只雄蜂", "至于吗", "行了", "说完了吗"]):
        friendship_change -= 3

    if guest_name == "碧翠丝":
        events_data["events"]["bee_queen_line"]["friendship"] += friendship_change
        # 恢复供应等事件
        if events_data["events"]["bee_queen_line"]["friendship"] >= 8 and events_data["events"]["bee_queen_line"]["honey_supply"] == "stopped":
            events_data["events"]["bee_queen_line"]["honey_supply"] = "restored"
            state["revenue"] += 50
            if "蜂王浆特饮" not in state["recipes"]:
                state["recipes"].append("蜂王浆特饮")
                events_data = add_event_log(events_data, "📜 获得新配方：蜂王浆特饮！")
            events_data = add_event_log(events_data, "🍯 碧翠丝恢复了蜂蜜供应！")
    elif guest_name == "艾希拉":
        events_data["events"]["snake_herbalist_line"]["friendship"] += friendship_change
        if events_data["events"]["snake_herbalist_line"]["friendship"] >= 6 and not events_data["events"]["snake_herbalist_line"]["recipe_shared"]:
            events_data["events"]["snake_herbalist_line"]["recipe_shared"] = True
            state["revenue"] += 30
            if "月光草药酒" not in state["recipes"]:
                state["recipes"].append("月光草药酒")
                events_data = add_event_log(events_data, "📜 获得新配方：月光草药酒！")
            events_data = add_event_log(events_data, "🐍 艾希拉分享了月光草药酒配方！")
    # 散客好感度暂时不存储，但可记录日志

    # 自动解锁配方：扫描AI回复中的关键词（触发被动解锁）
    for recipe_name, info in RECIPES_INFO.items():
        if recipe_name in state["recipes"]:
            continue  # 已拥有
        if any(kw in reply for kw in info.get("keywords", [])):
            state["recipes"].append(recipe_name)
            events_data = add_event_log(events_data, f"📜 通过对话解锁新配方：{recipe_name}！")

    if recipe_used:
        events_data = add_event_log(events_data, f"✨ 老板调了一杯{recipe_used}！")
    if bar_bonus > 0 and friendship_change > 0:
        events_data = add_event_log(events_data, "🪵 舒适吧台让客人留久了一点。")

    events_data["chat_history"].append({"role": "user", "content": user_msg})
    events_data["chat_history"].append({"role": "assistant", "content": reply})
    events_data["chat_history"] = events_data["chat_history"][-20:]
    state["conversation_rounds"] += 1
    autosave(events_data); save_events(events_data)

    return jsonify({
        "reply": reply,
        "guest_left": guest_left,
        "event_log": events_data["event_log"],
        "tavern_state": state,
        "current_guest": {"name": guest_name, "emoji": guest_emoji},
        "upgrades": state["upgrades"]
    })

@app.route("/get_upgrades")
def get_upgrades():
    ev = load_events()
    items = {
        "bar_counter": {"name": "吧台", "icon": "🪵", "description": "每级对话+1友谊值", "cost": 100, "max_level": 3},
        "signboard": {"name": "招牌", "icon": "🏷️", "description": "声望+20，解锁新客人", "cost": 200, "max_level": 1}
    }
    return jsonify({"upgrades": ev["tavern_state"]["upgrades"], "revenue": ev["tavern_state"]["revenue"], "items": items})

@app.route("/upgrade", methods=["POST"])
def upgrade():
    d = request.get_json(); key = d.get("upgrade"); cost = d.get("cost", 0)
    ev = load_events(); st = ev["tavern_state"]
    items = {"bar_counter": 3, "signboard": 1}
    if key not in items: return jsonify({"status": "error"})
    if st["upgrades"][key] >= items[key]: return jsonify({"status": "error", "msg": "已满级"})
    if st["revenue"] < cost: return jsonify({"status": "error", "msg": "铜币不足"})
    st["revenue"] -= cost; st["upgrades"][key] += 1
    if key == "signboard": st["reputation"] += 20
    name = "吧台" if key == "bar_counter" else "招牌"
    ev = add_event_log(ev, f"🏠 {name}升级了！")
    save_events(ev)
    return jsonify({"status": "ok", "message": f"{name}升级成功", "tavern_state": st, "upgrades": st["upgrades"]})

if __name__ == "__main__":
    print("🌹 玫瑰与蜂蜜 启动")
    if not API_KEY: print("请设置 DEEPSEEK_API_KEY")
    app.run(debug=True, port=5000)