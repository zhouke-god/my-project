"""
sprites.py — 像素美术精灵生成器 v3
借鉴手绘像素画技法重绘：Q版比例 / 深色描边 / cel四段阴影+边缘光 / 大眼睛高光 / 眨眼呼吸动画
用 PIL 逐像素生成，无需外部素材
"""
import os
from PIL import Image

SPRITE_SIZE = 96  # 96x96 真 1px 像素（更精致、显示更大）
SPRITE_DIR = "sprites"
SPRITE_VERSION = 4  # 美术风格版本号：升级后自动重新生成

PETS = ["blob", "cat", "dog", "rabbit", "dragon", "ghost", "robot", "fireball"]

# 生成到磁盘的正规心情
MOODS = ["idle", "happy", "sad", "eating", "sleeping", "angry", "surprised", "talking", "shy"]

# 未单独绘制的心情 → 映射到最近的正规心情（保证所有心情都走像素精灵图）
MOOD_ALIASES = {
    "stretching": "happy",
    "rolling": "happy",
    "walking": "idle",
    "looking": "idle",
    "dizzy": "surprised",
    "sweating": "surprised",
}

# ─── 调色板（每只宠物一套有限配色）────────────────
PALETTES = {
    "blob": {
        "base": (96, 200, 248), "light": (176, 232, 255), "dark": (52, 148, 210),
        "outline": (28, 72, 108), "eye": (36, 46, 70), "cheek": (255, 168, 188),
    },
    "cat": {
        "base": (255, 198, 130), "light": (255, 232, 190), "dark": (226, 156, 86),
        "outline": (114, 74, 40), "eye": (42, 48, 64), "cheek": (255, 160, 150),
        "inner": (255, 158, 168),
    },
    "dog": {
        "base": (210, 168, 108), "light": (240, 204, 152), "dark": (166, 122, 68),
        "outline": (94, 62, 34), "eye": (50, 38, 28), "cheek": (255, 170, 150),
        "ear": (148, 106, 56), "tongue": (255, 140, 150),
    },
    "rabbit": {
        "base": (255, 216, 226), "light": (255, 244, 248), "dark": (230, 176, 194),
        "outline": (132, 86, 100), "eye": (58, 46, 56), "cheek": (255, 158, 178),
        "inner": (255, 168, 188), "tail": (255, 255, 255),
    },
    "dragon": {
        "base": (146, 214, 138), "light": (198, 242, 188), "dark": (90, 172, 90),
        "outline": (46, 94, 50), "eye": (38, 54, 38), "cheek": (255, 190, 160),
        "horn": (255, 210, 90), "belly": (255, 246, 200), "flame": (255, 150, 60),
    },
    "ghost": {
        "base": (216, 216, 246), "light": (246, 246, 255), "dark": (170, 170, 214),
        "outline": (86, 86, 130), "eye": (50, 50, 82), "cheek": (216, 180, 226),
    },
    "robot": {
        "base": (190, 204, 224), "light": (230, 239, 250), "dark": (136, 152, 180),
        "outline": (60, 70, 94), "eye": (130, 230, 255), "cheek": None,
        "screen": (32, 42, 64), "antenna": (255, 96, 96), "bolt": (108, 120, 146),
    },
    "fireball": {
        "base": (255, 134, 86), "light": (255, 198, 118), "dark": (216, 86, 50),
        "outline": (122, 46, 24), "eye": (64, 32, 20), "cheek": (255, 190, 130),
        "flame": (255, 176, 60), "flame_hi": (255, 226, 110),
    },
}

MOUTH_RIM = (140, 55, 65)
MOUTH_IN = (168, 66, 76)
TONGUE = (255, 150, 160)
WHITE = (255, 255, 255)
CRUMB = (245, 222, 170)

CX = 48           # 身体中心 x
BODY_CY = 56      # 身体中心 y
EYE_Y = 46        # 左眼上沿
MOUTH_Y = 60      # 嘴上沿
BOB = [0, -1, 0, 1]  # 4 帧呼吸浮动

# 每只宠物的身体轮廓参数 (rx, ry, p)：轮廓差异化
# rx=半宽 ry=半高 p=超椭圆指数(越大越方)
BODY_PARAMS = {
    "blob":     (27, 18, 2.4),   # 团子：扁圆
    "cat":      (23, 19, 2.8),   # 小喵：略窄
    "dog":      (27, 18, 2.5),   # 汪仔：矮宽敦实
    "rabbit":   (20, 22, 3.0),   # 兔叽：瘦高
    "dragon":   (25, 19, 2.6),   # 小龙：壮实
    "robot":    (22, 21, 6.0),   # 豆豆：明显方形
    "fireball": (20, 19, 2.2),   # 火球：正圆
    # ghost 走专用绘制
}


def _mix(c1, c2, t):
    """颜色插值：t=0 → c1，t=1 → c2"""
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


# ═══════════════════════════════════════════════
#  基础工具
# ═══════════════════════════════════════════════
def _put(px, x, y, color):
    if 0 <= x < SPRITE_SIZE and 0 <= y < SPRITE_SIZE and color:
        px[x, y] = color


def _stamp(px, x0, y0, rows, cmap):
    """把字符串像素画盖到画布上：'.' 透明，其余字符查 cmap 取色"""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != ".":
                c = cmap.get(ch)
                if c:
                    _put(px, x0 + dx, y0 + dy, c)


def _mirror(rows):
    return [row[::-1] for row in rows]


def _disc(px, cx, cy, rx, ry, color):
    """实心椭圆"""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            nx, ny = (x - cx) / max(rx, 0.1), (y - cy) / max(ry, 0.1)
            if nx * nx + ny * ny <= 1:
                _put(px, x, y, color)


# ═══════════════════════════════════════════════
#  身体（超椭圆 + cel 四段阴影：左上边缘光 / 右下暗部 / 底部加深）
# ═══════════════════════════════════════════════
def _body_super(px, cx, cy, rx, ry, p, pal):
    deep = _mix(pal["dark"], pal["outline"], 0.35)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            d = abs(nx) ** p + abs(ny) ** p
            if d <= 1.0:
                c = pal["base"]
                if ny > 0.62 and d > 0.55:
                    c = deep                      # 底部加深，增加体积感
                elif d > 0.55 and nx * 0.55 + ny * 0.75 > 0.15:
                    c = pal["dark"]               # 右下暗部
                elif nx < -0.18 and ny < -0.12 and d > 0.15:
                    c = pal["light"]              # 左上受光
                _put(px, x, y, c)
    # 主高光点
    hx, hy = cx - int(rx * 0.45), cy - int(ry * 0.55)
    _stamp(px, hx, hy, ["###", "##.", "#.."], {"#": (255, 255, 255, 110)})
    # 次高光（更小更弱，增加通透感）
    _stamp(px, hx + 4, hy + 3, ["##"], {"#": (255, 255, 255, 70)})


def _body_ghost(px, cx, cy, pal, frame):
    """幽灵：上圆顶 + 直筒 + 波浪下摆（无脚）"""
    rx, ry = 21, 17
    deep = _mix(pal["dark"], pal["outline"], 0.35)
    for x in range(cx - rx, cx + rx + 1):
        nx = (x - cx) / rx
        top = cy - round(ry * (1 - nx * nx) ** 0.5)
        wave = 3 if ((x - cx) // 4 + frame) % 2 == 0 else 0
        bottom = 73 + wave
        for y in range(top, bottom + 1):
            ny = (y - cy) / ry
            d = nx * nx + ny * ny
            c = pal["base"]
            if y > 70:
                c = deep
            elif (d > 0.55 and nx * 0.55 + ny * 0.75 > 0.15) or x >= cx + rx - 1:
                c = pal["dark"]
            elif nx < -0.25 and y < cy:
                c = pal["light"]
            _put(px, x, y, c)
    hx, hy = cx - 9, cy - 10
    _stamp(px, hx, hy, ["###", "##.", "#.."], {"#": (255, 255, 255, 110)})


def _feet(px, cx, base_y, pal, style="round"):
    if style == "none":
        return
    if style == "tread":  # 机器人履带脚
        for dx in (-13, 4):
            for x in range(cx + dx, cx + dx + 9):
                for y in range(base_y, base_y + 5):
                    _put(px, x, y, pal["dark"])
            _put(px, cx + dx + 4, base_y + 2, pal["outline"])
            _put(px, cx + dx + 1, base_y + 1, pal["bolt"])
            _put(px, cx + dx + 7, base_y + 1, pal["bolt"])
        return
    for fx in (cx - 9, cx + 9):
        _disc(px, fx, base_y + 1, 6, 3.5, pal["dark"])


# ═══════════════════════════════════════════════
#  表情像素画（#=主色 W=高光 M=口腔 T=舌头）
#  大眼睛 + 双高光 = 精致感核心
# ═══════════════════════════════════════════════
EYE_NORMAL = [
    "..###..",
    ".#####.",
    "##WW###",
    "#WW####",
    "#######",
    "#####W#",
    ".#####.",
    "..###..",
]
EYE_HAPPY = [   # ∩ 眯眯眼
    "..###..",
    ".##.##.",
    "##...##",
    "#.....#",
]
EYE_CLOSED = [  # 眨眼
    "#######",
    ".#####.",
]
EYE_SLEEP_L = [
    ".#####.",
    "##...##",
    "#......",
]
EYE_SAD = [
    ".#####.",
    "##WW###",
    "#WW####",
    "#######",
    "#######",
    ".#####.",
]
BROW_SAD_L = [  # 八字眉（左）
    "...##",
    ".##..",
    "##...",
]
EYE_ANGRY_L = [
    "....###",
    "..#####",
    ".#WW###",
    "##W####",
    "#######",
    ".#####.",
]
EYE_SURPRISED = [
    "..###..",
    ".#####.",
    "##WWW##",
    "#W###W#",
    "#W###W#",
    "##WWW##",
    ".#####.",
    "..###..",
]

M_IDLE = [      # 小微笑
    "#.....#",
    ".##.##.",
    "..###..",
]
M_HAPPY = [     # 张嘴笑 + 舌头
    ".#######.",
    "#MMMMMMM#",
    "#MMTTTMM#",
    ".#TTTTT#.",
    "..#####..",
]
M_SAD = [       # 撇嘴
    "..###..",
    ".##.##.",
    "##...##",
]
M_O = [         # 小圆嘴
    ".###.",
    "#MMM#",
    "#MMM#",
    ".###.",
]
M_SURPRISED = [ # 大圆嘴
    "..###..",
    ".#####.",
    "##MMM##",
    "#MMMMM#",
    "##MMM##",
    ".#####.",
    "..###..",
]
M_ANGRY = [     # 咬牙锯齿
    "#...#...#",
    ".#.#.#.#.",
    "..#...#..",
    ".#.#.#.#.",
]
M_SHY = [       # 抿嘴笑
    "#.....#",
    ".##.##.",
]

Z_BIG = [
    "######",
    "....#.",
    "...#..",
    "..#...",
    ".#....",
    "######",
]
Z_SMALL = [
    "####",
    "..#.",
    ".#..",
    "####",
]


def _eye_cmap(pal):
    return {"#": pal["eye"], "W": WHITE}


def _mouth_cmap():
    return {"#": MOUTH_RIM, "M": MOUTH_IN, "T": TONGUE}


def _draw_eyes(px, mood, frame, pal, eye_y):
    """双眼 + 眉毛。左眼锚点 CX-14，右眼 CX+7（7px 宽）"""
    blink = frame == 2 and mood in ("idle", "sad", "angry", "talking")
    cmap = _eye_cmap(pal)

    if mood in ("happy", "eating", "shy"):
        _stamp(px, CX - 14, eye_y + 2, EYE_HAPPY, cmap)
        _stamp(px, CX + 7, eye_y + 2, EYE_HAPPY, cmap)
    elif mood == "sleeping":
        _stamp(px, CX - 14, eye_y + 3, EYE_SLEEP_L, cmap)
        _stamp(px, CX + 7, eye_y + 3, _mirror(EYE_SLEEP_L), cmap)
    elif mood == "surprised":
        _stamp(px, CX - 14, eye_y - 1, EYE_SURPRISED, cmap)
        _stamp(px, CX + 7, eye_y - 1, EYE_SURPRISED, cmap)
    elif blink:
        _stamp(px, CX - 14, eye_y + 3, EYE_CLOSED, cmap)
        _stamp(px, CX + 7, eye_y + 3, EYE_CLOSED, cmap)
    elif mood == "sad":
        _stamp(px, CX - 14, eye_y, EYE_SAD, cmap)
        _stamp(px, CX + 7, eye_y, _mirror(EYE_SAD), cmap)
        _stamp(px, CX - 14, eye_y - 4, BROW_SAD_L, cmap)
        _stamp(px, CX + 9, eye_y - 4, _mirror(BROW_SAD_L), cmap)
    elif mood == "angry":
        _stamp(px, CX - 14, eye_y, EYE_ANGRY_L, cmap)
        _stamp(px, CX + 7, eye_y, _mirror(EYE_ANGRY_L), cmap)
    else:  # idle / talking
        _stamp(px, CX - 14, eye_y, EYE_NORMAL, cmap)
        _stamp(px, CX + 7, eye_y, EYE_NORMAL, cmap)


def _draw_mouth(px, mood, frame, pet_type, mouth_y):
    cmap = _mouth_cmap()
    cx = CX
    if pet_type == "robot":
        cmap = {"#": pal_safe(pet_type, "eye"), "M": (70, 130, 160), "T": TONGUE}

    if mood == "happy" or mood == "eating":
        _stamp(px, cx - 4, mouth_y, M_HAPPY, cmap)
        if mood == "eating":
            _put(px, cx - 11, mouth_y + 5, CRUMB)
            _put(px, cx + 10, mouth_y + 6, CRUMB)
    elif mood == "sad":
        _stamp(px, cx - 3, mouth_y + 1, M_SAD, cmap)
    elif mood == "sleeping":
        _stamp(px, cx - 2, mouth_y, M_O, cmap)
    elif mood == "angry":
        _stamp(px, cx - 4, mouth_y + 1, M_ANGRY, cmap)
    elif mood == "surprised":
        _stamp(px, cx - 3, mouth_y - 2, M_SURPRISED, cmap)
    elif mood == "shy":
        _stamp(px, cx - 3, mouth_y, M_SHY, cmap)
    elif mood == "talking":
        rows = M_O if frame % 2 == 0 else M_IDLE
        _stamp(px, cx - 2 if rows is M_O else cx - 3, mouth_y, rows, cmap)
    else:  # idle
        _stamp(px, cx - 3, mouth_y, M_IDLE, cmap)


def _draw_cheeks(px, mood, pet_type, pal, cheek_y):
    if pet_type == "robot" or not pal.get("cheek"):
        return
    if mood in ("angry", "surprised", "sleeping"):
        return
    w = 7 if mood == "shy" else 5
    rows = ["." + "C" * (w - 2) + ".", "C" * w, "." + "C" * (w - 2) + "."]
    cmap = {"C": pal["cheek"]}
    _stamp(px, CX - 21, cheek_y, rows, cmap)
    _stamp(px, CX + 21 - w, cheek_y, rows, cmap)


def pal_safe(pet_type, key):
    return PALETTES.get(pet_type, PALETTES["blob"]).get(key) or PALETTES["blob"]["eye"]


def _draw_zzz(px, frame):
    color = (170, 180, 220)
    _stamp(px, 66, 30 - frame, Z_BIG, {"#": color})
    _stamp(px, 76, 20 - frame, Z_SMALL, {"#": color})


# ═══════════════════════════════════════════════
#  每只宠物的装饰层
# ═══════════════════════════════════════════════
def _acc_behind(px, pet_type, pal, frame):
    """身体之后的装饰：耳朵 / 角 / 翅膀 / 尾巴 / 天线"""
    if pet_type == "cat":
        # 大三角耳：明显超出头顶，带内耳
        ear = [
            "b............",
            "bbb..........",
            "bbbb.........",
            "bbbbb........",
            "bbbbbb.......",
            "bbbbbii......",
            "bbbbbbii.....",
            "bbbbbbbiii...",
            "bbbbbbbbiii..",
            "bbbbbbbbbiiii",
            "dbbbbbbbbbbbb",
            "ddbbbbbbbbbbb",
        ]
        cmap = {"b": pal["base"], "d": pal["dark"], "i": pal["inner"]}
        _stamp(px, 27, 21, ear, cmap)
        _stamp(px, 56, 21, _mirror(ear), cmap)
        # 尾巴（右后侧，帧间摆动）
        wag = [0, 1, 0, -1][frame]
        tail = [(70, 69), (74, 66), (77, 63), (79, 59), (80, 55)]
        for i, (tx, ty) in enumerate(tail):
            c = pal["dark"] if i >= len(tail) - 2 else pal["base"]
            ox = wag if i >= len(tail) - 2 else 0
            _put(px, tx + ox, ty, c)
            _put(px, tx + ox + 1, ty, c)
            _put(px, tx + ox, ty + 1, c)
            _put(px, tx + ox + 1, ty + 1, c)

    elif pet_type == "dog":
        # 长垂耳：从头侧垂到肩部，耳尖加深
        ear = [
            "eeeeeeee..",
            "eeeeeeeee.",
            "eeeeeeeee.",
            "eeeeeeee..",
            "eeeeeeee..",
            "eeeeeee...",
            "eeeeeee...",
            "eeeeeee...",
            ".eeeeee...",
            ".eeeeee...",
            ".eeeee....",
            "..eeeee...",
            "..dddd....",
            "..dddd....",
            "...ddd....",
            "...dd.....",
        ]
        cmap = {"e": pal["ear"], "d": pal["dark"]}
        _stamp(px, 18, 34, ear, cmap)
        _stamp(px, 68, 34, _mirror(ear), cmap)
        # 摇尾巴
        wag = [0, -1, 0, 1][frame]
        for i, (tx, ty) in enumerate([(70, 66), (74, 63), (76, 60)]):
            _stamp(px, tx + (wag if i == 2 else 0), ty, ["ttt", "ttt"], {"t": pal["dark"]})

    elif pet_type == "rabbit":
        # 超长兔耳：24 行高，三段式微弯
        ear = [
            ".bbbb.",
            ".bbbb.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".biib.",
            ".bbbb.",
            ".bbbb.",
            ".bbbb.",
            ".bbbb.",
            ".bbbb.",
            ".bbbb.",
        ]
        cmap = {"b": pal["base"], "i": pal["inner"]}
        # 耳尖外撇，更灵动
        _stamp(px, 33, 8, ear[:8], cmap)
        _stamp(px, 32, 16, ear[8:16], cmap)
        _stamp(px, 31, 24, ear[16:], cmap)
        ear_r = _mirror(ear)
        _stamp(px, 57, 8, ear_r[:8], cmap)
        _stamp(px, 58, 16, ear_r[8:16], cmap)
        _stamp(px, 59, 24, ear_r[16:], cmap)
        # 棉花尾巴
        _disc(px, 71, 67, 5, 5, pal["tail"])

    elif pet_type == "dragon":
        # 弯角（带尖端）
        horn_l = [
            "...hh.",
            "..hhh.",
            ".hhhh.",
            "hhhh..",
            "hhh...",
            "hhh...",
        ]
        cmap_h = {"h": pal["horn"]}
        _stamp(px, 35, 24, horn_l, cmap_h)
        _stamp(px, 55, 24, _mirror(horn_l), cmap_h)
        # 展开的大翅膀：深色骨架 + 浅色翼膜（帧间扇动）
        flap = [0, -1, 0, 1][frame]
        wing = [
            "ww.............",
            "wwww...........",
            "wllwwww........",
            "wllllwwwww.....",
            "wllllllwwwww...",
            "wllwwwwllwwwwww",
            "wlw...wwllwwwww",
            "ww.....wwllwwww",
            "w.......wwllwww",
        ]
        cmap_w = {"w": pal["dark"], "l": pal["light"]}
        _stamp(px, 6, 38 + flap, wing, cmap_w)
        _stamp(px, 75, 38 + flap, _mirror(wing), cmap_w)
        # 尾巴 + 火焰尖
        for tx, ty in [(72, 68), (76, 65), (78, 62)]:
            _stamp(px, tx, ty, ["ttt", "ttt"], {"t": pal["dark"]})
        _stamp(px, 78, 59 - frame % 2, ["fff", "fff"], {"f": pal["flame"]})

    elif pet_type == "ghost":
        # 小手
        _stamp(px, 22, 56, [".bb.", "bbbb", "bbbb", ".bb."], {"b": pal["base"]})
        _stamp(px, 70, 56, [".bb.", "bbbb", "bbbb", ".bb."], {"b": pal["base"]})

    elif pet_type == "robot":
        # 天线：立杆 + 发光大圆球
        for y in range(25, 32):
            _put(px, 47, y, pal["dark"])
            _put(px, 48, y, pal["dark"])
        tip = pal["antenna"] if frame != 2 else (255, 170, 130)
        ball = [
            "...aaa...",
            "..aaaaa..",
            ".aaaaaaa.",
            "aaaaaaaaa",
            "aaaaaaaaa",
            "aaaaaaaaa",
            ".aaaaaaa.",
            "..aaaaa..",
            "...aaa...",
        ]
        _stamp(px, 43, 16, ball, {"a": tip})
        _stamp(px, 45, 18, ["##"], {"#": (255, 255, 255, 160)})  # 球面高光
        # 两侧雷达圆盘耳
        disc = [
            "..bbbb..",
            ".bbbbbb.",
            "bbwwwwbb",
            "bbwwwwbb",
            "bbwbbwbb",
            "bbwwwwbb",
            "bbwwwwbb",
            ".bbbbbb.",
            "..bbbb..",
        ]
        cmap_d = {"b": pal["bolt"], "w": pal["light"]}
        _stamp(px, 8, 44, disc, cmap_d)
        _stamp(px, 80, 44, disc, cmap_d)

    elif pet_type == "fireball":
        # 头顶火焰鬃毛：五簇高火苗（帧间闪烁），带亮芯
        flicker = [(0, 1, 0, 1, 0), (1, 0, 1, 0, 1), (0, 1, 0, 1, 0), (1, 0, -1, 0, 1)][frame]
        base_h = [10, 14, 18, 14, 10]
        for i, fx in enumerate((36, 42, 48, 54, 60)):
            h = base_h[i] + flicker[i]
            for lvl in range(h):
                w = 3 if lvl < 3 else 2 if lvl < h - 4 else 1 if lvl < h - 1 else 0
                c = pal["flame"] if lvl < h - 3 else pal["flame_hi"]
                for dx in range(-w, w + 1):
                    _put(px, fx + dx, 38 - lvl, c)
                if lvl < h - 6 and w >= 2:  # 亮芯
                    _put(px, fx, 38 - lvl, pal["flame_hi"])
        # 火星
        _put(px, 30, 28 + frame, pal["flame_hi"])
        _put(px, 66, 25 + (3 - frame), pal["flame"])


def _acc_front(px, pet_type, pal, frame, mood):
    """身体之前的装饰：胡须 / 呆毛 / 肚皮 / 屏幕"""
    if pet_type == "cat":
        wh = (150, 130, 110)
        for wy in (54, 57):
            for i in range(6):
                _put(px, 18 + i, wy, wh)
                _put(px, 72 + i, wy, wh)

    elif pet_type == "blob":
        # 呆毛（两撮，更有灵性）
        hair = [
            "...bb.....",
            "..bb......",
            "..b.......",
            "..b...b...",
            ".bb...bb..",
            ".b.....b..",
        ]
        _stamp(px, 43, 30, hair, {"b": pal["base"]})

    elif pet_type == "dragon":
        # 浅色肚皮
        for y in range(58, 74):
            for x in range(37, 60):
                nx, ny = (x - 48) / 11, (y - 66) / 7.5
                if nx * nx + ny * ny <= 1:
                    _put(px, x, y, pal["belly"])

    elif pet_type == "robot":
        # 面部屏幕（深色面板）
        for y in range(40, 60):
            for x in range(31, 66):
                nx, ny = (x - 48) / 17, (y - 50) / 10
                if abs(nx) ** 4 + abs(ny) ** 4 <= 1:
                    _put(px, x, y, pal["screen"])
        # 机身铆钉
        for bx, by in [(30, 68), (64, 68), (30, 42), (64, 42)]:
            _stamp(px, bx, by, ["bb", "bb"], {"b": pal["bolt"]})


# ═══════════════════════════════════════════════
#  描边 + 投影
# ═══════════════════════════════════════════════
def _apply_outline(img, outline):
    """8 邻域自动描边：透明像素若挨着实体则变为深色轮廓"""
    px = img.load()
    marks = []
    for y in range(SPRITE_SIZE):
        for x in range(SPRITE_SIZE):
            if px[x, y][3] == 0:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < SPRITE_SIZE and 0 <= ny < SPRITE_SIZE:
                            if px[nx, ny][3] > 200:
                                marks.append((x, y))
                                break
                    else:
                        continue
                    break
    for x, y in marks:
        px[x, y] = outline


def _draw_shadow(img, pet_type):
    px = img.load()
    cx, cy, rx, ry = 48, 86, 20, 4
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(cx - rx, cx + rx + 1):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            d = nx * nx + ny * ny
            if d <= 1 and px[x, y][3] == 0:
                alpha = 70 if d <= 0.4 else 40
                px[x, y] = (20, 25, 40, alpha)


# ═══════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════
def create_sprite(pet_type, mood="idle", frame=0):
    """创建指定宠物的像素精灵图"""
    if pet_type not in PALETTES:
        pet_type = "blob"
    mood = MOOD_ALIASES.get(mood, mood)
    if mood not in MOODS:
        mood = "idle"
    frame = frame % 4

    img = Image.new("RGBA", (SPRITE_SIZE, SPRITE_SIZE), (0, 0, 0, 0))
    px = img.load()
    pal = PALETTES[pet_type]

    bob = BOB[frame] if mood != "sleeping" else 0
    cy = BODY_CY + bob

    _acc_behind(px, pet_type, pal, frame)

    if pet_type == "ghost":
        _body_ghost(px, CX, cy - 1, pal, frame)
        body_bottom = BODY_CY + 17
    else:
        rx, ry, pw = BODY_PARAMS.get(pet_type, (24, 19, 3))
        _body_super(px, CX, cy, rx, ry, pw, pal)
        body_bottom = BODY_CY + ry

    foot_style = {"ghost": "none", "fireball": "none", "robot": "tread"}.get(pet_type, "round")
    _feet(px, CX, body_bottom, pal, foot_style)

    _acc_front(px, pet_type, pal, frame, mood)

    eye_y = EYE_Y + bob
    mouth_y = MOUTH_Y + bob
    if pet_type == "robot":
        eye_y, mouth_y = EYE_Y - 3 + bob, MOUTH_Y - 6 + bob
    _draw_eyes(px, mood, frame, pal, eye_y)
    _draw_mouth(px, mood, frame, pet_type, mouth_y)
    _draw_cheeks(px, mood, pet_type, pal, EYE_Y + 10 + bob)

    if pet_type == "dog" and mood in ("idle", "happy", "talking"):
        _stamp(px, CX - 1, MOUTH_Y + 3 + bob, ["ttt", "ttt"], {"t": pal["tongue"]})

    if mood == "sleeping":
        _draw_zzz(px, frame)

    _apply_outline(img, pal["outline"])
    _draw_shadow(img, pet_type)
    return img


def generate_all_sprites():
    """生成所有宠物的所有状态精灵图"""
    os.makedirs(SPRITE_DIR, exist_ok=True)
    for pet in PETS:
        pet_dir = os.path.join(SPRITE_DIR, pet)
        os.makedirs(pet_dir, exist_ok=True)
        for mood in MOODS:
            for frame in range(4):
                img = create_sprite(pet, mood, frame)
                img.save(os.path.join(pet_dir, f"{mood}_{frame}.png"))
    with open(os.path.join(SPRITE_DIR, "_version.txt"), "w") as f:
        f.write(str(SPRITE_VERSION))
    print(f"[Sprites] 生成完成: {SPRITE_DIR}/ ({len(PETS)}只 x {len(MOODS)}心情 x 4帧)")


def ensure_sprites():
    """精灵图缺失或美术版本过旧时自动重新生成"""
    marker = os.path.join(SPRITE_DIR, "_version.txt")
    current = None
    if os.path.exists(marker):
        try:
            with open(marker, "r") as f:
                current = f.read().strip()
        except Exception:
            pass
    if current != str(SPRITE_VERSION):
        print(f"[Sprites] 检测到新版本美术 (v{SPRITE_VERSION})，重新生成精灵图...")
        generate_all_sprites()


def get_sprite_path(pet_type, mood="idle", frame=0):
    """获取精灵图路径（未绘制的心情自动映射到最近的正规心情）"""
    mood = MOOD_ALIASES.get(mood, mood)
    path = os.path.join(SPRITE_DIR, pet_type, f"{mood}_{frame % 4}.png")
    if not os.path.exists(path):
        path = os.path.join(SPRITE_DIR, pet_type, f"idle_{frame % 4}.png")
    return path


def _make_preview():
    """生成预览拼图，方便肉眼检查美术效果"""
    show_moods = ["idle", "happy", "sleeping", "angry"]
    cell = SPRITE_SIZE * 2
    sheet = Image.new("RGBA", (len(PETS) * cell, len(show_moods) * cell), (44, 48, 64, 255))
    for i, pet in enumerate(PETS):
        for j, mood in enumerate(show_moods):
            sprite = create_sprite(pet, mood, 0).resize((cell, cell), Image.NEAREST)
            sheet.paste(sprite, (i * cell, j * cell), sprite)
    out = os.path.join(SPRITE_DIR, "_preview.png")
    sheet.save(out)
    print(f"[Sprites] 预览图: {out}")


if __name__ == "__main__":
    generate_all_sprites()
    _make_preview()
