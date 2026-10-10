"""
features.py — 功能类特性
音效、皮肤、提醒、天气
"""
import json
import os
import time
import threading
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTimeEdit, QListWidget, QListWidgetItem,
    QLineEdit, QGroupBox, QColorDialog
)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QObject
from PyQt5.QtGui import QColor

# ─── 音效系统 ─────────────────────────────────────
# 用Windows内置beep生成简单音效，不需要外部文件

def play_sound(sound_type):
    """播放音效（用系统蜂鸣器，无需外部文件）"""
    try:
        import winsound
        sounds = {
            "happy":    [(800, 80), (1000, 80), (1200, 120)],
            "eat":      [(400, 60), (500, 60), (600, 80)],
            "pet":      [(600, 50), (800, 80)],
            "sleep":    [(400, 100), (300, 150)],
            "angry":    [(300, 80), (200, 80), (300, 80)],
            "surprise": [(1000, 50), (1200, 50), (800, 80)],
            "ball":     [(500, 40), (700, 40)],
            "card":     [(600, 30)],
            "win":      [(800, 80), (1000, 80), (1200, 80), (1500, 150)],
            "lose":     [(400, 100), (300, 100), (200, 200)],
            "notify":   [(800, 100), (0, 50), (800, 100)],
        }
        freqs = sounds.get(sound_type, [(500, 100)])
        def _play():
            for freq, dur in freqs:
                if freq > 0:
                    winsound.Beep(freq, dur)
                else:
                    time.sleep(dur / 1000)
        threading.Thread(target=_play, daemon=True).start()
    except ImportError:
        pass  # 非Windows系统忽略


# ─── 皮肤系统 ─────────────────────────────────────
SKINS = {
    "默认蓝": {
        "body": QColor(120, 220, 255),
        "body_dark": QColor(80, 180, 230),
        "cheek": QColor(255, 180, 180, 120),
    },
    "樱花粉": {
        "body": QColor(255, 180, 200),
        "body_dark": QColor(230, 140, 170),
        "cheek": QColor(255, 150, 150, 120),
    },
    "柠檬黄": {
        "body": QColor(255, 230, 100),
        "body_dark": QColor(220, 200, 70),
        "cheek": QColor(255, 200, 150, 120),
    },
    "薄荷绿": {
        "body": QColor(150, 230, 200),
        "body_dark": QColor(100, 200, 170),
        "cheek": QColor(200, 255, 200, 120),
    },
    "薰衣草紫": {
        "body": QColor(200, 180, 240),
        "body_dark": QColor(160, 140, 210),
        "cheek": QColor(230, 200, 255, 120),
    },
    "橘子橙": {
        "body": QColor(255, 180, 100),
        "body_dark": QColor(230, 150, 70),
        "cheek": QColor(255, 200, 150, 120),
    },
    "珍珠白": {
        "body": QColor(240, 240, 250),
        "body_dark": QColor(200, 200, 220),
        "cheek": QColor(255, 200, 200, 120),
    },
    "酷酷黑": {
        "body": QColor(60, 60, 80),
        "body_dark": QColor(40, 40, 60),
        "cheek": QColor(100, 80, 80, 120),
    },
}

SKIN_FILE = "pet_skin.json"


def load_skin():
    """加载皮肤设置"""
    if os.path.exists(SKIN_FILE):
        try:
            with open(SKIN_FILE, "r") as f:
                data = json.load(f)
            name = data.get("name", "默认蓝")
            if name in SKINS:
                return name, SKINS[name]
        except Exception:
            pass
    return "默认蓝", SKINS["默认蓝"]


def save_skin(name):
    """保存皮肤设置"""
    with open(SKIN_FILE, "w") as f:
        json.dump({"name": name}, f)


# ─── 提醒系统 ─────────────────────────────────────
REMINDERS_FILE = "pet_reminders.json"


def load_reminders():
    """加载提醒列表"""
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_reminders(reminders):
    """保存提醒列表"""
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)


# ─── 天气系统 ─────────────────────────────────────
WEATHER_FILE = "pet_weather.json"


def get_weather():
    """获取天气（使用免费API，失败则返回默认值，不阻塞）"""
    # 检查缓存
    if os.path.exists(WEATHER_FILE):
        try:
            with open(WEATHER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("time", 0) < 1800:
                return data
        except Exception:
            pass

    # 异步获取天气（不阻塞UI）
    def _fetch():
        try:
            resp = requests.get("https://wttr.in/?format=j1", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current_condition", [{}])[0]
                weather_code = int(current.get("weatherCode", 113))
                temp = current.get("temp_C", "22")
                if weather_code == 113:
                    weather = "sunny"
                elif weather_code in [116, 119, 122]:
                    weather = "cloudy"
                elif weather_code in [176, 263, 266, 293, 296, 299, 302, 305, 308]:
                    weather = "rainy"
                elif weather_code in [179, 227, 230, 320, 323, 326, 329, 332, 335, 338]:
                    weather = "snowy"
                elif weather_code in [200, 386, 389, 392, 395]:
                    weather = "stormy"
                else:
                    weather = "cloudy"
                result = {"weather": weather, "temp": temp, "time": time.time()}
                with open(WEATHER_FILE, "w", encoding="utf-8") as f:
                    json.dump(result, f)
        except Exception:
            pass

    import threading
    threading.Thread(target=_fetch, daemon=True).start()

    # 立即返回默认值
    return {"weather": "sunny", "temp": "22", "time": time.time()}


# ─── 设置对话框（功能类）──────────────────────────

class SkinDialog(QDialog):
    """皮肤选择对话框"""

    skin_changed = pyqtSignal(str)

    def __init__(self, current_skin, parent=None):
        super().__init__(parent)
        self.current_skin = current_skin
        self.setWindowTitle("🎨 选择皮肤")
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QPushButton { padding: 10px; border-radius: 8px; font-size: 13px;
                          border: 2px solid #ddd; text-align: left; }
            QPushButton:hover { border-color: #78dcff; }
            QPushButton[selected="true"] { border-color: #78dcff; background: #e8f0fe; }
        """)

        layout = QVBoxLayout(self)
        title = QLabel("选择宠物的颜色：")
        title.setStyleSheet("font-size: 15px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        for name, colors in SKINS.items():
            btn = QPushButton(f"  {name}")
            c = colors["body"]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgb({c.red()},{c.green()},{c.blue()});
                    color: {'white' if c.lightness() < 150 else '#333'};
                }}
            """)
            if name == current_skin:
                btn.setProperty("selected", True)
            btn.clicked.connect(lambda _, n=name: self._select(n))
            layout.addWidget(btn)

    def _select(self, name):
        save_skin(name)
        self.skin_changed.emit(name)
        self.accept()


class ReminderDialog(QDialog):
    """提醒设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ 提醒设置")
        self.setFixedSize(320, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.reminders = load_reminders()

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QTimeEdit { padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
            QLineEdit { padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
            QPushButton { padding: 8px 16px; border-radius: 6px; font-size: 13px; }
            #addBtn { background: #78dcff; color: white; font-weight: bold; }
            #delBtn { background: #ff6b6b; color: white; }
        """)

        layout = QVBoxLayout(self)

        title = QLabel("⏰ 设置提醒（到时间宠物会提醒你）")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        # 添加提醒
        add_group = QGroupBox("添加提醒")
        add_layout = QVBoxLayout()

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("时间:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_edit)
        add_layout.addLayout(time_layout)

        msg_layout = QHBoxLayout()
        msg_layout.addWidget(QLabel("内容:"))
        self.msg_edit = QLineEdit()
        self.msg_edit.setPlaceholderText("例如: 该喝水了~")
        msg_layout.addWidget(self.msg_edit)
        add_layout.addLayout(msg_layout)

        add_btn = QPushButton("➕ 添加")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self._add)
        add_layout.addWidget(add_btn)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # 提醒列表
        list_group = QGroupBox("已设置的提醒")
        list_layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self._refresh_list()
        list_layout.addWidget(self.list_widget)

        del_btn = QPushButton("🗑️ 删除选中")
        del_btn.setObjectName("delBtn")
        del_btn.clicked.connect(self._delete)
        list_layout.addWidget(del_btn)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

    def _add(self):
        time_str = self.time_edit.time().toString("HH:mm")
        msg = self.msg_edit.text().strip() or "时间到了~"
        self.reminders.append({"time": time_str, "message": msg, "enabled": True})
        save_reminders(self.reminders)
        self._refresh_list()
        self.msg_edit.clear()

    def _delete(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.reminders.pop(row)
            save_reminders(self.reminders)
            self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for r in self.reminders:
            self.list_widget.addItem(f"⏰ {r['time']} — {r['message']}")


# ─── 提醒检查器 ─────────────────────────────────────
class ReminderChecker(QObject):
    """定时检查提醒"""

    reminder_triggered = pyqtSignal(str)  # 触发提醒时发送消息

    def __init__(self):
        super().__init__()
        self.reminders = load_reminders()
        self.triggered_today = set()

        # 每30秒检查一次
        self.timer = QTimer()
        self.timer.timeout.connect(self._check)
        self.timer.start(30000)

    def reload(self):
        self.reminders = load_reminders()
        self.triggered_today.clear()

    def _check(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        for r in self.reminders:
            key = f"{today}_{r['time']}_{r['message']}"
            if r.get("enabled", True) and r["time"] == current_time and key not in self.triggered_today:
                self.triggered_today.add(key)
                self.reminder_triggered.emit(r["message"])
                play_sound("notify")
