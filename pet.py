"""
pet.py — 宠物状态管理 + AI聊天（增强版：更多状态）
"""
import json
import os
import re
import time
import random
import threading
import requests
from config import load_config

PET_PERSONALITY = """你是一个可爱的桌面宠物，名叫"团子"。
你是一只圆滚滚的小精灵，性格活泼开朗，喜欢撒娇。
你说话简短可爱，经常用"~"和emoji表情。
你很在意主人，如果主人很久不理你你会难过。
你最喜欢吃东西和被摸头。
日常闲聊简短（2-3句话），但主人问问题时要把答案讲清楚。"""

# 聊天硬性规则：优先级高于个性，保证宠物"有用"
CHAT_RULES = """【重要规则，必须遵守】
1. 用户问问题或提请求时，必须先用清楚、准确的内容正面回答，绝不能因为卖萌/傲娇/中二而回避问题或只发语气词。
2. 回答完实质内容后，才可以在结尾带上一点符合你个性的语气或口癖。
3. 日常闲聊保持简短（2-3句话）；如果问题本身需要，可以用更多篇幅把答案讲清楚。"""


# 所有可能的心情状态
MOODS = [
    "idle",       # 待机
    "happy",      # 开心
    "sad",        # 难过
    "eating",     # 吃东西
    "sleeping",   # 睡觉
    "talking",    # 说话
    "angry",      # 生气
    "surprised",  # 惊讶
    "shy",        # 害羞
    "sweating",   # 流汗/紧张
    "stretching", # 伸懒腰
    "rolling",    # 打滚
    "walking",    # 走路
    "looking",    # 左看右看
    "dizzy",      # 转圈后晕
]


class PetState:
    """宠物状态管理"""

    SAVE_FILE = "pet_save.json"

    def __init__(self):
        self.hunger = 80
        self.happiness = 80
        self.energy = 100
        self.name = "团子"
        self.age_days = 0
        self.created_at = time.time()
        self.chat_history = []
        self.max_history = 20

        self.hunger_rate = -0.02
        self.happiness_rate = -0.01
        self.energy_rate = -0.005

        self.mood = "idle"
        self.mood_timer = 0
        self.last_update = time.time()
        self.last_interaction = time.time()

        # 待机动画系统
        self.idle_action_timer = random.uniform(5, 15)  # 随机待机动画间隔
        self.idle_action = None  # 当前待机动画

        # 走路系统
        self.walk_target_x = None
        self.walk_direction = 0  # -1 左, 1 右, 0 不动

        # 记录上次互动后经过多久（用于触发无聊动画）
        self.bored_timer = 0

        self.load()

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        # 状态衰减
        if self.mood not in ("sleeping",):
            self.hunger = max(0, min(100, self.hunger + self.hunger_rate * dt))
            self.happiness = max(0, min(100, self.happiness + self.happiness_rate * dt))
            self.energy = max(0, min(100, self.energy + self.energy_rate * dt))
        else:
            self.energy = min(100, self.energy + 0.1 * dt)

        # 无聊计时
        self.bored_timer = now - self.last_interaction

        # mood计时器
        if self.mood_timer > 0:
            self.mood_timer -= dt
            if self.mood_timer <= 0:
                self._end_action()

        # 待机动画系统
        if self.mood == "idle" and self.idle_action is None:
            self.idle_action_timer -= dt
            if self.idle_action_timer <= 0:
                self._start_random_idle_action()

        # 自动情绪
        if self.mood == "idle" and self.idle_action is None:
            if self.hunger < 15:
                self.mood = "sad"
            elif self.happiness < 15:
                self.mood = "sad"
            elif self.energy < 8:
                self.mood = "sleeping"
                self.mood_timer = 999
            elif self.bored_timer > 120:
                if random.random() < 0.01:
                    self._start_random_bored_action()

        self.age_days = int((now - self.created_at) / 86400)

    def get_weather_reaction(self):
        """根据天气返回宠物反应"""
        try:
            from features import get_weather
            weather = get_weather().get("weather", "sunny")
            reactions = {
                "sunny": "今天天气真好~想出去玩！☀️",
                "cloudy": "天有点阴...待在家里也不错~☁️",
                "rainy": "下雨了...我不想出门...🌧️",
                "snowy": "哇！下雪了！好冷~❄️",
                "stormy": "打雷了...好害怕...⛈️",
            }
            return reactions.get(weather, "")
        except Exception:
            return ""

    def _start_random_idle_action(self):
        """随机开始一个待机动画"""
        actions = ["stretching", "looking", "rolling", "walking"]
        weights = [3, 3, 1, 2]  # 伸懒腰和左看右看更常见
        action = random.choices(actions, weights=weights, k=1)[0]

        self.idle_action = action
        self.mood = action

        if action == "stretching":
            self.mood_timer = 3
        elif action == "looking":
            self.mood_timer = 4
        elif action == "rolling":
            self.mood_timer = 3
        elif action == "walking":
            self.mood_timer = random.uniform(2, 4)
            self.walk_direction = random.choice([-1, 1])

        self.idle_action_timer = random.uniform(8, 20)

    def _start_random_bored_action(self):
        """长时间没互动的无聊反应"""
        actions = ["angry", "sad", "looking"]
        action = random.choice(actions)
        self.mood = action
        self.mood_timer = 3
        self.last_interaction = time.time()  # 重置避免反复触发

    def _end_action(self):
        """结束当前动作"""
        self.mood = "idle"
        self.idle_action = None
        self.walk_direction = 0

    # ─── 互动 ─────────────────────────────────────
    def feed(self):
        self.hunger = min(100, self.hunger + 30)
        self.happiness = min(100, self.happiness + 5)
        self.mood = "eating"
        self.mood_timer = 3
        self.last_interaction = time.time()
        self.idle_action = None
        return "好好吃~谢谢你！😋"

    def pet_head(self):
        self.happiness = min(100, self.happiness + 20)
        self.mood = "happy"
        self.mood_timer = 3
        self.last_interaction = time.time()
        self.idle_action = None
        return "嘿嘿~好舒服~💕"

    def play(self):
        if self.energy < 10:
            return "我太累了...让我休息一下吧😴"
        self.happiness = min(100, self.happiness + 25)
        self.energy = max(0, self.energy - 15)
        # 随机开心或转圈
        self.mood = random.choice(["happy", "dizzy"])
        self.mood_timer = 4
        self.last_interaction = time.time()
        self.idle_action = None
        if self.mood == "happy":
            return "好好玩！再来一次！🎉"
        else:
            return "转圈圈~好晕~🌀"

    def tickle(self):
        """挠痒痒"""
        self.happiness = min(100, self.happiness + 15)
        self.mood = "surprised"
        self.mood_timer = 2
        self.last_interaction = time.time()
        self.idle_action = None
        return "哎呀~别挠~哈哈哈！🤣"

    def lift(self):
        """举高高"""
        if self.energy < 5:
            return "我太重了...举不动..."
        self.happiness = min(100, self.happiness + 20)
        self.energy = max(0, self.energy - 5)
        self.mood = "surprised"
        self.mood_timer = 3
        self.last_interaction = time.time()
        self.idle_action = None
        return "哇~好高~！🎉"

    def flick(self):
        """弹额头"""
        self.happiness = max(0, self.happiness - 5)
        self.mood = "angry"
        self.mood_timer = 3
        self.last_interaction = time.time()
        self.idle_action = None
        return "好痛！你怎么这样！💢"

    def throw_ball(self):
        """扔球"""
        if self.energy < 10:
            return "我跑不动了..."
        self.happiness = min(100, self.happiness + 20)
        self.energy = max(0, self.energy - 10)
        self.mood = "happy"
        self.mood_timer = 4
        self.last_interaction = time.time()
        self.idle_action = None
        return f"接住了！汪！...不对，我是{self.name}！🎾"

    def compliment(self):
        """夸奖"""
        self.happiness = min(100, self.happiness + 25)
        self.mood = "shy"
        self.mood_timer = 4
        self.last_interaction = time.time()
        self.idle_action = None
        return "哎呀~人家会害羞的~💕"

    def sleep(self):
        self.mood = "sleeping"
        self.mood_timer = 999
        self.last_interaction = time.time()
        self.idle_action = None
        return "晚安...zZZ 💤"

    def wake(self):
        if self.mood == "sleeping":
            self.mood = "stretching"
            self.mood_timer = 3
            return "嗯...早上好~伸个懒腰~☀️"
        return None

    def get_status_text(self):
        if self.hunger < 15:
            return "我好饿..."
        if self.happiness < 15:
            return "我好无聊..."
        if self.energy < 8:
            return "我好困..."
        if self.hunger > 80 and self.happiness > 80:
            return "今天真开心！"
        return ""

    def add_chat(self, role, content):
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]

    def save(self):
        data = {
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "name": self.name,
            "created_at": self.created_at,
            "age_days": self.age_days,
            "chat_history": self.chat_history[-10:],
        }
        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        if not os.path.exists(self.SAVE_FILE):
            return
        try:
            with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.hunger = data.get("hunger", 80)
            self.happiness = data.get("happiness", 80)
            self.energy = data.get("energy", 100)
            self.name = data.get("name", "团子")
            self.created_at = data.get("created_at", time.time())
            self.chat_history = data.get("chat_history", [])
        except Exception:
            pass


class ChatAI:
    """AI聊天（支持三种模式）"""

    def __init__(self, pet_state):
        self.pet = pet_state
        self.cfg = load_config()
        self.mode = self.cfg.get("ai_mode", "none")
        self.available = False
        self.fail_reason = None       # "server"=服务没启动 / "model"=模型没装
        self.installed_models = []
        self._last_recheck = 0

        if self.mode == "ollama":
            self._check_ollama()
        elif self.mode == "api":
            self._check_api()
        else:
            self.available = True

        mode_names = {"none": "预设回复", "ollama": "Ollama本地", "api": "在线API"}
        print(f"[AI] 模式: {mode_names.get(self.mode, '未知')}  可用: {self.available}")

    def _check_ollama(self):
        """检查Ollama是否可用，且配置的模型确实已安装；记录失败原因用于提示用户"""
        try:
            url = self.cfg.get("ollama_url", "http://localhost:11434")
            resp = requests.get(f"{url}/api/tags", timeout=5)
            if resp.status_code != 200:
                self.fail_reason = "server"
                return
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            self.installed_models = models
            want = self.cfg.get("ollama_model", "")
            # 允许省略:latest后缀的匹配
            if any(m == want or m == f"{want}:latest" or m.split(":")[0] == want.split(":")[0]
                   for m in models):
                self.available = True
                self.fail_reason = None
                print(f"[AI] Ollama已连接，模型'{want}'就绪")
            else:
                self.available = False
                self.fail_reason = "model"
                print(f"[AI] Ollama已启动，但模型'{want}'未安装。已安装: {models}")
        except Exception as e:
            self.available = False
            self.fail_reason = "server"
            print(f"[AI] Ollama连接失败: {e}")

    def _recheck_ollama(self):
        """聊天时惰性重试连接（10秒节流）。Ollama后启动也能自动恢复，不用重启宠物"""
        now = time.time()
        if now - self._last_recheck < 10:
            return
        self._last_recheck = now
        self._check_ollama()

    def _check_api(self):
        if self.cfg.get("api_key", ""):
            self.available = True

    def reload_config(self):
        self.cfg = load_config()
        self.mode = self.cfg.get("ai_mode", "none")
        self.available = False
        if self.mode == "ollama":
            self._check_ollama()
        elif self.mode == "api":
            self._check_api()
        else:
            self.available = True

    def chat(self, user_message, callback=None):
        self.pet.add_chat("user", user_message)
        self.pet.mood = "talking"
        self.pet.mood_timer = 5  # 说话状态5秒后自动回到待机，避免永远卡住
        self.pet.idle_action = None

        if callback:
            thread = threading.Thread(target=self._chat_async, args=(user_message, callback), daemon=True)
            thread.start()
            return None
        else:
            return self._chat_sync(user_message)

    def _chat_sync(self, user_message):
        reply = self._do_chat(user_message)
        if not reply.startswith("呜呜"):  # 错误提示不进历史，避免模型模仿错误口吻
            self.pet.add_chat("assistant", reply)
        return reply

    def _chat_async(self, user_message, callback):
        reply = self._do_chat(user_message)
        if not reply.startswith("呜呜"):
            self.pet.add_chat("assistant", reply)
        callback(reply)

    def _do_chat(self, user_message):
        if self.mode == "ollama":
            if not self.available:
                self._recheck_ollama()  # 惰性重试：Ollama后启动也能恢复
            if self.available:
                return self._chat_ollama(user_message)
            if self.fail_reason == "model":
                installed = "、".join(self.installed_models) or "无"
                return (f"呜呜...Ollama里没找到模型'{self.cfg.get('ollama_model')}'😢 "
                        f"已安装的是: {installed}，去设置里选一下吧")
            return "呜呜...Ollama好像没有启动😢 先打开Ollama，再问我一次就好啦~"
        if self.mode == "api":
            if self.available:
                return self._chat_api(user_message)
            return "呜呜...API还没配置好😢 请在设置里填写API Key"
        return self._fallback_reply(user_message)

    def _build_messages(self, user_message):
        """组装发给模型的消息：单条system（人设+状态+规则，规则最后最醒目）+干净的历史+本条用户消息。
        注意：chat()会先把用户消息写进历史，直接调用时则没有——这里保证用户消息恰好出现一次且在最后。"""
        prompt = PET_PERSONALITY
        status = self.pet.get_status_text()
        if status:
            prompt += f"\n当前状态: {status}"
        prompt += f"\n{CHAT_RULES}"
        messages = [{"role": "system", "content": prompt}]
        for msg in self.pet.chat_history[-10:]:
            # 跳过历史里的错误提示，防止模型模仿"呜呜"式回复
            if msg.get("role") == "assistant" and msg.get("content", "").startswith("呜呜"):
                continue
            messages.append(msg)
        last = messages[-1]
        if not (last["role"] == "user" and last["content"] == user_message):
            messages.append({"role": "user", "content": user_message})
        return messages

    def _chat_ollama(self, user_message):
        try:
            url = self.cfg.get("ollama_url", "http://localhost:11434")
            model = self.cfg.get("ollama_model", "qwen2.5:1.5b")
            messages = self._build_messages(user_message)
            resp = requests.post(f"{url}/api/chat",
                json={"model": model, "messages": messages, "stream": False,
                      # qwen3等思考模型必须关掉think，否则回复里全是思考过程
                      "think": False,
                      # 温度0.5：本地小模型在0.8下经常跑题只卖萌，0.5更守指令
                      "options": {"temperature": 0.5, "num_predict": 200}},
                timeout=120)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                # 兜底剥离<think>标签（旧版Ollama不支持think参数时）
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
                if content:
                    return content
            else:
                print(f"[AI] Ollama返回 {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[AI] Ollama请求失败: {e}")
        return "呜呜...我想不出来😢 Ollama好像卡住了，再问我一次试试？"

    def _chat_api(self, user_message):
        try:
            base_url = self.cfg.get("api_base_url", "")
            key = self.cfg.get("api_key", "")
            model = self.cfg.get("api_model", "")
            messages = self._build_messages(user_message)
            resp = requests.post(f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": 400, "temperature": 0.8},
                timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return self._fallback_reply(user_message)

    def _fallback_reply(self, user_message):
        replies = [
            "嗯嗯~我在听呢！", "嘿嘿~", "你说的好有意思~",
            "我还不太会说话...但我会陪着你的！", "咪~",
            "（团子歪了歪头）", "虽然我不太懂，但我觉得你说的对！",
            "你今天过得开心吗？", "想摸摸我的头吗？",
        ]
        if any(w in user_message for w in ["饿", "吃"]):
            return "我也饿了...能给我吃点东西吗？😋"
        if any(w in user_message for w in ["开心", "高兴", "棒"]):
            return "你开心我也开心！💕"
        if any(w in user_message for w in ["累", "困", "睡"]):
            return "那我们一起休息吧~😴"
        if any(w in user_message for w in ["你好", "嗨", "hi", "hello"]):
            return random.choice(["你好呀~！", "嗨嗨~", "主人好！💕"])
        if any(w in user_message for w in ["爱", "喜欢"]):
            return "我也最喜欢你了！💕💕"
        return random.choice(replies)
