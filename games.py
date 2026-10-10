"""
games.py — 宠物小游戏
猜拳、翻牌、接球
"""
import random
import time
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QPen


# ─── 猜拳游戏 ─────────────────────────────────────
class RockPaperScissors(QDialog):
    """猜拳：和宠物玩石头剪刀布"""

    def __init__(self, pet_state, parent=None):
        super().__init__(parent)
        self.pet = pet_state
        self.wins = 0
        self.rounds = 0

        self.setWindowTitle(f"✊✌✋ 猜拳 — vs {pet_state.name}")
        self.setFixedSize(350, 420)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #f0f4f8; font-family: "Microsoft YaHei"; }
            QLabel { font-size: 14px; }
            QPushButton { font-size: 28px; padding: 15px; border-radius: 12px;
                          border: 2px solid #ddd; background: white; }
            QPushButton:hover { background: #e8f0fe; border-color: #78dcff; }
            #result { font-size: 20px; font-weight: bold; }
            #score { font-size: 16px; color: #666; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel(f"和{pet_state.name}猜拳！")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 回合显示
        self.round_label = QLabel("选择你的出拳：")
        self.round_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.round_label)

        # 宠物出拳显示
        self.pet_label = QLabel("🐾")
        self.pet_label.setStyleSheet("font-size: 60px;")
        self.pet_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pet_label)

        # 结果
        self.result_label = QLabel("")
        self.result_label.setObjectName("result")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        # 分数
        self.score_label = QLabel("胜: 0 / 0")
        self.score_label.setObjectName("score")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)

        # 按钮
        btn_layout = QHBoxLayout()
        choices = [("✊", "rock"), ("✌", "scissors"), ("✋", "paper")]
        for emoji, choice in choices:
            btn = QPushButton(emoji)
            btn.clicked.connect(lambda _, c=choice: self._play(c))
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # 宠物状态
        self.pet_msg = QLabel("")
        self.pet_msg.setStyleSheet("color: #888; font-size: 12px;")
        self.pet_msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pet_msg)

        # 退出
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _play(self, player_choice):
        self.rounds += 1

        # 宠物随机出
        pet_choice = random.choice(["rock", "scissors", "paper"])
        emoji_map = {"rock": "✊", "scissors": "✌", "paper": "✋"}
        self.pet_label.setText(emoji_map[pet_choice])

        # 判定
        result = self._judge(player_choice, pet_choice)

        if result == "win":
            self.wins += 1
            self.result_label.setText("你赢了！🎉")
            self.result_label.setStyleSheet("color: #4CAF50; font-size: 20px;")
            self.pet_msg.setText(f"{self.pet.name}: 呜...再来！")
            self.pet.happiness = min(100, self.pet.happiness + 5)
        elif result == "lose":
            self.result_label.setText("你输了！😤")
            self.result_label.setStyleSheet("color: #f44336; font-size: 20px;")
            self.pet_msg.setText(f"{self.pet.name}: 嘿嘿~我赢了！")
            self.pet.happiness = min(100, self.pet.happiness + 10)
        else:
            self.result_label.setText("平局！🤝")
            self.result_label.setStyleSheet("color: #FF9800; font-size: 20px;")
            self.pet_msg.setText(f"{self.pet.name}: 诶~一样！")

        self.score_label.setText(f"胜: {self.wins} / {self.rounds}")
        self.round_label.setText(f"第 {self.rounds} 回合 — 再来！")

    def _judge(self, p1, p2):
        if p1 == p2:
            return "draw"
        wins = {("rock", "scissors"), ("scissors", "paper"), ("paper", "rock")}
        return "win" if (p1, p2) in wins else "lose"


# ─── 翻牌游戏 ─────────────────────────────────────
class CardFlip(QDialog):
    """翻牌：记忆配对游戏"""

    def __init__(self, pet_state, parent=None):
        super().__init__(parent)
        self.pet = pet_state
        self.pairs = 6  # 6对 = 12张牌
        self.emojis = random.sample(["🍎", "🍊", "🍋", "🍇", "🍓", "🍑",
                                      "🌸", "🌻", "⭐", "🌙", "❤️", "💎"], self.pairs)
        self.cards = self.emojis * 2
        random.shuffle(self.cards)

        self.revealed = [False] * len(self.cards)  # 是否翻开
        self.matched = [False] * len(self.cards)   # 是否配对成功
        self.first_pick = -1
        self.moves = 0
        self.matched_count = 0
        self.locked = False  # 防止连续点击

        self.setWindowTitle("🃏 翻牌记忆")
        self.setFixedSize(360, 440)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #2d5016; font-family: "Microsoft YaHei"; }
            QPushButton { font-size: 24px; padding: 12px; border-radius: 8px;
                          background: #4a7c2e; color: white; border: 2px solid #3d6b22;
                          min-width: 50px; min-height: 50px; }
            QPushButton:hover { background: #5a9c3e; }
            QPushButton[matched="true"] { background: #2d5016; border-color: #4a7c2e; }
            QLabel { color: white; font-size: 14px; }
        """)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🃏 记忆翻牌 — 找出所有配对！")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #90EE90;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 信息
        self.info_label = QLabel(f"步数: 0  配对: 0/{self.pairs}")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # 宠物提示
        self.pet_label = QLabel(f"{pet_state.name}: 加油！找到所有配对！")
        self.pet_label.setStyleSheet("color: #FFD700; font-size: 12px;")
        self.pet_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pet_label)

        # 牌面网格 (4行3列)
        grid = QGridLayout()
        grid.setSpacing(6)
        self.buttons = []
        for i in range(len(self.cards)):
            btn = QPushButton("?")
            btn.clicked.connect(lambda _, idx=i: self._flip(idx))
            self.buttons.append(btn)
            grid.addWidget(btn, i // 4, i % 4)

        layout.addLayout(grid)

        # 退出
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("font-size: 14px; padding: 6px; background: #666;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _flip(self, idx):
        if self.locked or self.matched[idx] or self.revealed[idx]:
            return

        self.revealed[idx] = True
        self.buttons[idx].setText(self.cards[idx])
        self.buttons[idx].setStyleSheet("font-size: 24px; background: white;")

        if self.first_pick == -1:
            self.first_pick = idx
        else:
            self.moves += 1
            self.locked = True

            if self.cards[self.first_pick] == self.cards[idx]:
                # 配对成功
                self.matched[self.first_pick] = True
                self.matched[idx] = True
                self.matched_count += 1

                self.buttons[self.first_pick].setProperty("matched", True)
                self.buttons[idx].setProperty("matched", True)
                self.buttons[self.first_pick].setStyleSheet(
                    "font-size: 24px; background: #2d5016; border: 2px solid #4a7c2e;")
                self.buttons[idx].setStyleSheet(
                    "font-size: 24px; background: #2d5016; border: 2px solid #4a7c2e;")

                self.first_pick = -1
                self.locked = False

                if self.matched_count == self.pairs:
                    self.pet_label.setText(f"{self.pet.name}: 太厉害了！{self.moves}步就完成了！🎉")
                    self.pet.happiness = min(100, self.pet.happiness + 20)
            else:
                # 不匹配，翻回去
                QTimer.singleShot(600, lambda: self._hide(self.first_pick, idx))

            self.info_label.setText(f"步数: {self.moves}  配对: {self.matched_count}/{self.pairs}")

    def _hide(self, idx1, idx2):
        # 对话框可能已关闭销毁，延迟回调需防 RuntimeError
        try:
            self._do_hide(idx1, idx2)
        except RuntimeError:
            pass

    def _do_hide(self, idx1, idx2):
        self.revealed[idx1] = False
        self.revealed[idx2] = False
        self.buttons[idx1].setText("?")
        self.buttons[idx1].setStyleSheet("font-size: 24px; padding: 12px; background: #4a7c2e;")
        self.buttons[idx2].setText("?")
        self.buttons[idx2].setStyleSheet("font-size: 24px; padding: 12px; background: #4a7c2e;")
        self.first_pick = -1
        self.locked = False


# ─── 接球游戏 ─────────────────────────────────────
class CatchBall(QDialog):
    """接球：左右移动接住掉落的球"""

    def __init__(self, pet_state, parent=None):
        super().__init__(parent)
        self.pet = pet_state

        self.setWindowTitle("🎾 接球游戏")
        self.setFixedSize(300, 450)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background: #1a1a2e;")

        # 游戏状态
        self.paddle_x = 120  # 挡板位置
        self.paddle_w = 60
        self.balls = []  # [(x, y, speed), ...]
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.spawn_timer = 0

        # 标签
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("color: white; font-size: 14px; font-family: 'Microsoft YaHei';")
        self.info_label.setGeometry(10, 5, 280, 25)

        self.pet_label = QLabel(f"{pet_state.name}: 接住球球！", self)
        self.pet_label.setStyleSheet("color: #FFD700; font-size: 12px; font-family: 'Microsoft YaHei';")
        self.pet_label.setGeometry(10, 28, 280, 20)

        # 游戏定时器（parent=self，随窗口销毁自动清理）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)  # 33fps

        # 生成第一个球
        self._spawn_ball()

    def closeEvent(self, event):
        # 关闭时停止定时器，避免触发已删除的对象
        self.timer.stop()
        super().closeEvent(event)

    def _spawn_ball(self):
        x = random.randint(20, 260)
        speed = random.uniform(2, 4 + self.score * 0.1)
        self.balls.append([x, 0, speed])

    def _tick(self):
        if self.game_over:
            return

        self.spawn_timer += 1
        if self.spawn_timer > 40:  # 每1.2秒生成新球
            self._spawn_ball()
            self.spawn_timer = 0

        # 移动球
        for ball in self.balls:
            ball[1] += ball[2]

        # 检测接住
        new_balls = []
        for ball in self.balls:
            bx, by = ball[0], ball[1]
            # 接住
            if by >= 390 and by <= 410:
                if self.paddle_x <= bx <= self.paddle_x + self.paddle_w:
                    self.score += 1
                    self.pet.happiness = min(100, self.pet.happiness + 1)
                    continue
            # 掉出屏幕
            if by > 430:
                self.lives -= 1
                if self.lives <= 0:
                    self._game_over()
                    return
                continue
            new_balls.append(ball)
        self.balls = new_balls

        self.info_label.setText(f"分数: {self.score}  ❤️ x {self.lives}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 挡板
        painter.setBrush(QBrush(QColor(120, 220, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.paddle_x, 400, self.paddle_w, 12, 6, 6)

        # 球
        for ball in self.balls:
            painter.setBrush(QBrush(QColor(255, 200, 80)))
            painter.setPen(QPen(QColor(255, 150, 50), 1))
            painter.drawEllipse(int(ball[0]) - 8, int(ball[1]) - 8, 16, 16)

        painter.end()

    def mouseMoveEvent(self, event):
        if not self.game_over:
            self.paddle_x = max(0, min(240, event.x() - self.paddle_w // 2))
            self.update()

    def _game_over(self):
        self.game_over = True
        self.timer.stop()
        self.pet_label.setText(f"{self.pet.name}: 结束了！得分 {self.score}！{'🎉' if self.score > 10 else '💪'}")
        if self.score >= 10:
            self.pet.happiness = min(100, self.pet.happiness + 20)
        self.pet.energy = max(0, self.pet.energy - 10)

        # 显示重新开始按钮
        restart_btn = QPushButton("再来一次", self)
        restart_btn.setStyleSheet("""
            QPushButton { background: #78dcff; color: white; font-size: 16px;
                          padding: 10px; border-radius: 8px; font-family: "Microsoft YaHei"; }
            QPushButton:hover { background: #5bc0f0; }
        """)
        restart_btn.setGeometry(100, 200, 100, 40)
        restart_btn.clicked.connect(self._restart)
        restart_btn.show()

    def _restart(self):
        self.balls = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.spawn_timer = 0
        self.paddle_x = 120
        self.timer.start(30)
        self.pet_label.setText(f"{self.pet.name}: 接住球球！")
        # 清除重启按钮
        for child in self.findChildren(QPushButton):
            if child.text() == "再来一次":
                child.deleteLater()
        self.update()
