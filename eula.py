"""
eula.py — 版权声明 + 用户协议
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt


COPYRIGHT_TEXT = """
MIT License

Copyright (c) 2026 AI桌面宠物团队

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""".strip()


EULA_TEXT = """
AI桌面宠物 — 最终用户许可协议 (EULA)

生效日期：2026年6月

请仔细阅读本协议。安装、复制或使用本软件即表示您同意接受本协议的约束。

────────────────────────────────────────

一、版权声明

本软件（AI桌面宠物）及其所有相关内容（包括但不限于代码、设计、
图像、文档）的版权归开发者所有。

────────────────────────────────────────

二、许可范围

1. 您可以免费下载、安装和使用本软件的免费版本。
2. 付费版本授予您个人、非排他、不可转让的使用权。
3. 您可以在一台设备上安装和使用本软件。

────────────────────────────────────────

三、禁止行为

未经开发者明确书面许可，您不得：

1. 倒卖、转售、出租、出借本软件或其任何部分。
2. 对本软件进行反编译、反向工程或逆向分析。
3. 移除、修改或遮盖本软件中的任何版权标识。
4. 将本软件用于任何商业用途（除非获得商业许可）。
5. 分发本软件的修改版本或声称是您自己的作品。
6. 在任何第三方平台上以付费形式重新分发本软件。

────────────────────────────────────────

四、付费版本补充条款

1. 付费版本的序列号仅限购买者本人使用。
2. 序列号不得转让、分享或公开发布。
3. 每个序列号仅可在一台设备上激活。
4. 付费版本享有优先技术支持和更新服务。

────────────────────────────────────────

五、免责声明

1. 本软件按"现状"提供，不作任何明示或暗示的保证。
2. 开发者不对因使用本软件而产生的任何损失承担责任。
3. 开发者保留随时修改本协议的权利。

────────────────────────────────────────

六、违约处理

违反本协议的，开发者有权：
1. 终止您的使用许可。
2. 追究法律责任。
3. 要求赔偿损失。

────────────────────────────────────────

七、联系方式

如有任何问题，请通过以下方式联系：
- 邮箱：[您的邮箱]
- GitHub：[您的GitHub地址]

────────────────────────────────────────

点击"我同意"即表示您已阅读并同意本协议的所有条款。
""".strip()


EULA_FILE = "eula_accepted.txt"


def is_eula_accepted():
    """检查用户是否已接受EULA"""
    import os
    return os.path.exists(EULA_FILE)


def accept_eula():
    """记录用户接受EULA"""
    import time
    with open(EULA_FILE, "w", encoding="utf-8") as f:
        f.write(f"accepted:{time.time()}")


class EulaDialog(QDialog):
    """EULA对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI桌面宠物 — 用户协议")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QTextEdit { background: white; border: 1px solid #ddd; border-radius: 6px;
                        padding: 10px; font-size: 12px; }
            QPushButton { padding: 10px 20px; border-radius: 6px; font-size: 13px; }
            #agreeBtn { background: #78dcff; color: white; font-weight: bold; }
            #agreeBtn:hover { background: #5bc0f0; }
            #agreeBtn:disabled { background: #ccc; }
            #disagreeBtn { background: #eee; color: #666; }
        """)

        layout = QVBoxLayout(self)

        title = QLabel("AI桌面宠物 — 最终用户许可协议")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # EULA文本
        text_edit = QTextEdit()
        text_edit.setPlainText(EULA_TEXT)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        # 同意复选框
        self.agree_check = QCheckBox("我已阅读并同意本协议的所有条款")
        self.agree_check.setStyleSheet("font-size: 13px; margin: 10px;")
        self.agree_check.stateChanged.connect(self._on_check_changed)
        layout.addWidget(self.agree_check)

        # 按钮
        btn_layout = QVBoxLayout()

        self.agree_btn = QPushButton("我同意")
        self.agree_btn.setObjectName("agreeBtn")
        self.agree_btn.setEnabled(False)
        self.agree_btn.clicked.connect(self._accept)
        btn_layout.addWidget(self.agree_btn)

        disagree_btn = QPushButton("不同意（退出程序）")
        disagree_btn.setObjectName("disagreeBtn")
        disagree_btn.clicked.connect(self.reject)
        btn_layout.addWidget(disagree_btn)

        layout.addLayout(btn_layout)

    def _on_check_changed(self, state):
        self.agree_btn.setEnabled(state == Qt.Checked)

    def _accept(self):
        accept_eula()
        self.accept()


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 AI桌面宠物")
        self.setFixedSize(350, 300)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QLabel { font-size: 13px; color: #333; }
        """)

        layout = QVBoxLayout(self)

        title = QLabel("AI桌面宠物")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #78dcff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel("版本 1.0.0")
        version.setStyleSheet("font-size: 14px; color: #888;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(20)

        copyright_label = QLabel("© 2026 AI桌面宠物团队\n保留所有权利")
        copyright_label.setStyleSheet("font-size: 13px; color: #666;")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)

        layout.addSpacing(10)

        desc = QLabel("一个可爱的AI桌面宠物\n支持多种宠物、AI聊天、小游戏")
        desc.setStyleSheet("font-size: 12px; color: #888;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        close_btn = QPushButton("确定")
        close_btn.setStyleSheet("""
            QPushButton { padding: 8px 20px; border-radius: 6px; font-size: 13px;
                          background: #78dcff; color: white; }
            QPushButton:hover { background: #5bc0f0; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
