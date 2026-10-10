"""
pet_selector.py — 宠物选择页面（简化版）
"""
import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from pets import get_pet_list, get_pet_data, PET_DATA

PET_SAVE_FILE = "pet_selected.json"


def load_selected_pet():
    if os.path.exists(PET_SAVE_FILE):
        try:
            with open(PET_SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", "团子")
            if name in PET_DATA:
                return name
        except Exception:
            pass
    return "团子"


def save_selected_pet(name):
    with open(PET_SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f, ensure_ascii=False)


class PetCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name, desc, emoji, is_selected=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(140, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.selected = is_selected
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        name_label = QLabel(f"{emoji} {name}")
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setStyleSheet("font-size: 11px; color: #888;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def set_selected(self, selected):
        self.selected = selected
        self._update_style()

    def _update_style(self):
        if self.selected:
            self.setStyleSheet("""
                PetCard {
                    background: #e8f0fe;
                    border: 2px solid #78dcff;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                PetCard {
                    background: white;
                    border: 2px solid #eee;
                    border-radius: 10px;
                }
                PetCard:hover {
                    border-color: #78dcff;
                    background: #f8f9fa;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)


# 每种宠物的emoji
PET_EMOJIS = {
    "团子": "🔵",
    "小喵": "🐱",
    "汪仔": "🐶",
    "兔叽": "🐰",
    "小龙": "🐲",
    "幽幽": "👻",
    "豆豆": "🤖",
    "火球": "🔥",
}


class PetSelectorDialog(QDialog):
    pet_selected = pyqtSignal(str)

    def __init__(self, current_pet="团子", parent=None):
        super().__init__(parent)
        self.current_pet = current_pet
        self.setWindowTitle("选择你的宠物")
        self.setFixedSize(420, 380)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
        """)

        layout = QVBoxLayout(self)

        title = QLabel("选择你的宠物伙伴：")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 宠物网格
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cards = {}

        pets = get_pet_list()
        for i, (name, desc) in enumerate(pets):
            emoji = PET_EMOJIS.get(name, "⭐")
            card = PetCard(name, desc, emoji, is_selected=(name == current_pet))
            card.clicked.connect(self._on_card_clicked)
            self.cards[name] = card
            grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(grid)

        # 选中信息
        self.info_label = QLabel(f"当前选择: {current_pet}")
        self.info_label.setStyleSheet("font-size: 14px; color: #666; margin: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # 按钮
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton { padding: 10px 20px; border-radius: 8px; font-size: 14px;
                          background: #eee; color: #666; }
            QPushButton:hover { background: #ddd; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("确认选择")
        confirm_btn.setStyleSheet("""
            QPushButton { padding: 10px 20px; border-radius: 8px; font-size: 14px;
                          background: #78dcff; color: white; font-weight: bold; }
            QPushButton:hover { background: #5bc0f0; }
        """)
        confirm_btn.clicked.connect(self._confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _on_card_clicked(self, name):
        self.current_pet = name
        for n, card in self.cards.items():
            card.set_selected(n == name)
        self.info_label.setText(f"当前选择: {name} — {get_pet_data(name)['desc']}")

    def _confirm(self):
        save_selected_pet(self.current_pet)
        self.pet_selected.emit(self.current_pet)
        self.accept()
