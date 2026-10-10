"""
ui.py — 桌面宠物UI（v3 每种宠物完全不同造型）
"""
import sys
import math
import time
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, QVBoxLayout,
    QLineEdit, QTextEdit, QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon, QPixmap, QImage
from features import play_sound, load_skin, SKINS, get_weather, ReminderChecker

# 尝试导入精灵图系统
SPRITES_AVAILABLE = False
try:
    from sprites import get_sprite_path, ensure_sprites, SPRITE_DIR
    ensure_sprites()
    SPRITES_AVAILABLE = True
    print("[UI] 像素精灵图系统已加载")
except Exception as e:
    print(f"[UI] 精灵图系统不可用: {e}，使用QPainter绘制")


# ─── 颜色 ─────────────────────────────────────────
C_BODY = QColor(120, 220, 255)
C_BODY_DARK = QColor(80, 180, 230)
C_EYE = QColor(40, 40, 60)
C_EYE_WHITE = QColor(255, 255, 255)
C_MOUTH = QColor(255, 120, 120)
C_CHEEK = QColor(255, 180, 180, 120)
C_HAPPY = QColor(255, 220, 100)
C_SAD = QColor(150, 150, 200)
C_SLEEPING = QColor(180, 180, 220)
C_ANGRY = QColor(255, 120, 120)
C_SURPRISED = QColor(255, 200, 150)
C_SHY = QColor(255, 180, 200)
C_SWEATING = QColor(180, 220, 255)
C_STRETCHING = QColor(180, 255, 200)
C_DIZZY = QColor(220, 200, 255)


class PetWidget(QWidget):

    chat_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    change_pet_requested = pyqtSignal()
    about_requested = pyqtSignal()

    def __init__(self, pet_state):
        super().__init__()
        self.pet = pet_state
        self.drag_pos = QPoint()
        self.is_dragging = False
        self.anim_frame = 0
        self.blink_timer = 0
        self.is_blinking = False

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 240)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 250, screen.height() - 320)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.pet.save)
        self.save_timer.start(30000)

        self.bubble_text = ""
        self.bubble_timer = 0
        self.base_x = self.x()
        self.base_y = self.y()

        self.skin_name, self.skin_colors = load_skin()
        self.weather = get_weather()
        self.reminder_checker = ReminderChecker()
        self.reminder_checker.reminder_triggered.connect(self._on_reminder)

    def show_bubble(self, text, duration=3):
        self.bubble_text = text
        self.bubble_timer = duration

    def tick(self):
        self.anim_frame += 1
        self.pet.update()

        if self.bubble_timer > 0:
            self.bubble_timer -= 0.05
            if self.bubble_timer <= 0:
                self.bubble_text = ""

        self.blink_timer += 1
        if not self.is_blinking and self.blink_timer > 60:
            self.is_blinking = True
            self.blink_timer = 0
        elif self.is_blinking and self.blink_timer > 5:
            self.is_blinking = False
            self.blink_timer = 0

        if self.pet.mood == "walking" and not self.is_dragging:
            dx = self.pet.walk_direction * 2
            new_x = self.x() + dx
            screen = QApplication.primaryScreen().geometry()
            new_x = max(0, min(screen.width() - self.width(), new_x))
            self.move(new_x, self.y())

        self.update()

    def paintEvent(self, event):
        try:
            self._paint(event)
        except Exception as e:
            print(f"[ERROR] 绘制错误: {e}")
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(120, 220, 255)))
            painter.setPen(QPen(QColor(80, 180, 230), 2))
            painter.drawEllipse(60, 100, 80, 80)
            painter.end()

    def _paint(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = 100, 130
        mood = self.pet.mood
        f = self.anim_frame

        from pets import get_pet_data
        pet_data = get_pet_data(self.pet.name)
        pet_type = pet_data.get("type", "blob")

        # 弹跳
        bounce = 0.0
        if mood in ("happy", "dizzy"):
            bounce = abs(math.sin(f * 0.3)) * 8
        elif mood == "eating":
            bounce = abs(math.sin(f * 0.5)) * 4
        elif mood == "surprised":
            bounce = abs(math.sin(f * 0.4)) * 10
        elif mood not in ("sleeping",):
            bounce = abs(math.sin(f * 0.08)) * 3
        cy = int(cy - bounce)

        # 尝试使用精灵图
        if SPRITES_AVAILABLE:
            try:
                sprite_path = get_sprite_path(pet_type, mood, f // 5)
                if os.path.exists(sprite_path):
                    # 缓存QPixmap，避免每帧读磁盘
                    if not hasattr(self, "_pixmap_cache"):
                        self._pixmap_cache = {}
                    pixmap = self._pixmap_cache.get(sprite_path)
                    if pixmap is None:
                        pixmap = QPixmap(sprite_path)
                        if not pixmap.isNull():
                            self._pixmap_cache[sprite_path] = pixmap
                    if pixmap is not None and not pixmap.isNull():
                        # 按皮肤色相换色（非默认皮肤时）
                        tinted = self._tint_pixmap(sprite_path)
                        if tinted is not None and not tinted.isNull():
                            pixmap = tinted
                        # 整数倍放大（96→192），像素边缘锐利不发虚
                        scaled = pixmap.scaled(192, 192, Qt.KeepAspectRatio, Qt.FastTransformation)
                        # 绘制到中心
                        x = cx - scaled.width() // 2
                        y = cy - scaled.height() // 2 + 10
                        painter.drawPixmap(x, y, scaled)
                        # 气泡（精灵图分支也要画，否则文字提示永远不显示）
                        if self.bubble_text and self.bubble_timer > 0:
                            self._draw_bubble(painter, cx, cy - 80)
                        painter.end()
                        return
            except Exception as e:
                print(f"[UI] 精灵图加载失败: {e}")

        # 回退到QPainter绘制
        base_color = self.skin_colors.get("body", pet_data.get("color", C_BODY))
        mood_colors = {
            "happy": C_HAPPY, "sad": C_SAD, "sleeping": C_SLEEPING,
            "angry": C_ANGRY, "surprised": C_SURPRISED, "shy": C_SHY,
            "sweating": C_SWEATING, "stretching": C_STRETCHING,
            "dizzy": C_DIZZY, "rolling": C_DIZZY,
        }
        body_color = mood_colors.get(mood, base_color)

        if pet_type == "cat":
            self._draw_cat(painter, cx, cy, body_color, mood, f)
        elif pet_type == "dog":
            self._draw_dog(painter, cx, cy, body_color, mood, f)
        elif pet_type == "rabbit":
            self._draw_rabbit(painter, cx, cy, body_color, mood, f)
        elif pet_type == "dragon":
            self._draw_dragon(painter, cx, cy, body_color, mood, f)
        elif pet_type == "ghost":
            self._draw_ghost(painter, cx, cy, body_color, mood, f)
        elif pet_type == "robot":
            self._draw_robot(painter, cx, cy, body_color, mood, f)
        elif pet_type == "fireball":
            self._draw_fireball(painter, cx, cy, body_color, mood, f)
        else:
            self._draw_blob(painter, cx, cy, body_color, mood, f)

        # 气泡
        if self.bubble_text and self.bubble_timer > 0:
            self._draw_bubble(painter, cx, cy - 80)

        painter.end()

    def _tint_pixmap(self, sprite_path):
        """按皮肤色相对精灵图换色：替换色相和饱和度，保留原明暗层次。
        返回染色后的QPixmap；默认皮肤或失败时返回None（用原图）"""
        if self.skin_name == "默认蓝" or not self.skin_colors:
            return None
        tint = self.skin_colors.get("body")
        if tint is None:
            return None
        if not hasattr(self, "_tint_cache"):
            self._tint_cache = {}
        key = (sprite_path, self.skin_name)
        if key in self._tint_cache:
            return self._tint_cache[key]
        result = None
        try:
            import colorsys
            from PIL import Image
            h_t, s_t, v_t = colorsys.rgb_to_hsv(
                tint.red() / 255, tint.green() / 255, tint.blue() / 255)
            img = Image.open(sprite_path).convert("RGBA")
            px = img.load()
            for yy in range(img.height):
                for xx in range(img.width):
                    r, g, b, a = px[xx, yy]
                    if a == 0:
                        continue
                    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                    if s < 0.08:
                        continue  # 纯白/灰高光保持原样
                    nr, ng, nb = colorsys.hsv_to_rgb(h_t, s_t, v * v_t)
                    px[xx, yy] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            result = QPixmap.fromImage(qimg.copy())
        except Exception as e:
            print(f"[UI] 皮肤染色失败: {e}")
        self._tint_cache[key] = result
        return result

    # ═══════════════════════════════════════════════
    #  团子 — 圆滚滚的小精灵
    # ═══════════════════════════════════════════════
    def _draw_blob(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 35, cy + 38, 70, 12)
        # 身体（圆球）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 40, cy - 40, 80, 80)
        # 肚子高光
        p.setBrush(QBrush(QColor(255, 255, 255, 60)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 18, cy - 8, 36, 32)
        # 脚
        p.setBrush(QBrush(c.darker(110)))
        p.setPen(QPen(c.darker(120), 1.5))
        self._draw_feet(p, cx, cy, mood, f)
        # 手
        self._draw_blob_arms(p, cx, cy, mood, f)
        # 腮红
        p.setBrush(QBrush(C_CHEEK))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 32, cy - 6, 14, 8)
        p.drawEllipse(cx + 18, cy - 6, 14, 8)
        # 眼睛嘴巴
        self._draw_face_standard(p, cx, cy - 10, mood, f)

    def _draw_blob_arms(self, p, cx, cy, mood, f):
        if mood == "eating":
            p.drawEllipse(cx - 48, cy - 15, 14, 10)
            p.drawEllipse(cx + 34, cy - 15, 14, 10)
        elif mood in ("happy", "dizzy"):
            arm = int(math.sin(f * 0.2) * 8)
            p.drawEllipse(cx - 52, cy - 32 + arm, 14, 10)
            p.drawEllipse(cx + 38, cy - 32 - arm, 14, 10)
        elif mood == "stretching":
            p.drawEllipse(cx - 55, cy - 40, 14, 10)
            p.drawEllipse(cx + 41, cy - 40, 14, 10)
        else:
            p.drawEllipse(cx - 48, cy + 2, 14, 10)
            p.drawEllipse(cx + 34, cy + 2, 14, 10)

    # ═══════════════════════════════════════════════
    #  小喵 — 傲娇猫咪
    # ═══════════════════════════════════════════════
    def _draw_cat(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 25, cy + 35, 50, 10)
        # 身体（椭圆，猫的体型）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 30, cy - 25, 60, 55)
        # 三角耳朵
        ear_l = [QPoint(cx - 22, cy - 25), QPoint(cx - 12, cy - 50), QPoint(cx - 2, cy - 25)]
        ear_r = [QPoint(cx + 2, cy - 25), QPoint(cx + 12, cy - 50), QPoint(cx + 22, cy - 25)]
        p.drawPolygon(ear_l)
        p.drawPolygon(ear_r)
        # 内耳
        p.setBrush(QBrush(QColor(255, 180, 200)))
        p.setPen(Qt.NoPen)
        p.drawPolygon([QPoint(cx - 18, cy - 25), QPoint(cx - 12, cy - 42), QPoint(cx - 6, cy - 25)])
        p.drawPolygon([QPoint(cx + 6, cy - 25), QPoint(cx + 12, cy - 42), QPoint(cx + 18, cy - 25)])
        # 胡须
        p.setPen(QPen(QColor(180, 180, 180), 1))
        p.drawLine(cx - 30, cy - 5, cx - 50, cy - 10)
        p.drawLine(cx - 30, cy, cx - 50, cy + 2)
        p.drawLine(cx + 30, cy - 5, cx + 50, cy - 10)
        p.drawLine(cx + 30, cy, cx + 50, cy + 2)
        # 弯尾巴
        tail_x = cx + 25 + int(math.sin(f * 0.08) * 12)
        tail_y = cy + 20
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(tail_x, tail_y - 15, 12, 8)
        p.drawEllipse(tail_x + 8, tail_y - 22, 10, 8)
        p.drawEllipse(tail_x + 14, tail_y - 28, 8, 6)
        # 脚（小猫爪）
        p.drawEllipse(cx - 20, cy + 25, 16, 10)
        p.drawEllipse(cx + 4, cy + 25, 16, 10)
        # 眼睛（猫眼，竖瞳孔）
        self._draw_cat_eyes(p, cx, cy - 10, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 5, mood, f)

    def _draw_cat_eyes(self, p, cx, ey, mood, f):
        if mood in ("happy", "shy"):
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 14, ey - 5, 12, 10, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 5, 12, 10, 0, 180 * 16)
        elif mood == "angry":
            p.setBrush(QBrush(QColor(255, 200, 200)))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 4, 10, 8)
            p.drawEllipse(cx + 2, ey - 4, 10, 8)
            p.setBrush(QBrush(C_ANGRY))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 2, 3, 5)
            p.drawEllipse(cx + 5, ey - 2, 3, 5)
            # 生气眉毛
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 14, ey - 8, cx - 2, ey - 4)
            p.drawLine(cx + 14, ey - 8, cx + 2, ey - 4)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        elif mood == "sleeping":
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 12, ey - 4, 10, 8, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 4, 10, 8, 0, 180 * 16)
        else:
            # 猫眼（大而圆，竖瞳孔）
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 5, 11, 12)
            p.drawEllipse(cx + 1, ey - 5, 11, 12)
            # 竖瞳孔
            p.setBrush(QBrush(QColor(50, 180, 50)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 3, 3, 8)
            p.drawEllipse(cx + 5, ey - 3, 3, 8)
            # 高光
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 7, ey - 4, 2, 3)
            p.drawEllipse(cx + 6, ey - 4, 2, 3)

    # ═══════════════════════════════════════════════
    #  汪仔 — 热情小狗
    # ═══════════════════════════════════════════════
    def _draw_dog(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 30, cy + 38, 60, 12)
        # 身体（圆胖）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 35, cy - 30, 70, 65)
        # 大垂耳
        ear_sway = int(math.sin(f * 0.1) * 3)
        p.drawEllipse(cx - 45 + ear_sway, cy - 20, 16, 30)
        p.drawEllipse(cx + 29 - ear_sway, cy - 20, 16, 30)
        # 舌头
        if mood in ("happy", "idle"):
            p.setBrush(QBrush(QColor(255, 150, 150)))
            p.setPen(Qt.NoPen)
            tongue_y = int(math.sin(f * 0.2) * 2)
            p.drawEllipse(cx - 3, cy + 12 + tongue_y, 8, 10)
        # 尾巴（摇摆）
        tail_wag = int(math.sin(f * 0.3) * 15)
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx + 28 + tail_wag, cy + 5, 16, 8)
        p.drawEllipse(cx + 38 + tail_wag, cy - 2, 12, 8)
        # 脚
        p.drawEllipse(cx - 22, cy + 28, 16, 12)
        p.drawEllipse(cx + 6, cy + 28, 16, 12)
        # 腮红
        p.setBrush(QBrush(C_CHEEK))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 30, cy - 2, 12, 7)
        p.drawEllipse(cx + 18, cy - 2, 12, 7)
        # 眼睛（狗眼，圆而亮）
        self._draw_dog_eyes(p, cx, cy - 12, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 3, mood, f)

    def _draw_dog_eyes(self, p, cx, ey, mood, f):
        if mood in ("happy", "shy"):
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 14, ey - 5, 12, 10, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 5, 12, 10, 0, 180 * 16)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        elif mood == "sleeping":
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 12, ey - 4, 10, 8, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 4, 10, 8, 0, 180 * 16)
        else:
            # 大而圆的狗眼
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 13, ey - 6, 13, 14)
            p.drawEllipse(cx + 0, ey - 6, 13, 14)
            p.setBrush(QBrush(QColor(80, 50, 30)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 3, 6, 7)
            p.drawEllipse(cx + 4, ey - 3, 6, 7)
            # 高光
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 7, ey - 5, 3, 3)
            p.drawEllipse(cx + 5, ey - 5, 3, 3)

    # ═══════════════════════════════════════════════
    #  兔叽 — 胆小兔子
    # ═══════════════════════════════════════════════
    def _draw_rabbit(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 25, cy + 35, 50, 10)
        # 身体（圆）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 30, cy - 20, 60, 50)
        # 超长耳朵（会动）
        ear_bounce = int(abs(math.sin(f * 0.06)) * 6)
        p.drawEllipse(cx - 16, cy - 68 + ear_bounce, 12, 50)
        p.drawEllipse(cx + 4, cy - 68 - ear_bounce, 12, 50)
        # 内耳
        p.setBrush(QBrush(QColor(255, 180, 200)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 13, cy - 63 + ear_bounce, 6, 40)
        p.drawEllipse(cx + 7, cy - 63 - ear_bounce, 6, 40)
        # 棉花尾巴
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(QPen(c.darker(120), 1))
        p.drawEllipse(cx + 20, cy + 18, 14, 12)
        # 脚
        p.setBrush(QBrush(c.darker(110)))
        p.setPen(QPen(c.darker(120), 1.5))
        p.drawEllipse(cx - 20, cy + 25, 16, 10)
        p.drawEllipse(cx + 4, cy + 25, 16, 10)
        # 腮红
        p.setBrush(QBrush(QColor(255, 200, 200, 100)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 28, cy - 2, 12, 7)
        p.drawEllipse(cx + 16, cy - 2, 12, 7)
        # 眼睛（兔眼，大而怯生生）
        self._draw_rabbit_eyes(p, cx, cy - 8, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 6, mood, f)

    def _draw_rabbit_eyes(self, p, cx, ey, mood, f):
        if mood in ("happy", "shy"):
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 12, ey - 4, 10, 8, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 4, 10, 8, 0, 180 * 16)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 7, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 7, ey)
        else:
            # 兔眼（大，有点害怕的感觉）
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 11, ey - 5, 10, 12)
            p.drawEllipse(cx + 1, ey - 5, 10, 12)
            p.setBrush(QBrush(QColor(200, 100, 100)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 7, ey - 1, 4, 6)
            p.drawEllipse(cx + 5, ey - 1, 4, 6)
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 6, ey - 3, 2, 3)
            p.drawEllipse(cx + 6, ey - 3, 2, 3)

    # ═══════════════════════════════════════════════
    #  小龙 — 中二的龙
    # ═══════════════════════════════════════════════
    def _draw_dragon(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 28, cy + 38, 56, 12)
        # 身体（菱形/椭圆）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 32, cy - 28, 64, 58)
        # 鳞片纹理
        p.setBrush(QBrush(c.lighter(115)))
        p.setPen(Qt.NoPen)
        for i in range(3):
            for j in range(2):
                sx = cx - 15 + i * 15
                sy = cy - 10 + j * 15
                p.drawEllipse(sx, sy, 10, 8)
        # 大角
        p.setBrush(QBrush(QColor(255, 200, 50)))
        p.setPen(QPen(QColor(200, 150, 30), 1.5))
        horn_l = [QPoint(cx - 18, cy - 28), QPoint(cx - 12, cy - 55), QPoint(cx - 6, cy - 28)]
        horn_r = [QPoint(cx + 6, cy - 28), QPoint(cx + 12, cy - 55), QPoint(cx + 18, cy - 28)]
        p.drawPolygon(horn_l)
        p.drawPolygon(horn_r)
        # 翅膀（会扇动）
        wing_y = int(math.sin(f * 0.15) * 12)
        p.setBrush(QBrush(c.lighter(130)))
        p.setPen(QPen(c.darker(120), 1.5))
        wing_l = [QPoint(cx - 32, cy - 10), QPoint(cx - 58, cy - 30 + wing_y), QPoint(cx - 38, cy + 10)]
        wing_r = [QPoint(cx + 32, cy - 10), QPoint(cx + 58, cy - 30 - wing_y), QPoint(cx + 38, cy + 10)]
        p.drawPolygon(wing_l)
        p.drawPolygon(wing_r)
        # 尾巴（有尖）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx + 28, cy + 10, 18, 8)
        p.drawEllipse(cx + 42, cy + 8, 12, 6)
        # 尾巴尖
        tail_tip = [QPoint(cx + 52, cy + 8), QPoint(cx + 62, cy + 4), QPoint(cx + 52, cy + 14)]
        p.setBrush(QBrush(QColor(255, 150, 50)))
        p.drawPolygon(tail_tip)
        # 脚
        p.setBrush(QBrush(c.darker(110)))
        p.setPen(QPen(c.darker(120), 1.5))
        p.drawEllipse(cx - 22, cy + 25, 16, 10)
        p.drawEllipse(cx + 6, cy + 25, 16, 10)
        # 眼睛（龙眼，自信/中二）
        self._draw_dragon_eyes(p, cx, cy - 10, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 5, mood, f)

    def _draw_dragon_eyes(self, p, cx, ey, mood, f):
        if mood == "angry":
            p.setBrush(QBrush(QColor(255, 200, 200)))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 4, 10, 9)
            p.drawEllipse(cx + 2, ey - 4, 10, 9)
            p.setBrush(QBrush(QColor(255, 50, 50)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 1, 4, 5)
            p.drawEllipse(cx + 6, ey - 1, 4, 5)
            p.setPen(QPen(C_EYE, 2.5))
            p.drawLine(cx - 14, ey - 7, cx - 2, ey - 3)
            p.drawLine(cx + 14, ey - 7, cx + 2, ey - 3)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        else:
            # 龙眼（锐利）
            p.setBrush(QBrush(QColor(255, 240, 200)))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 5, 11, 11)
            p.drawEllipse(cx + 1, ey - 5, 11, 11)
            p.setBrush(QBrush(QColor(200, 100, 0)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 2, 5, 6)
            p.drawEllipse(cx + 5, ey - 2, 5, 6)
            # 竖瞳孔
            p.setBrush(QBrush(C_EYE))
            p.drawEllipse(cx - 6, ey - 1, 2, 5)
            p.drawEllipse(cx + 7, ey - 1, 2, 5)
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 5, ey - 3, 2, 2)
            p.drawEllipse(cx + 8, ey - 3, 2, 2)

    # ═══════════════════════════════════════════════
    #  幽幽 — 可爱幽灵
    # ═══════════════════════════════════════════════
    def _draw_ghost(self, p, cx, cy, c, mood, f):
        # 漂浮
        float_y = int(math.sin(f * 0.06) * 10)
        cy += float_y
        # 幽灵身体（上圆下飘）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 35, cy - 40, 70, 65)
        # 底部波浪飘动
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 1.5))
        for i in range(5):
            x = cx - 30 + i * 12
            wave = int(math.sin(f * 0.15 + i * 1.2) * 4)
            p.drawEllipse(x, cy + 18 + wave, 14, 12)
        # 半透明效果
        p.setBrush(QBrush(QColor(255, 255, 255, 40)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 15, cy - 30, 30, 25)
        # 眼睛（幽灵眼，空洞）
        self._draw_ghost_eyes(p, cx, cy - 10, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 5, mood, f)

    def _draw_ghost_eyes(self, p, cx, ey, mood, f):
        if mood in ("happy", "shy"):
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 12, ey - 4, 10, 8, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 4, 10, 8, 0, 180 * 16)
        elif mood == "angry":
            p.setBrush(QBrush(QColor(255, 200, 200)))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 4, 10, 9)
            p.drawEllipse(cx + 2, ey - 4, 10, 9)
            p.setPen(QPen(C_EYE, 2.5))
            p.drawLine(cx - 14, ey - 7, cx - 2, ey - 3)
            p.drawLine(cx + 14, ey - 7, cx + 2, ey - 3)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        else:
            # 空洞的幽灵眼
            p.setBrush(QBrush(QColor(30, 30, 60)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 11, ey - 5, 10, 12)
            p.drawEllipse(cx + 1, ey - 5, 10, 12)
            # 小高光
            p.setBrush(QBrush(QColor(255, 255, 255, 150)))
            p.drawEllipse(cx - 8, ey - 3, 3, 3)
            p.drawEllipse(cx + 4, ey - 3, 3, 3)

    # ═══════════════════════════════════════════════
    #  豆豆 — 呆萌机器人
    # ═══════════════════════════════════════════════
    def _draw_robot(self, p, cx, cy, c, mood, f):
        # 阴影
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 28, cy + 38, 56, 12)
        # 身体（方形圆角）
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawRoundedRect(cx - 35, cy - 32, 70, 65, 10, 10)
        # 天线
        p.setPen(QPen(c.darker(120), 2))
        p.drawLine(cx, cy - 32, cx, cy - 48)
        # 天线灯（闪烁）
        blink = abs(math.sin(f * 0.3))
        p.setBrush(QBrush(QColor(255, int(100 * blink), int(100 * blink))))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 4, cy - 52, 8, 8)
        # 螺栓装饰
        p.setBrush(QBrush(QColor(150, 170, 200)))
        p.drawEllipse(cx - 28, cy - 22, 6, 6)
        p.drawEllipse(cx + 22, cy - 22, 6, 6)
        p.drawEllipse(cx - 28, cy + 12, 6, 6)
        p.drawEllipse(cx + 22, cy + 12, 6, 6)
        # 屏幕脸（方形区域）
        p.setBrush(QBrush(QColor(200, 230, 255)))
        p.setPen(QPen(c.darker(130), 1))
        p.drawRoundedRect(cx - 22, cy - 18, 44, 30, 5, 5)
        # 机械手臂
        p.setBrush(QBrush(c.darker(110)))
        p.setPen(QPen(c.darker(120), 1.5))
        p.drawRoundedRect(cx - 48, cy - 10, 14, 25, 4, 4)
        p.drawRoundedRect(cx + 34, cy - 10, 14, 25, 4, 4)
        # 脚
        p.drawRoundedRect(cx - 22, cy + 28, 16, 12, 4, 4)
        p.drawRoundedRect(cx + 6, cy + 28, 16, 12, 4, 4)
        # 屏幕上的脸
        self._draw_robot_face(p, cx, cy - 8, mood, f)

    def _draw_robot_face(self, p, cx, ey, mood, f):
        if mood in ("happy", "shy"):
            # 像素开心眼
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            p.drawRect(cx - 14, ey - 2, 4, 4)
            p.drawRect(cx - 10, ey - 4, 4, 4)
            p.drawRect(cx - 6, ey - 2, 4, 4)
            p.drawRect(cx + 6, ey - 2, 4, 4)
            p.drawRect(cx + 10, ey - 4, 4, 4)
            p.drawRect(cx + 14, ey - 2, 4, 4)
        elif mood == "angry":
            p.setBrush(QBrush(C_ANGRY))
            p.setPen(Qt.NoPen)
            p.drawRect(cx - 14, ey - 4, 8, 4)
            p.drawRect(cx - 10, ey, 8, 4)
            p.drawRect(cx + 6, ey, 8, 4)
            p.drawRect(cx + 10, ey - 4, 8, 4)
        elif self.is_blinking:
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            p.drawRect(cx - 12, ey, 8, 2)
            p.drawRect(cx + 4, ey, 8, 2)
        else:
            # 像素方块眼
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            p.drawRect(cx - 14, ey - 4, 8, 8)
            p.drawRect(cx + 6, ey - 4, 8, 8)
            # 高光
            p.setBrush(QBrush(QColor(255, 255, 255, 150)))
            p.drawRect(cx - 12, ey - 2, 3, 3)
            p.drawRect(cx + 8, ey - 2, 3, 3)
        # 像素嘴
        p.setBrush(QBrush(C_MOUTH))
        p.setPen(Qt.NoPen)
        if mood in ("happy", "shy"):
            p.drawRect(cx - 6, ey + 8, 12, 2)
            p.drawRect(cx - 4, ey + 10, 8, 2)
        elif mood == "angry":
            p.drawRect(cx - 4, ey + 10, 8, 2)
            p.drawRect(cx - 6, ey + 8, 12, 2)
        else:
            p.drawRect(cx - 6, ey + 8, 12, 2)

    # ═══════════════════════════════════════════════
    #  火球 — 暴躁火球
    # ═══════════════════════════════════════════════
    def _draw_fireball(self, p, cx, cy, c, mood, f):
        # 火焰外层光晕
        p.setBrush(QBrush(QColor(255, 200, 50, 50)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 48, cy - 48, 96, 96)
        # 主火焰身体
        p.setBrush(QBrush(c))
        p.setPen(QPen(c.darker(120), 2))
        p.drawEllipse(cx - 35, cy - 32, 70, 65)
        # 火焰尖（多个椭圆）
        p.setBrush(QBrush(QColor(255, 220, 50)))
        p.setPen(Qt.NoPen)
        flame1 = int(18 + math.sin(f * 0.3) * 8)
        flame2 = int(14 + math.sin(f * 0.25 + 1) * 6)
        flame3 = int(12 + math.sin(f * 0.35 + 2) * 5)
        p.drawEllipse(cx - 6, cy - 32 - flame1, 12, flame1 + 5)
        p.drawEllipse(cx - 22, cy - 25 - flame2, 10, flame2 + 5)
        p.drawEllipse(cx + 12, cy - 25 - flame3, 10, flame3 + 5)
        # 内层火焰
        p.setBrush(QBrush(QColor(255, 255, 100, 180)))
        inner_h = int(10 + math.sin(f * 0.4) * 5)
        p.drawEllipse(cx - 4, cy - 28 - inner_h, 8, inner_h + 3)
        # 火焰粒子（飘散）
        p.setBrush(QBrush(QColor(255, 200, 50, 120)))
        for i in range(4):
            px = cx + int(math.cos(f * 0.08 + i * 1.5) * 30)
            py = cy - 35 - int((f * 0.5 + i * 10) % 30)
            p.drawEllipse(px, py, 4, 4)
        # 腮红（愤怒的红晕）
        p.setBrush(QBrush(QColor(255, 100, 50, 100)))
        p.drawEllipse(cx - 30, cy - 4, 12, 7)
        p.drawEllipse(cx + 18, cy - 4, 12, 7)
        # 眼睛（火球眼，暴躁）
        self._draw_fireball_eyes(p, cx, cy - 10, mood, f)
        # 嘴巴
        self._draw_mouth(p, cx, cy + 5, mood, f)

    def _draw_fireball_eyes(self, p, cx, ey, mood, f):
        if mood == "angry":
            # 愤怒火眼
            p.setBrush(QBrush(QColor(255, 255, 200)))
            p.setPen(QPen(QColor(200, 50, 0), 1.5))
            p.drawEllipse(cx - 12, ey - 5, 11, 11)
            p.drawEllipse(cx + 1, ey - 5, 11, 11)
            p.setBrush(QBrush(QColor(255, 50, 0)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 2, 5, 6)
            p.drawEllipse(cx + 5, ey - 2, 5, 6)
            # 愤怒眉毛
            p.setPen(QPen(QColor(200, 50, 0), 2.5))
            p.drawLine(cx - 14, ey - 6, cx - 2, ey - 9)
            p.drawLine(cx + 14, ey - 6, cx + 2, ey - 9)
        elif self.is_blinking:
            p.setPen(QPen(QColor(200, 100, 0), 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        else:
            # 火焰眼
            p.setBrush(QBrush(QColor(255, 255, 200)))
            p.setPen(QPen(QColor(200, 100, 0), 1.5))
            p.drawEllipse(cx - 12, ey - 5, 11, 11)
            p.drawEllipse(cx + 1, ey - 5, 11, 11)
            p.setBrush(QBrush(QColor(255, 150, 0)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 2, 5, 6)
            p.drawEllipse(cx + 5, ey - 2, 5, 6)
            # 火焰瞳孔
            p.setBrush(QBrush(QColor(200, 50, 0)))
            p.drawEllipse(cx - 6, ey, 3, 4)
            p.drawEllipse(cx + 7, ey, 3, 4)

    # ═══════════════════════════════════════════════
    #  通用绘制方法
    # ═══════════════════════════════════════════════
    def _draw_feet(self, p, cx, cy, mood, f):
        if mood == "walking":
            off = int(math.sin(f * 0.4) * 8)
            p.drawEllipse(cx - 22, cy + 32 + off, 16, 10)
            p.drawEllipse(cx + 6, cy + 32 - off, 16, 10)
        else:
            p.drawEllipse(cx - 22, cy + 32, 16, 10)
            p.drawEllipse(cx + 6, cy + 32, 16, 10)

    def _draw_face_standard(self, p, cx, ey, mood, f):
        """通用面部"""
        if mood in ("happy", "shy"):
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 14, ey - 5, 12, 10, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 5, 12, 10, 0, 180 * 16)
        elif mood == "angry":
            p.setBrush(QBrush(QColor(255, 200, 200)))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 4, 10, 9)
            p.drawEllipse(cx + 2, ey - 4, 10, 9)
            p.setBrush(QBrush(C_ANGRY))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 1, 4, 5)
            p.drawEllipse(cx + 6, ey - 1, 4, 5)
            p.setPen(QPen(C_EYE, 2.5))
            p.drawLine(cx - 14, ey - 7, cx - 2, ey - 3)
            p.drawLine(cx + 14, ey - 7, cx + 2, ey - 3)
        elif mood == "surprised":
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 14, ey - 6, 13, 14)
            p.drawEllipse(cx + 1, ey - 6, 13, 14)
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 9, ey - 2, 5, 6)
            p.drawEllipse(cx + 4, ey - 2, 5, 6)
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 8, ey - 4, 3, 3)
            p.drawEllipse(cx + 5, ey - 4, 3, 3)
        elif mood == "sweating":
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 3, 10, 8)
            p.drawEllipse(cx + 2, ey - 3, 10, 8)
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            shift = int(math.sin(f * 0.2) * 2)
            p.drawEllipse(cx - 8 + shift, ey, 4, 4)
            p.drawEllipse(cx + 5 + shift, ey, 4, 4)
        elif self.is_blinking:
            p.setPen(QPen(C_EYE, 2))
            p.drawLine(cx - 8, ey, cx - 2, ey)
            p.drawLine(cx + 2, ey, cx + 8, ey)
        elif mood == "sleeping":
            p.setPen(QPen(C_EYE, 2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx - 12, ey - 4, 10, 8, 0, 180 * 16)
            p.drawArc(cx + 2, ey - 4, 10, 8, 0, 180 * 16)
        else:
            p.setBrush(QBrush(C_EYE_WHITE))
            p.setPen(QPen(C_EYE, 1.5))
            p.drawEllipse(cx - 12, ey - 5, 12, 12)
            p.drawEllipse(cx + 0, ey - 5, 12, 12)
            p.setBrush(QBrush(C_EYE))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 8, ey - 2, 5, 5)
            p.drawEllipse(cx + 4, ey - 2, 5, 5)
            p.setBrush(QBrush(QColor(255, 255, 255, 200)))
            p.drawEllipse(cx - 7, ey - 4, 2, 2)
            p.drawEllipse(cx + 5, ey - 4, 2, 2)

        # 嘴巴
        self._draw_mouth(p, cx, ey + 12, mood, f)

    def _draw_mouth(self, p, cx, my, mood, f):
        p.setPen(QPen(C_MOUTH, 2))
        p.setBrush(Qt.NoBrush)
        if mood == "eating":
            p.setBrush(QBrush(C_MOUTH))
            phase = abs(math.sin(f * 0.5))
            p.drawEllipse(cx - 5, my - int(2 * phase), 10, int(6 * phase + 2))
        elif mood in ("happy", "shy"):
            p.drawArc(cx - 6, my - 3, 12, 10, 0, -180 * 16)
        elif mood == "sad":
            p.drawArc(cx - 6, my, 12, 10, 0, 180 * 16)
        elif mood == "angry":
            pts = [QPoint(cx - 6, my), QPoint(cx - 2, my + 3),
                   QPoint(cx + 2, my), QPoint(cx + 6, my + 3)]
            p.drawPolyline(pts)
        elif mood == "surprised":
            p.setBrush(QBrush(C_MOUTH))
            p.drawEllipse(cx - 4, my, 8, 8)
        elif mood == "talking":
            phase = abs(math.sin(f * 0.4))
            p.setBrush(QBrush(C_MOUTH))
            p.drawEllipse(cx - 4, my, 8, int(5 * phase + 2))
        else:
            p.drawArc(cx - 4, my - 2, 8, 6, 0, -180 * 16)

    def _draw_bubble(self, p, x, y):
        p.setOpacity(min(1.0, self.bubble_timer))
        p.setBrush(QBrush(QColor(255, 255, 255, 230)))
        p.setPen(QPen(QColor(200, 200, 200), 1))

        font = QFont("Microsoft YaHei", 9)
        p.setFont(font)
        metrics = p.fontMetrics()

        # 超长文本截断，避免气泡高到无法容纳
        text = self.bubble_text
        if len(text) > 60:
            text = text[:59] + "…"

        lines = []
        current = ""
        for char in text:
            test = current + char
            if metrics.horizontalAdvance(test) > 140:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)

        text_width = min(150, max(metrics.horizontalAdvance(l) for l in lines))
        total_height = len(lines) * 18 + 10
        bw = text_width + 16
        bx = x - bw // 2
        by = y - total_height
        # 钳制在窗口内：上方不再被裁掉，左右也不越界
        bx = max(2, min(self.width() - bw - 2, bx))
        by = max(2, by)

        p.drawRoundedRect(bx, by, bw, total_height, 8, 8)
        pts = [QPoint(x - 5, by + total_height), QPoint(x + 5, by + total_height),
               QPoint(x, by + total_height + 6)]
        p.drawPolygon(pts)

        p.setPen(QPen(QColor(60, 60, 60)))
        for i, line in enumerate(lines):
            p.drawText(bx + 8, by + 16 + i * 18, line)
        p.setOpacity(1.0)

    # ═══════════════════════════════════════════════
    #  交互菜单
    # ═══════════════════════════════════════════════
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = False
            self.pet.pet_head()
            self.show_bubble(self.pet.pet_head())
            play_sound("pet")
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.chat_requested.emit()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.is_dragging = True
            self.move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #ddd; border-radius: 6px;
                    padding: 5px; font-size: 13px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #e8f0fe; }
        """)

        status = menu.addAction(
            f"饱食:{int(self.pet.hunger)}  快乐:{int(self.pet.happiness)}  精力:{int(self.pet.energy)}")
        status.setEnabled(False)
        menu.addSeparator()

        feed_a = menu.addAction("喂食")
        pet_a = menu.addAction("摸头")
        play_a = menu.addAction("玩耍")
        tickle_a = menu.addAction("挠痒痒")
        lift_a = menu.addAction("举高高")
        ball_a = menu.addAction("扔球")
        compliment_a = menu.addAction("夸奖")
        flick_a = menu.addAction("弹额头")

        menu.addSeparator()

        game_menu = menu.addMenu("小游戏")
        rps_a = game_menu.addAction("猜拳")
        card_a = game_menu.addAction("翻牌记忆")
        ball_game_a = game_menu.addAction("接球")

        menu.addSeparator()

        skin_a = menu.addAction("换皮肤")
        change_pet_a = menu.addAction("换宠物")
        reminder_a = menu.addAction("设置提醒")

        weather_names = {"sunny": "Sunny", "cloudy": "多云", "rainy": "下雨",
                        "snowy": "下雪", "stormy": "雷暴"}
        weather_text = weather_names.get(self.weather.get("weather", "sunny"), "Sunny")
        temp = self.weather.get("temp", "?")
        weather_info = menu.addAction(f"{weather_text} {temp}C")
        weather_info.setEnabled(False)

        menu.addSeparator()

        chat_a = menu.addAction("聊天")
        settings_a = menu.addAction("设置")
        about_a = menu.addAction("关于")
        menu.addSeparator()

        # 开机自启动
        import autostart
        if autostart.is_autostart_enabled():
            autostart_a = menu.addAction("关闭开机自启")
        else:
            autostart_a = menu.addAction("开启开机自启")

        if self.pet.mood == "sleeping":
            wake_a = menu.addAction("唤醒")
            wake_a.triggered.connect(lambda: self._do_action("wake"))
        else:
            sleep_a = menu.addAction("睡觉")
            sleep_a.triggered.connect(lambda: self._do_action("sleep"))

        quit_a = menu.addAction("退出")

        feed_a.triggered.connect(lambda: self._do_action("feed"))
        pet_a.triggered.connect(lambda: self._do_action("pet"))
        play_a.triggered.connect(lambda: self._do_action("play"))
        tickle_a.triggered.connect(lambda: self._do_action("tickle"))
        lift_a.triggered.connect(lambda: self._do_action("lift"))
        ball_a.triggered.connect(lambda: self._do_action("ball"))
        compliment_a.triggered.connect(lambda: self._do_action("compliment"))
        flick_a.triggered.connect(lambda: self._do_action("flick"))
        chat_a.triggered.connect(self.chat_requested.emit)
        settings_a.triggered.connect(self.settings_requested.emit)
        about_a.triggered.connect(self.about_requested.emit)
        quit_a.triggered.connect(self._quit)

        rps_a.triggered.connect(lambda: self._open_game("rps"))
        card_a.triggered.connect(lambda: self._open_game("card"))
        ball_game_a.triggered.connect(lambda: self._open_game("ball"))

        skin_a.triggered.connect(self._open_skin_dialog)
        change_pet_a.triggered.connect(self.change_pet_requested.emit)
        reminder_a.triggered.connect(self._open_reminder_dialog)
        autostart_a.triggered.connect(self._toggle_autostart)

        menu.exec_(pos)

    def _do_action(self, action):
        replies = {
            "feed": self.pet.feed, "pet": self.pet.pet_head,
            "play": self.pet.play, "tickle": self.pet.tickle,
            "lift": self.pet.lift, "ball": self.pet.throw_ball,
            "compliment": self.pet.compliment, "flick": self.pet.flick,
            "sleep": self.pet.sleep, "wake": self.pet.wake,
        }
        sound_map = {
            "feed": "eat", "pet": "pet", "play": "happy",
            "tickle": "surprise", "lift": "surprise",
            "ball": "ball", "compliment": "happy",
            "flick": "angry", "sleep": "sleep", "wake": "happy",
        }
        fn = replies.get(action)
        if fn:
            reply = fn()
            if reply:
                self.show_bubble(reply)
                play_sound(sound_map.get(action, "happy"))

    def _quit(self):
        self.pet.save()
        QApplication.quit()

    def _open_game(self, game_type):
        from games import RockPaperScissors, CardFlip, CatchBall
        classes = {"rps": RockPaperScissors, "card": CardFlip, "ball": CatchBall}
        cls = classes.get(game_type)
        if cls is None:
            return
        # 必须持有引用，否则局部变量被GC后窗口会消失
        if not hasattr(self, "_games"):
            self._games = {}
        game = self._games.get(game_type)
        if game is None:
            game = cls(self.pet, self)
            game.setAttribute(Qt.WA_DeleteOnClose)
            game.destroyed.connect(lambda: self._games.pop(game_type, None))
            self._games[game_type] = game
        game.show()
        game.raise_()
        game.activateWindow()

    def _open_skin_dialog(self):
        from features import SkinDialog
        dialog = SkinDialog(self.skin_name, self)
        dialog.skin_changed.connect(self._apply_skin)
        dialog.exec_()

    def _apply_skin(self, name):
        self.skin_name = name
        self.skin_colors = SKINS.get(name, SKINS["默认蓝"])
        # 换肤后清掉染色缓存，立即按新颜色重绘
        self._tint_cache = {}
        self.update()
        self.show_bubble(f"换成了{name}~好看吗？")

    def _open_reminder_dialog(self):
        from features import ReminderDialog
        dialog = ReminderDialog(self)
        dialog.exec_()
        self.reminder_checker.reload()

    def _on_reminder(self, message):
        self.show_bubble(f"提醒: {message}", duration=5)
        self.pet.mood = "surprised"
        self.pet.mood_timer = 3

    def _toggle_autostart(self):
        import autostart
        if autostart.is_autostart_enabled():
            autostart.disable_autostart()
            self.show_bubble("已关闭开机自启")
        else:
            if autostart.enable_autostart():
                self.show_bubble("已开启开机自启！")
            else:
                self.show_bubble("开启失败")


# ─── 聊天窗口 ─────────────────────────────────────
class ChatInput(QLineEdit):
    """跟踪中文输入法组词状态：组词中按Enter是让候选词上屏，不应触发发送。
    否则上屏的最后一个字会在text()读取后才提交，导致发送内容缺末字。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ime_composing = False

    def inputMethodEvent(self, event):
        # 有预编辑串=组词中；提交时preedit为空、commitString有值
        self.ime_composing = bool(event.preeditString())
        super().inputMethodEvent(event)


class ChatWindow(QWidget):

    # AI回复在后台线程产生，用信号投递回GUI线程（线程安全）
    reply_received = pyqtSignal(str)

    def __init__(self, pet_state, chat_ai):
        super().__init__()
        self.pet = pet_state
        self.chat_ai = chat_ai
        self.reply_received.connect(self._on_reply)

        self.setWindowTitle(f"Chat with {pet_state.name}")
        self.setFixedSize(350, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setStyleSheet("""
            QWidget { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QTextEdit { background: white; border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 10px; font-size: 13px; }
            QLineEdit { border: 1px solid #ddd; border-radius: 15px; padding: 8px 15px; font-size: 13px; }
            QLineEdit:focus { border-color: #78dcff; }
            QPushButton { background: #78dcff; color: white; border: none; border-radius: 15px;
                          padding: 8px 20px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #5bc0f0; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel(f"Chat with {pet_state.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; padding: 5px;")
        layout.addWidget(title)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_field = ChatInput()
        self.input_field.setPlaceholderText("说点什么...")
        self.input_field.returnPressed.connect(self._send)
        input_layout.addWidget(self.input_field)

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._send)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

        self._load_history()

    def _load_history(self):
        for msg in self.pet.chat_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                self._append_message("You", content, "#333")
            else:
                self._append_message(self.pet.name, content, "#78dcff")

    def _send(self):
        # 中文输入法组词中按Enter是确认候选词，不发送（再按一次Enter才发送）
        if getattr(self.input_field, "ime_composing", False):
            return
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._append_message("You", text, "#333")
        self._append_message(self.pet.name, "思考中...", "#999")

        self.chat_ai.chat(text, callback=self.reply_received.emit)

    def _on_reply(self, reply):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self._append_message(self.pet.name, reply, "#78dcff")

    def _append_message(self, sender, text, color):
        html = f'<p style="margin: 4px 0;"><b style="color: {color};">{sender}:</b> {text}</p>'
        self.chat_display.append(html)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
